#!/usr/bin/env python3

import os
import sys
from src.parser import parse_args, parse_map
from src.app import App


def main() -> None:
    args = parse_args()
    try:
        map_data = parse_map(args.map_file)
    except Exception as e:
        sys.exit(str(e))
    app = App(map_data)
    app.init_window()
    app.run()


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print("An error occurred:", e)
        os._exit(1)
