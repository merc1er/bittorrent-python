import json
import sys
from hashlib import sha1
from pprint import pprint

import bencodepy

bc = bencodepy.BencodeDecoder(encoding="utf-8")


def calculate_info_hash(info: dict) -> str:
    bencoded_info = bencodepy.encode(info)
    # pprint(bc.decode(bencoded_info))
    return sha1(bencoded_info).hexdigest()


def read_torrent_file_raw(file_path: str) -> dict:
    with open(file_path, "rb") as f:
        data = f.read()
        decoded_data = bencodepy.decode(data)
    return decoded_data


def main():
    command = sys.argv[1]

    if command == "decode":
        bencoded_value = sys.argv[2].encode()
        decoded_value = bc.decode(bencoded_value)
        print(json.dumps(decoded_value))
    elif command == "info":
        decoded_value = read_torrent_file_raw(sys.argv[2])
        print("Tracker URL:", decoded_value[b"announce"].decode("utf-8"))
        print("Length:", decoded_value[b"info"][b"length"])
        print("Info Hash:", calculate_info_hash(decoded_value[b"info"]))
    else:
        raise NotImplementedError(f"Unknown command {command}")


if __name__ == "__main__":
    main()
