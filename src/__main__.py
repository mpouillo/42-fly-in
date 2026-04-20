#!/usr/bin/env python3

import os
import sys
from src.parser import parse_args, parse_map
from src.view import Game


def main() -> None:
    args = parse_args()
    map_data = parse_map(args.map_file)
    game = Game(map_data)
    game.run()


if __name__ == "__main__":
    main() # Don't forget to try except before pushing
