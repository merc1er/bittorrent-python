import json
import socket
import sys
from hashlib import sha1
from pprint import pprint
from typing import Any

import bencodepy
import requests

bc = bencodepy.BencodeDecoder(encoding="utf-8")

PEER_ID = "-CC0001-123456789012"


def calculate_sha1(data: Any) -> str:
    bencoded_info = bencodepy.encode(data)
    return sha1(bencoded_info).hexdigest()


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


def decode_peers(peers: bytes) -> list[str]:
    decoded_peers = []
    while peers:
        ip = ".".join(str(x) for x in peers[:4])
        port = int.from_bytes(peers[4:6], byteorder="big")
        decoded_peers.append(f"{ip}:{port}")
        peers = peers[6:]

    return decoded_peers


def get_peers(url: str, info_hash: dict, left: int) -> list[str]:
    url_encoded_info_hash = sha1(bencodepy.encode(info_hash)).digest()

    params = {
        "info_hash": url_encoded_info_hash,
        "peer_id": PEER_ID,
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

    decoded_response = bencodepy.decode(response.content)
    return decode_peers(decoded_response[b"peers"])


def connect_to_server(ip: str, port: int, data: bytes) -> bytes:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((ip, port))
        client_socket.sendall(data)
        response = client_socket.recv(1024)
        return response


def perform_handshake(ip: str, port: int, info_hash: bytes) -> None:
    data = (
        b"\x13BitTorrent protocol\x00\x00\x00\x00\x00\x00\x00\x00"
        + info_hash
        + PEER_ID.encode()
    )
    response = connect_to_server(ip, port, data)
    response_peer_id = response[48:].hex()
    print("Peer ID:", response_peer_id)


def main():
    command = sys.argv[1]

    if command == "decode":
        bencoded_value = sys.argv[2].encode()
        decoded_value = bc.decode(bencoded_value)
        print(json.dumps(decoded_value))
    elif command in ["info", "peers", "handshake", "download_piece"]:
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
            pass
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
