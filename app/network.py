"""
Handles connecting to peers and downloading pieces.

Example call:
python app/main.py download_piece -o /tmp/test-piece sample.torrent <piece_index>
"""

import socket

from app.file_parsing import calculate_sha1, get_peers
from app.settings import PEER_ID


def perform_handshake(info_hash: bytes, sock: socket.socket) -> None:
    data = b"\x13BitTorrent protocol" + b"\x00" * 8 + info_hash + PEER_ID.encode()
    sock.sendall(data)
    response = sock.recv(1024)
    response_peer_id = response[48:].hex()
    print("Peer ID:", response_peer_id)


def perform_handshake_standalone(ip: str, port: str, info_hash: str) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, int(port)))
        perform_handshake(bytes.fromhex(info_hash), sock)


def wait_for_bitfield(client_socket: socket.socket) -> None:
    """
    Waits for a bitfield message from the peer.
    The message id for this type is 5.
    The payload is ignored as the tracker ensures all pieces are available.
    """

    while True:
        response = client_socket.recv(1024)
        print("Received response:", response.hex())
        if not response:
            raise ConnectionError(
                "Peer disconnected before sending a bitfield message."
            )

        message_id = response[0]
        if message_id == 5:  # Bitfield message
            print("Received bitfield message from the peer.")
            return
        else:
            print(f"Ignoring message with ID {message_id}.")


def download_piece(
    torrent_file_content: dict, piece_index: int, output_file_path: str
) -> bytes:

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
        wait_for_bitfield(sock)

        # Assume all pieces are available, proceed to download the piece
        print(f"Downloading piece {piece_index}...")
        # Placeholder for actual piece download logic
        with open(output_file_path, "wb") as output_file:
            output_file.write(b"Downloaded data for piece")
        print(f"Piece {piece_index} downloaded to {output_file_path}.")

    return bytes(0)
