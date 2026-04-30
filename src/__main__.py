#!/usr/bin/env python3

# import os
# import sys
from src.parser import parse_args, parse_map
from src.app import App


def main() -> None:
    args = parse_args()
    map_data = parse_map(args.map_file)
    app = App(map_data)
    app.init_window()
    app.run()


if __name__ == "__main__":
    main()  # Don't forget to try except before pushing
