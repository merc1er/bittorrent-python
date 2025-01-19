from hashlib import sha1

import bencodepy
import requests

from app.settings import PEER_ID


def calculate_sha1(data: bytes) -> str:
    bencoded_info = bencodepy.encode(data)
    return sha1(bencoded_info).hexdigest()


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
