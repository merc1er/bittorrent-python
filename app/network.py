"""
Handles connecting to peers and downloading pieces.

Example call:
python app/main.py download_piece -o /tmp/test-piece sample.torrent <piece_index>
"""

import math
import socket
import struct

from app.file_parsing import calculate_sha1, get_peers
from app.settings import PEER_ID


# Entrypoint
def download_piece(torrent_file_content: dict, piece_index: int, output_file_path: str):
    info_hash = calculate_sha1(torrent_file_content[b"info"])
    tracker_url = torrent_file_content[b"announce"].decode("utf-8")
    default_piece_length = torrent_file_content[b"info"][b"piece length"]
    file_length = torrent_file_content[b"info"][b"length"]
    number_of_blocks = math.ceil(default_piece_length / (16 * 1024))
    total_number_of_pieces = math.ceil(file_length / default_piece_length)

    if piece_index >= total_number_of_pieces:
        raise ValueError(
            f"{piece_index=} is too big. Torrent has {total_number_of_pieces} pieces."
        )

    if piece_index == total_number_of_pieces - 1:
        piece_length = calculate_last_piece_length(
            default_piece_length, file_length, total_number_of_pieces
        )
    else:
        piece_length = default_piece_length

    peers = get_peers(
        url=tracker_url,
        info_hash=torrent_file_content[b"info"],
        left=torrent_file_content[b"info"][b"length"],
    )
    ip, port = peers[0].split(":")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, int(port)))
        sock.settimeout(2)
        perform_handshake(bytes.fromhex(info_hash), sock)

        print("Waiting for bitfield message...")
        read_message(sock, 5)

        interested_message = b"\x00\x00\x00\x01\x02"
        sock.sendall(interested_message)

        print("🫸🏻 Waiting for unchoke message...")
        read_message(sock, 1)
        print("📥 Received unchoke message.")

        data = bytearray()
        for block_index in range(number_of_blocks):
            begin = 2**14 * block_index
            print(f"begin: {begin}")
            block_length = min(piece_length - begin, 2**14)
            print(
                f"Requesting block {block_index + 1} of {number_of_blocks} with length {block_length}"
            )

            request_payload = struct.pack(
                ">IBIII", 13, 6, piece_index, begin, block_length
            )
            print("Requesting block, with payload:")
            print(request_payload)

            print(struct.unpack(">IBIII", request_payload))

            print(int.from_bytes(request_payload[:4]))
            print(int.from_bytes(request_payload[4:5]))
            print(int.from_bytes(request_payload[5:9]))
            print(int.from_bytes(request_payload[17:21]))
            sock.sendall(request_payload)

            message = receive_message(sock)

            data.extend(message[13:])

        with open(output_file_path, "wb") as f:
            f.write(data)


def receive_message(s: socket.socket) -> bytes:
    length = s.recv(4)

    while not length or not int.from_bytes(length):
        length = s.recv(4)

    message = s.recv(int.from_bytes(length))

    # If we didn't receive the full message for some reason, keep gobbling.
    while len(message) < int.from_bytes(length):
        message += s.recv(int.from_bytes(length) - len(message))

    return length + message


def calculate_last_piece_length(
    default_piece_length: int, file_length: int, total_number_of_pieces: int
) -> int:
    return file_length - (default_piece_length * (total_number_of_pieces - 1))


def perform_handshake(info_hash: bytes, sock: socket.socket) -> None:
    data = b"\x13BitTorrent protocol" + b"\x00" * 8 + info_hash + PEER_ID.encode()
    sock.sendall(data)
    response = sock.recv(68)
    response_peer_id = response[48:].hex()
    print("Peer ID:", response_peer_id)


def perform_handshake_standalone(ip: str, port: str, info_hash: str) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, int(port)))
        perform_handshake(bytes.fromhex(info_hash), sock)


def receive_full_message(sock: socket.socket, length: int) -> bytes:
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed before full message was received")
        data += chunk
    return data


def read_message(sock: socket.socket, expected_message_id: int) -> bytes:
    """
    Waits for a message with the specified ID from the peer.
    """

    length_bytes = receive_full_message(sock, 4)
    total_length = int.from_bytes(length_bytes, "big")

    if total_length == 0:
        raise ValueError("Received a zero-length message, which is unexpected.")

    message = receive_full_message(sock, total_length)

    message_id = message[0]
    if message_id == expected_message_id:
        print(f"Received message with ID {expected_message_id}.")
        return length_bytes + message
    else:
        raise ValueError(
            f"Expected message with ID {expected_message_id}, but got {message_id}."
        )
