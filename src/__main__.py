#!/usr/bin/env python3

import os
import sys
from src.parser import parse_args, parse_map
from src.view import Game


def main() -> None:
    args = parse_args()

    try:
        map_dict = parse_map(args.map_file)
    except BaseException as e:
        sys.exit(f"Error while parsing map file: {e}")

    from pprint import pprint
    pprint(map_dict)
    game = Game(map_dict)
    game.run()


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print(e)
        os._exit(1)
