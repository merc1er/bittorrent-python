import json
import sys
from hashlib import sha1
from pprint import pprint
from typing import Any

import bencodepy
import requests

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
        print(piece.hex())
        pieces = pieces[20:]


def get_peers(url: str, info_hash: dict, left: int) -> str:
    url_encoded_info_hash = bencodepy.encode(info_hash)

    params = {
        "info_hash": url_encoded_info_hash,
        "peer_id": "superpeer",
        "port": 6881,
        "uploaded": 0,
        "downloaded": 0,
        "left": left,
        "compact": 1,
    }
    try:
        response = requests.get(url, params=params)
    except requests.RequestException as e:
        if isinstance(e, requests.HTTPError):
            print(response.text)
        print(f"Error: {e}")

    decoded_response = bc.decode(response.content)
    return decoded_response


def main():
    command = sys.argv[1]

    if command == "decode":
        bencoded_value = sys.argv[2].encode()
        decoded_value = bc.decode(bencoded_value)
        print(json.dumps(decoded_value))
    elif command == "info":
        decoded_value = read_torrent_file_raw(sys.argv[2])
        info_hash = calculate_sha1(decoded_value[b"info"])
        tracker_url = decoded_value[b"announce"].decode("utf-8")

        print("Tracker URL:", tracker_url)
        print("Length:", decoded_value[b"info"][b"length"])
        print("Info Hash:", info_hash)
        print("Piece Length:", decoded_value[b"info"][b"piece length"])
        print("Piece Hashes:")
        decode_pieces(decoded_value[b"info"][b"pieces"])

        peers = get_peers(
            url=tracker_url,
            info_hash=decoded_value[b"info"],
            left=decoded_value[b"info"][b"length"],
        )
        print(f"Peers: {peers}")
    else:
        raise NotImplementedError(f"Unknown command {command}")


if __name__ == "__main__":
    main()
