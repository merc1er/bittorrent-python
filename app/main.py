import json
import sys

import bencodepy

# import requests - available if you need it!


def bytes_to_str(data):
    # json.dumps() can't handle bytes, but bencoded "strings" need to be
    # bytestrings since they might contain non utf-8 characters.

    if isinstance(data, bytes):
        return data.decode()

    raise TypeError(f"Type not serializable: {type(data)}")


def main():
    command = sys.argv[1]

    if command == "decode":
        bencoded_value = sys.argv[2].encode()
        decoded_value = bencodepy.decode(bencoded_value)
        if len(decoded_value) == 1:
            decoded_value = decoded_value[0]
        print(json.dumps(decoded_value, default=bytes_to_str))
    else:
        raise NotImplementedError(f"Unknown command {command}")


if __name__ == "__main__":
    main()
