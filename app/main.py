import json
import sys

import bencodepy
from file_parsing import calculate_sha1, get_peers
from network import download_piece, perform_handshake

bc = bencodepy.BencodeDecoder(encoding="utf-8")


def read_torrent_file_raw(file_path: str) -> dict:
    with open(file_path, "rb") as f:
        data = f.read()
        decoded_data = bencodepy.decode(data)
    return decoded_data


def decode_pieces(pieces: bytes) -> None:
    while pieces:
        piece = pieces[:20]
        print(piece.hex())
        pieces = pieces[20:]


def main():
    command = sys.argv[1]

    if command == "decode":
        bencoded_value = sys.argv[2].encode()
        decoded_value = bc.decode(bencoded_value)
        print(json.dumps(decoded_value))
    elif command in ["info", "peers", "handshake"]:
        decoded_value = read_torrent_file_raw(sys.argv[2])
        info_hash = calculate_sha1(decoded_value[b"info"])
        tracker_url = decoded_value[b"announce"].decode("utf-8")

        if command == "info":
            print_info(decoded_value, info_hash, tracker_url)
        elif command == "peers":
            peers = get_peers(
                url=tracker_url,
                info_hash=decoded_value[b"info"],
                left=decoded_value[b"info"][b"length"],
            )
            for peer in peers:
                print(peer)
        elif command == "handshake":
            ip, port = sys.argv[3].split(":")
            # print(f"Connecting to {ip}:{port}")
            perform_handshake(ip, int(port), bytes.fromhex(info_hash))
    elif command == "download_piece":
        output_file_path = sys.argv[3]
        torrent_file_content = read_torrent_file_raw(sys.argv[4])
        piece_index = int(sys.argv[5])
        download_piece(torrent_file_content, piece_index, output_file_path)
    else:
        raise NotImplementedError(f"Unknown command {command}")


def print_info(decoded_value: dict, info_hash: str, tracker_url: str) -> None:
    print("Tracker URL:", tracker_url)
    print("Length:", decoded_value[b"info"][b"length"])
    print("Info Hash:", info_hash)
    print("Piece Length:", decoded_value[b"info"][b"piece length"])
    print("Piece Hashes:")
    decode_pieces(decoded_value[b"info"][b"pieces"])


if __name__ == "__main__":
    main()
