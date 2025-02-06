from hashlib import sha1

import bencodepy  # type: ignore


def calculate_sha1(data: bytes) -> str:
    bencoded_info = bencodepy.encode(data)
    return sha1(bencoded_info).hexdigest()
