import json
import sys

import bencodepy

bc = bencodepy.BencodeDecoder(encoding="utf-8")


def read_torrent_file(file_path: str) -> dict | list | str | int:
    def convert_bytes_to_str(obj: bytes):
        # Recursively convert all byte strings to normal strings
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                result[convert_bytes_to_str(key)] = convert_bytes_to_str(value)
            return result
        elif isinstance(obj, list):
            result = []
            for item in obj:
                result.append(convert_bytes_to_str(item))
            return result
        elif isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")  # Decode bytes to string
        elif isinstance(obj, int):
            return obj
        raise ValueError(f"Unexpected type {type(obj)}")

    with open(file_path, "rb") as f:
        data = f.read()
        decoded_data = bencodepy.decode(data)
        stringified_data = convert_bytes_to_str(decoded_data)

    print(stringified_data)
    return stringified_data


def main():
    command = sys.argv[1]

    if command == "decode":
        bencoded_value = sys.argv[2].encode()
        decoded_value = bc.decode(bencoded_value)
        print(json.dumps(decoded_value))
    elif command == "info":
        decoded_value = read_torrent_file(sys.argv[2])
        print("Tracker URL:", decoded_value["announce"])
        print("Length:", decoded_value["info"]["length"])
    else:
        raise NotImplementedError(f"Unknown command {command}")


if __name__ == "__main__":
    main()
