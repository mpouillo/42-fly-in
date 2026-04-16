#!/usr/bin/env python3

import os
import sys
from src.parser import parse_args, parse_map
from src.view import run_gui


def main() -> None:
    args = parse_args()

    try:
        map_dict = parse_map(args.map_file)
    except BaseException as e:
        sys.exit(f"Error while parsing map file: {e}")

    from pprint import pprint
    pprint(map_dict)

    run_gui(map_dict)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print(e)
        os._exit(1)
