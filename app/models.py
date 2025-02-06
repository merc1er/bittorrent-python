from dataclasses import dataclass
from hashlib import sha1

import bencodepy  # type: ignore
import requests

from app.settings import PEER_ID


@dataclass
class Peer:
    ip: str
    port: int

    def __str__(self) -> str:
        return f"{self.ip}:{self.port}"

    @classmethod
    def from_bytes(cls, peers: bytes) -> list["Peer"]:
        decoded_peers = []
        while peers:
            ip = ".".join(str(x) for x in peers[:4])
            port = int.from_bytes(peers[4:6], byteorder="big")
            decoded_peers.append(cls(ip=ip, port=port))
            peers = peers[6:]

        return decoded_peers


@dataclass
class Torrent:
    tracker_url: str
    info: dict
    info_hash: str
    length: int
    piece_length: int
    pieces: list[bytes]
    decoded_value: dict
    peers: list[Peer] = None

    @classmethod
    def from_file(cls, file_path: str) -> "Torrent":
        with open(file_path, "rb") as file:
            torrent_data = bencodepy.decode(file.read())

        tracker_url = torrent_data.get(b"announce", b"").decode("utf-8")
        info: dict = torrent_data.get(b"info", {})
        piece_length = info.get(b"piece length", 0)
        pieces = []
        pieces_data = info[b"pieces"]
        for i in range(0, len(pieces_data), 20):
            pieces.append(pieces_data[i : i + 20].hex())
        length = info[b"length"]

        return cls(
            tracker_url=tracker_url,
            info=info,
            info_hash=cls.calculate_sha1(info),
            length=length,
            piece_length=piece_length,
            pieces=pieces,
            decoded_value=torrent_data,
        )

    @staticmethod
    def calculate_sha1(data: dict) -> str:
        bencoded_info = bencodepy.encode(data)
        return sha1(bencoded_info).hexdigest()

    def print_info(self) -> None:
        print("Tracker URL:", self.tracker_url)
        print("Length:", self.length)
        print("Info Hash:", self.info_hash)
        print("Piece Length:", self.piece_length)
        print("Piece Hashes:")
        for piece in self.pieces:
            print(piece)

    def get_peers(self) -> list[Peer]:
        url_encoded_info_hash = sha1(bencodepy.encode(self.info)).digest()
        params = {
            "info_hash": url_encoded_info_hash,
            "peer_id": PEER_ID,
            "port": 6881,
            "uploaded": 0,
            "downloaded": 0,
            "left": self.length,
            "compact": 1,
        }
        try:
            response = requests.get(self.tracker_url, params=params)
        except requests.RequestException as e:
            if isinstance(e, requests.HTTPError):
                print(response.text)
            print(f"Error: {e}")

        decoded_response = bencodepy.decode(response.content)
        self.peers = Peer.from_bytes(decoded_response[b"peers"])
        return self.peers
