from dataclasses import dataclass
from hashlib import sha1

import bencodepy


@dataclass
class Torrent:
    tracker_url: str
    info: dict
    info_hash: str
    length: int
    piece_length: int
    pieces: list[bytes]
    decoded_value: dict

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
