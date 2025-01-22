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
    total_number_of_pieces = math.ceil(file_length / default_piece_length)
    number_of_blocks = math.ceil(default_piece_length / (16 * 1024))

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
        perform_handshake(bytes.fromhex(info_hash), sock)

        print("Waiting for bitfield message...")
        read_message(sock, 5)

        interested_message = b"\x00\x00\x00\x01\x02"
        sock.sendall(interested_message)

        print("🫸🏻 Waiting for unchoke message...")
        read_message(sock, 1)
        print("📥 Received unchoke message.")

        piece_data = b""
        for block in range(number_of_blocks):
            msg_id = 6
            begin = 16 * 1024 * block
            block_length = min(piece_length - begin, 16 * 1024)

            print(
                f"Requesting block {block + 1} of {number_of_blocks} with length {block_length}"
            )

            msg = struct.pack(">IBIII", 13, msg_id, piece_index, begin, block_length)
            sock.sendall(msg)

            print("🫸🏻 Waiting for piece message...")
            message = read_message(sock, 7)
            piece_data += message[8:]
            print(f"📥 Received piece message. Length: {len(message) * 8}")

        with open(output_file_path, "wb") as f:
            f.write(piece_data)


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


def read_message(sock: socket.socket, expected_message_id: int) -> bytes:
    """
    Waits for a message with the specified ID from the peer.
    """

    length = sock.recv(4)
    while not length or not int.from_bytes(length):
        length = sock.recv(4)

    message = sock.recv(int.from_bytes(length))

    # In case the message is split into multiple packets.
    while len(message) < int.from_bytes(length):
        message += sock.recv(int.from_bytes(length) - len(message))

    full_message_hex = length.hex() + message.hex()
    message_id = message[0]
    payload = message[1:]
    if message_id == expected_message_id:
        print(f"Received message with ID {expected_message_id}.")
        # print(full_message_hex)
        return payload
    else:
        raise ValueError(
            f"Expected message with ID {expected_message_id}, but got {message_id}."
        )
