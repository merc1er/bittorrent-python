"""
Handles connecting to peers and downloading pieces.

Example call:
python app/main.py download_piece -o /tmp/test-piece sample.torrent <piece_index>
"""

import socket

from app.file_parsing import calculate_sha1, get_peers
from app.settings import PEER_ID


# Entrypoint
def download_piece(torrent_file_content: dict, piece_index: int, output_file_path: str):

    info_hash = calculate_sha1(torrent_file_content[b"info"])
    tracker_url = torrent_file_content[b"announce"].decode("utf-8")

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
        wait_for_message(sock, 5)

        interested_message = b"\x00\x00\x00\x01\x02"
        sock.sendall(interested_message)

        print("🫸🏻 Waiting for unchoke message...")
        wait_for_message(sock, 1)
        print("📥 Received unchoke message.")

        length = 16 * 1024
        request_message = (
            b"\x00\x00\x00\x0d\x06\x00\x00\x00\x00\x00\x00\x00\x00"
            + length.to_bytes(4, byteorder="big")
        )
        sock.sendall(request_message)

        print("🫸🏻 Waiting for piece message...")
        piece_data = wait_for_message(sock, 7)
        print(f"📥 Received piece message. Length: {len(piece_data)}")


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


def wait_for_message(sock: socket.socket, expected_message_id: int) -> bytes:
    """
    Waits for a message with the specified ID from the peer.
    """

    length = sock.recv(4)
    message = sock.recv(int.from_bytes(length))

    message_id, payload = read_message(message)
    if message_id == expected_message_id:
        print(f"Received message with ID {expected_message_id}.")
        return payload
    else:
        print(f"Ignoring message with ID {message_id}.")
        return wait_for_message(sock, expected_message_id)


def read_message(message: bytes) -> tuple[int, bytes]:
    """
    Reads the message and returns the message ID and payload.
    """

    message_id = message[0]
    payload = message[1:]
    return message_id, payload
