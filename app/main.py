import json
import sys

import bencodepy

from app.file_parsing import get_peers
from app.network import download_piece, perform_handshake_standalone
from app.torrent import Torrent

bc = bencodepy.BencodeDecoder(encoding="utf-8")


def read_torrent_file_raw(file_path: str) -> dict:
    with open(file_path, "rb") as f:
        data = f.read()
        decoded_data = bencodepy.decode(data)
    return decoded_data


def main():
    command = sys.argv[1]

    if command == "decode":
        bencoded_value = sys.argv[2].encode()
        decoded_value = bc.decode(bencoded_value)
        print(json.dumps(decoded_value))
    elif command in ["info", "peers", "handshake"]:
        torrent = Torrent.from_file(sys.argv[2])

        if command == "info":
            torrent.print_info()
        elif command == "peers":
            peers = get_peers(
                url=torrent.tracker_url,
                info_hash=torrent.info_hash,
                left=torrent.length,
            )
            for peer in peers:
                print(peer)
        elif command == "handshake":
            ip, port = sys.argv[3].split(":")
            # print(f"Connecting to {ip}:{port}")
            perform_handshake_standalone(ip, port, torrent.info_hash)
    elif command == "download_piece":
        output_file_path = sys.argv[3]
        torrent_file_content = read_torrent_file_raw(sys.argv[4])
        piece_index = int(sys.argv[5])
        download_piece(torrent_file_content, piece_index, output_file_path)
    else:
        raise NotImplementedError(f"Unknown command {command}")


if __name__ == "__main__":
    main()
