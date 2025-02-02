from hashlib import sha1

import bencodepy
import requests

from app.models import Peer
from app.settings import PEER_ID


def calculate_sha1(data: bytes) -> str:
    bencoded_info = bencodepy.encode(data)
    return sha1(bencoded_info).hexdigest()


def get_peers(url: str, info: dict, left: int) -> list[Peer]:
    url_encoded_info_hash = sha1(bencodepy.encode(info)).digest()

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
    return Peer.from_bytes(decoded_response[b"peers"])
