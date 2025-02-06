import asyncio
import itertools
import json
import os
import sys

import bencodepy  # type: ignore

from app.models import Torrent
from app.network import download_piece, perform_handshake_standalone

bc = bencodepy.BencodeDecoder(encoding="utf-8")


async def main():
    command = sys.argv[1]

    match command:
        case "decode":
            bencoded_value = sys.argv[2].encode()
            decoded_value = bc.decode(bencoded_value)
            print(json.dumps(decoded_value))

        case "info":
            torrent = Torrent.from_file(sys.argv[2])
            torrent.print_info()

        case "peers":
            torrent = Torrent.from_file(sys.argv[2])
            peers = torrent.get_peers()
            for peer in peers:
                print(peer)

        case "handshake":
            torrent = Torrent.from_file(sys.argv[2])
            ip, port = sys.argv[3].split(":")
            await perform_handshake_standalone(ip, port, torrent.info_hash)

        case "download_piece":
            output_file_path = sys.argv[3]
            torrent = Torrent.from_file(sys.argv[4])
            print(f"Total number of pieces: {len(torrent.pieces)}")
            piece_index = int(sys.argv[5])
            await download_piece(torrent, piece_index, output_file_path)
            os.remove(f"{output_file_path}.part{piece_index}")

        case "download":
            output_file_path = sys.argv[3]
            torrent = Torrent.from_file(sys.argv[4])
            torrent.get_peers()

            print(f"Total number of pieces: {len(torrent.pieces)}")
            print(f"Found {len(torrent.peers)} peers.")

            peers_cycle = itertools.cycle(torrent.peers)
            tasks = []

            for piece_index in range(len(torrent.pieces)):
                peer = next(peers_cycle)
                tasks.append(
                    asyncio.create_task(
                        download_piece(torrent, piece_index, output_file_path, peer)
                    )
                )

                # Limit the number of concurrent tasks based on the number of peers.
                if len(tasks) >= len(torrent.peers):
                    done, pending = await asyncio.wait(
                        tasks, return_when=asyncio.FIRST_COMPLETED
                    )
                    tasks = list(pending)  # Reassign pending tasks to tasks.

            # Wait for any remaining tasks to complete.
            await asyncio.gather(*tasks)

            with open(output_file_path, "wb") as final_file:
                for piece_index in range(len(torrent.pieces)):
                    piece_file_name = f"{output_file_path}.part{piece_index}"
                    with open(piece_file_name, "rb") as piece_file:
                        final_file.write(piece_file.read())
                    os.remove(piece_file_name)

        case _:
            raise NotImplementedError(f"Unknown command {command}")


if __name__ == "__main__":
    asyncio.run(main())
