#!/usr/bin/env python3

# import os
# import sys
from src.parser import parse_args, parse_map
from src.app import App


def main() -> None:
    args = parse_args()
    map_data = parse_map(args.map_file)
    from pprint import pprint
    pprint(map_data)
    app = App(map_data)
    pprint(app.graph.weight_graph)
    pprint(app.graph.drone_map)
    app.init_window()
    app.run()


if __name__ == "__main__":
    main()  # Don't forget to try except before pushing
