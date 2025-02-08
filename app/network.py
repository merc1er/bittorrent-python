"""
Handles connecting to peers and downloading pieces.

Example call:
python app/main.py download_piece -o /tmp/test-piece sample.torrent <piece_index>
"""

import asyncio
import math
import socket
import struct

from app.models import Peer, Torrent
from app.settings import PEER_ID


# Entrypoint
async def download_piece(
    torrent: Torrent, piece_index: int, output_file_path: str, peer: Peer | None = None
) -> None:
    info_hash = torrent.info_hash
    file_length = torrent.length
    total_number_of_pieces = len(torrent.pieces)

    if piece_index >= total_number_of_pieces:
        raise ValueError(
            f"{piece_index=} is too big. Torrent has {total_number_of_pieces} pieces."
        )

    default_piece_length = torrent.piece_length
    if piece_index == total_number_of_pieces - 1:
        piece_length = file_length - (default_piece_length * piece_index)
    else:
        piece_length = default_piece_length

    number_of_blocks = math.ceil(piece_length / (16 * 1024))

    if not peer:
        peers = torrent.get_peers()
        peer = peers[0]

    reader, writer = await asyncio.open_connection(peer.ip, int(peer.port))
    await perform_handshake(bytes.fromhex(info_hash), writer=writer, reader=reader)

    print("Waiting for bitfield message...")
    await read_message(5, writer=writer, reader=reader)

    # Interested message.
    interested_message = b"\x00\x00\x00\x01\x02"
    writer.write(interested_message)
    await writer.drain()

    print("🫸🏻 Waiting for unchoke message...")
    await read_message(1, writer=writer, reader=reader)
    print("📥 Received unchoke message.")

    data = await download_blocks(
        piece_index, piece_length, number_of_blocks, reader, writer
    )

    piece_file_name = f"{output_file_path}.part{piece_index}"
    with open(piece_file_name, "wb") as f:
        f.write(data)


async def download_blocks(
    piece_index: int,
    piece_length: int,
    number_of_blocks: int,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> bytes:
    data = bytearray()
    semaphore = asyncio.Semaphore(5)
    response_queue: asyncio.Queue[tuple[int, bytes]] = asyncio.Queue()

    async def send_requests():
        """Sends block requests concurrently but limits outgoing requests."""
        for block_index in range(number_of_blocks):
            async with semaphore:
                begin = 2**14 * block_index
                block_length = min(piece_length - begin, 2**14)
                print(
                    f"Requesting block {block_index + 1} of {number_of_blocks} with "
                    f" length {block_length}"
                )

                request_payload = struct.pack(
                    ">IBIII", 13, 6, piece_index, begin, block_length
                )
                writer.write(request_payload)
                await writer.drain()

    async def receive_responses():
        """Reads incoming messages and stores them in the queue."""
        for _ in range(number_of_blocks):
            message = await read_message(7, writer=writer, reader=reader)
            block_index = (
                struct.unpack(">I", message[9:13])[0] // 2**14
            )  # Extract block index
            await response_queue.put((block_index, message[13:]))

    # Start sending and receiving concurrently
    await asyncio.gather(send_requests(), receive_responses())

    # Process blocks in order
    results = [await response_queue.get() for _ in range(number_of_blocks)]
    for _, block_data in sorted(results):
        data.extend(block_data)

    return data


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


async def perform_handshake(
    info_hash: bytes,
    writer: asyncio.StreamWriter,
    reader: asyncio.StreamReader,
    signal_extensions: bool = False,
) -> None:
    reserved = bytearray(8)
    if signal_extensions:
        reserved[5] |= 0x10

    data = b"\x13BitTorrent protocol" + reserved + info_hash + PEER_ID.encode()
    writer.write(data)
    await writer.drain()

    response = await reader.readexactly(68)
    response_peer_id = response[48:].hex()
    print("Peer ID:", response_peer_id)


async def perform_handshake_standalone(
    peer: Peer, info_hash: str, signal_extension: bool = False
) -> None:
    reader, writer = await asyncio.open_connection(peer.ip, int(peer.port))
    await perform_handshake(bytes.fromhex(info_hash), writer, reader, signal_extension)
    writer.close()
    await writer.wait_closed()


async def receive_full_message(
    length: int, writer: asyncio.StreamWriter, reader: asyncio.StreamReader
) -> bytes:
    data = b""
    while len(data) < length:
        chunk = await reader.read(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed before full message was received")
        data += chunk
    return data


async def read_message(
    expected_message_id: int, writer: asyncio.StreamWriter, reader: asyncio.StreamReader
) -> bytes:
    """
    Waits for a message with the specified ID from the peer.
    """

    length_bytes = await receive_full_message(4, writer, reader)
    total_length = int.from_bytes(length_bytes, "big")

    if total_length == 0:
        raise ValueError("Received a zero-length message, which is unexpected.")

    message = await receive_full_message(total_length, writer, reader)

    message_id = message[0]
    if message_id == expected_message_id:
        print(f"Received message with ID {expected_message_id}.")
        return length_bytes + message
    else:
        raise ValueError(
            f"Expected message with ID {expected_message_id}, but got {message_id}."
        )
