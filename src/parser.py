import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List
from src.constants import ALLOWED_COLORS, ALLOWED_ZONES


class ParsingError(Exception):
    """Custom error class for parsing errors."""
    def __init__(self, message: str, line: int) -> None:
        """Initialize parent Exception class with a custom message."""
        super().__init__(f"{message} (line {line})")


def parse_args() -> argparse.Namespace:
    """Parse and return command line arguments."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "map_file",
        help="Path to input map file",
    )

    return parser.parse_args()


def parse_map(filepath: str) -> Dict[str, Any]:
    """Parse file pointed to by filename for map data"""
    file: Path = Path(filepath)
    if not bool(file.is_file):
        raise ValueError("'map' argument is not a file")
    if not file.suffix == ".txt":
        raise ValueError("map file extension should be '.txt'")

    with file.open("r") as f:
        file_data: List[str] = [line.strip("\n") for line in f.readlines()]

    map_data: Dict[str, Any] = {
        "nb_drones": 0,
        "hubs": defaultdict(dict),
        "connections": defaultdict(dict)
    }

    flag_nb_drones: bool = False
    flag_start: bool = False
    flag_end: bool = False

    for i, line in enumerate(file_data, 1):
        # Skip comments or empty lines
        if line.startswith("#") or not line.strip():
            continue

        if ':' not in line:
            raise ParsingError("missing ':' separator", i)

        # The first line must define the number of drones
        if not flag_nb_drones:
            key, value = (v.strip() for v in line.split(':', 1))
            if key != "nb_drones":
                raise ParsingError(
                    "first line must be 'nb_drones: <number>'", i
                )
            if not value:
                raise ParsingError(
                    "missing 'nb_drones' value ('nb_drones': <number>')", i
                )
            if not value.isdecimal():
                raise ParsingError(
                    "invalid 'nb_drones' value "
                    "(must be a valid positive integer)", i
                )
            map_data["nb_drones"] = int(value)
            flag_nb_drones = True
            continue

        key, value = (v.strip() for v in line.split(':', 1))
        match key:
            case "start_hub":
                if flag_start:
                    raise ParsingError(
                        "only one 'start_hub' line is allowed", i
                    )
                parse_hub(map_data, key, value, i)
                flag_start = True
            case "end_hub":
                if flag_end:
                    raise ParsingError("only one 'end_hub' line is allowed", i)
                parse_hub(map_data, key, value, i)
                flag_end = True
            case "hub":
                parse_hub(map_data, key, value, i)
            case "connection":
                continue
            case _:
                raise ParsingError(f"invalid value in map file: '{key}'", i)

    if not flag_start:
        raise ParsingError("missing 'start_hub' value", i)
    if not flag_end:
        raise ParsingError("missing 'end_hub' value", i)

    flag_nb_drones = False

    # Parse connections after everything else
    # to detect missing hubs and avoid false positives
    for i, line in enumerate(file_data, 1):
        # Skip comments or empty lines
        if line.startswith("#") or not line.strip():
            continue

        if ':' not in line:
            raise ParsingError(f"missing ':' separator at line {i + 1}", i)

        # Skip nb_drones lines (checked during first loop)
        if not flag_nb_drones:
            flag_nb_drones = True
            continue

        key, value = (v.strip() for v in line.split(':', 1))
        match key:
            case "start_hub":
                continue
            case "end_hub":
                continue
            case "hub":
                continue
            case "connection":
                parse_connection(map_data, value, i)
            case _:
                raise ParsingError(f"invalid value in map file: '{key}'", i)

    return (map_data)


def parse_hub(map_dict: Dict[str, Any], key: str, value: str, i: int) -> None:
    """
    Parse hub values and store them in map_dict.
    Raise ParsingError if any value is invalid.
    """
    values = [v.strip() for v in value.split(' ', 3)]
    if len(values) < 3:
        raise ParsingError("missing arguments for hub value", i)
    elif len(values) == 3:
        name, x, y = values
        metadata = None
    elif len(values) == 4:
        name, x, y, metadata = values

    if not name:
        raise ParsingError("hub cannot be None", i)

    if name in map_dict["hubs"]:
        raise ParsingError(
            f"hub names must be unique (duplicate '{name}' hub)", i
        )

    if "-" in name or " " in name:
        raise ParsingError("hub name cannot contain dashes or spaces", i)

    map_dict["hubs"][name] = {
        "x": 0,
        "y": 0,
        "hub_type": key,
        "zone": "normal",
        "color": "blue",
        "max_drones": 1
    }

    try:
        int(x)
    except ParsingError:
        raise ParsingError(
            f"x value for '{name}' must be a valid integer", i
        )
    map_dict["hubs"][name]["x"] = int(x)

    try:
        int(y)
    except ParsingError:
        raise ParsingError(
            f"y value for '{name}' must be a valid integer", i
        )
    map_dict["hubs"][name]["y"] = int(y)

    # Metadata is optional and enclosed in brackets
    if not metadata:
        return

    if not (metadata.startswith('[') and metadata.endswith(']')):
        raise ParsingError("metadata must be enclosed in brackets", i)

    md_values = [v.strip() for v in metadata[1:-1].split()]
    flag_zone = 0
    flag_color = 0
    flag_max_drones = 0
    for v in md_values:
        try:
            key, val = v.split('=', 1)
        except BaseException:
            raise ParsingError("missing '=' for metadata value", i)
        match key:
            case "zone":
                if flag_zone:
                    raise ParsingError(
                        f"duplicate 'zone' metadata for '{name}'", i
                    )
                if val not in ALLOWED_ZONES:
                    raise ParsingError(
                        f"invalid 'zone' metadata for '{name}'", i
                    )
                map_dict["hubs"][name]["zone"] = val
            case "color":
                if flag_color:
                    raise ParsingError(
                        f"duplicate 'color' metadata for '{name}'", i
                    )
                if not val.isalpha() or val not in ALLOWED_COLORS:
                    raise ParsingError(
                        f"invalid 'color' metadata for '{name}'", i
                    )
                map_dict["hubs"][name]["color"] = val
            case "max_drones":
                if flag_max_drones:
                    raise ParsingError(
                        f"duplicate 'max_drones' metadata for '{name}'", i
                    )
                if not val.isdecimal():
                    raise ParsingError(
                        f"invalid 'max_drones' metadata for '{name}' "
                        "(must be a valid positive integer)", i
                        )
                map_dict["hubs"][name]["max_drones"] = int(val)
            case _:
                raise ParsingError(f"invalid metadata for '{name}'", i)


def parse_connection(map_dict: Dict[str, Any], value: str, i: int) -> None:
    """
    Parse connection values and store them in map_dict.
    Raise ParsingError if any value is invalid.
    """
    values = [v.strip() for v in value.split(' ', 1)]
    if len(values) == 0:
        raise ParsingError("connection value cannot be empty", i)
    elif len(values) == 1:
        connection = values[0]
        metadata = None
    else:
        connection, metadata = values

    # Validate hub names
    try:
        name1, name2 = connection.split('-', 1)
    except BaseException:
        raise ParsingError("missing hub name in connection", i)
    if name1 not in map_dict["hubs"].keys():
        raise ParsingError(f"connection to undefined hub '{name1}'", i)
    if name2 not in map_dict["hubs"].keys():
        raise ParsingError(f"connection to undefined hub '{name2}'", i)

    # Append connections with default value of 1
    map_dict["connections"][name1][name2] = 1
    map_dict["connections"][name2][name1] = 1

    # Stop here if no metadata
    if not metadata:
        return

    # Validate metadata
    if not (metadata.startswith('[') and metadata.endswith(']')):
        raise ParsingError("metadata must be enclosed in brackets", i)

    md_values = [v.strip() for v in metadata[1:-1].split()]
    flag_capacity = False
    for v in md_values:
        try:
            key, val = v.split('=', 1)
        except BaseException:
            raise ParsingError("missing '=' for metadata value", i)
        match key:
            case "max_link_capacity":
                if flag_capacity:
                    raise ParsingError(
                        "duplicate 'max_link_capacity' connection metadata", i
                    )
                if not val.isdecimal():
                    raise ParsingError(
                        "'max_link_capacity' value must be "
                        "a valid positive integer", i
                    )
                map_dict["connections"][name1][name2] = int(val)
                map_dict["connections"][name2][name1] = int(val)
            case _:
                raise ParsingError(f"invalid connection metadata '{key}'", i)
