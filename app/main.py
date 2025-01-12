import json
import sys
from hashlib import sha1
from pprint import pprint
from typing import Any

import bencodepy

bc = bencodepy.BencodeDecoder(encoding="utf-8")


def calculate_sha1(data: Any) -> str:
    bencoded_info = bencodepy.encode(data)
    # pprint(bc.decode(bencoded_info))
    return sha1(bencoded_info).hexdigest()


def read_torrent_file_raw(file_path: str) -> dict:
    with open(file_path, "rb") as f:
        data = f.read()
        decoded_data = bencodepy.decode(data)
    return decoded_data


def decode_pieces(pieces: bytes):
    while pieces:
        piece = pieces[:20]
        print(calculate_sha1(piece))
        pieces = pieces[20:]


def main():
    command = sys.argv[1]

    if command == "decode":
        bencoded_value = sys.argv[2].encode()
        decoded_value = bc.decode(bencoded_value)
        print(json.dumps(decoded_value))
    elif command == "info":
        decoded_value = read_torrent_file_raw(sys.argv[2])
        print("Tracker URL:", decoded_value[b"announce"].decode("utf-8"))
        print("Length:", decoded_value[b"info"][b"length"])
        print("Info Hash:", calculate_sha1(decoded_value[b"info"]))
        print("Piece Length:", decoded_value[b"info"][b"piece length"])
        print("Piece Hashes:")
        decode_pieces(decoded_value[b"info"][b"pieces"])
    else:
        raise NotImplementedError(f"Unknown command {command}")


if __name__ == "__main__":
    main()
