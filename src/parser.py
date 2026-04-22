import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict
from src.constants import ALLOWED_COLORS, ALLOWED_ZONES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "map_file",
        help="Path to input map file",
    )

    return parser.parse_args()


def parse_map(filepath) -> Dict[str, Any]:
    file = Path(filepath)
    if not file.is_file:
        raise ValueError("'map' argument is not a file")
    if not file.suffix == ".txt":
        raise ValueError("map file extension should be '.txt'")

    with file.open("r") as f:
        file_data = [line.strip("\n") for line in f.readlines()]

    map_data: Dict[str, Any] = {
        "nb_drones": 0,
        "hubs": defaultdict(dict),
        "connections": defaultdict(dict)
    }

    flag_nb_drones: bool = False
    flag_start: bool = False
    flag_end: bool = False

    for i, line in enumerate(file_data):
        # Skip comments or empty lines
        if line.startswith("#") or not line.strip():
            continue

        if ':' not in line:
            raise ValueError(f"missing ':' separator at line {i + 1}")

        # The first line must define the number of drones
        if not flag_nb_drones:
            key, value = (v.strip() for v in line.split(':', 1))
            if key != "nb_drones":
                raise ValueError("first line must be 'nb_drones: <number>'")
            if not value:
                raise ValueError(
                    "missing 'nb_drones' value ('nb_drones': <number>')"
                )
            if not value.isdecimal():
                raise ValueError(
                    "invalid 'nb_drones' value "
                    "(must be a valid positive integer)"
                )
            map_data["nb_drones"] = int(value)
            flag_nb_drones = True
            continue

        key, value = (v.strip() for v in line.split(':', 1))
        match key:
            case "start_hub":
                if flag_start:
                    raise ValueError("only one 'start_hub' line is allowed")
                parse_hub(map_data, key, value)
                flag_start = True
            case "end_hub":
                if flag_end:
                    raise ValueError("only one 'end_hub' line is allowed")
                parse_hub(map_data, key, value)
                flag_end = True
            case "hub":
                parse_hub(map_data, key, value)
            case "connection":
                continue
            case _:
                raise ValueError(f"invalid value in map file: '{key}'")

    if not flag_start:
        raise ValueError("missing 'start_hub' value")
    if not flag_end:
        raise ValueError("missing 'end_hub' value")

    flag_nb_drones = False

    # Parse connections after everything else
    # to detect missing hubs and avoid false positives
    for i, line in enumerate(file_data):
        # Skip comments or empty lines
        if line.startswith("#") or not line.strip():
            continue

        if ':' not in line:
            raise ValueError(f"missing ':' separator at line {i + 1}")

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
                parse_connection(map_data, value)
            case _:
                raise ValueError(f"invalid value in map file: '{key}'")

    return (map_data)


def parse_hub(map_dict: Dict[str, Any], key: str, value: str) -> None:
    """
    Parse hub values and store them in map_dict.
    Raise ValueError if any value is invalid.
    """

    values = [v.strip() for v in value.split(' ', 3)]
    if len(values) < 3:
        raise ValueError("missing arguments for hub value")
    elif len(values) == 3:
        name, x, y = values
        metadata = None
    elif len(values) == 4:
        name, x, y, metadata = values

    if not name:
        raise ValueError("hub cannot be None")

    if name in map_dict["hubs"]:
        raise ValueError(f"hub names must be unique (duplicate '{name}' hub)")

    if "-" in name or " " in name:
        raise ValueError("hub name cannot contain dashes or spaces")

    map_dict["hubs"].update({name: {"x": 0, "y": 0, "type": key}})

    try:
        int(x)
    except ValueError:
        raise ValueError(
            f"x value for '{name}' must be a valid integer"
        )
    map_dict["hubs"][name]["x"] = int(x)

    try:
        int(y)
    except ValueError:
        raise ValueError(
            f"y value for '{name}' must be a valid integer"
        )
    map_dict["hubs"][name]["y"] = int(y)

    if key in ["start_hub", "end_hub"]:
        max_drones = float('inf')
    else:
        max_drones = 1

    # Metadata is optional and enclosed in brackets
    map_dict["hubs"][name].update(
        {"metadata":
            {"zone": "normal",
             "color": "blue",
             "max_drones": max_drones}
         }
    )
    if not metadata:
        return

    if not (metadata.startswith('[') and metadata.endswith(']')):
        raise ValueError("metadata must be enclosed in brackets")

    md_values = [v.strip() for v in metadata[1:-1].split()]
    flag_zone = 0
    flag_color = 0
    flag_max_drones = 0
    for v in md_values:
        try:
            key, val = v.split('=', 1)
        except BaseException:
            raise ValueError("missing '=' for metadata value")
        match key:
            case "zone":
                if flag_zone:
                    raise ValueError(
                        f"duplicate 'zone' metadata for '{name}'"
                    )
                if val not in ALLOWED_ZONES:
                    raise ValueError(f"invalid 'zone' metadata for '{name}'")
                map_dict["hubs"][name]["metadata"]["zone"] = val
            case "color":
                if flag_color:
                    raise ValueError(
                        f"duplicate 'color' metadata for '{name}'"
                    )
                if not val.isalpha() or val not in ALLOWED_COLORS:
                    raise ValueError(
                        f"invalid 'color' metadata for '{name}'"
                    )
                map_dict["hubs"][name]["metadata"]["color"] = val
            case "max_drones":
                if flag_max_drones:
                    raise ValueError(
                        f"duplicate 'max_drones' metadata for '{name}'"
                    )
                if not val.isdecimal():
                    raise ValueError(
                        f"invalid 'max_drones' metadata for '{name}' "
                        "(must be a valid positive integer)"
                        )
                map_dict["hubs"][name]["metadata"]["max_drones"] = int(val)
            case _:
                raise ValueError(f"invalid metadata for '{name}'")


def parse_connection(map_dict: Dict[str, Any], value: str) -> None:
    values = [v.strip() for v in value.split(' ', 1)]
    if len(values) == 0:
        raise ValueError("connection value cannot be empty")
    elif len(values) == 1:
        connection = values[0]
        metadata = None
    else:
        connection, metadata = values

    # Validate hub names
    try:
        name1, name2 = connection.split('-', 1)
    except BaseException:
        raise ValueError("missing hub name in connection")
    if name1 not in map_dict["hubs"].keys():
        raise ValueError(f"connection to undefined hub '{name1}'")
    if name2 not in map_dict["hubs"].keys():
        raise ValueError(f"connection to undefined hub '{name2}'")

    # Append connections with default value of 1
    map_dict["connections"][name1][name2] = 1
    map_dict["connections"][name2][name1] = 1

    # Stop here if no metadata
    if not metadata:
        return

    # Validate metadata
    if not (metadata.startswith('[') and metadata.endswith(']')):
        raise ValueError("metadata must be enclosed in brackets")

    md_values = [v.strip() for v in metadata[1:-1].split()]
    flag_capacity = False
    for v in md_values:
        try:
            key, val = v.split('=', 1)
        except BaseException:
            raise ValueError("missing '=' for metadata value")
        match key:
            case "max_link_capacity":
                if flag_capacity:
                    raise ValueError(
                        "duplicate 'max_link_capacity' connection metadata"
                    )
                if not val.isdecimal():
                    raise ValueError(
                        "'max_link_capacity' value must be "
                        "a valid positive integer"
                    )
                map_dict["connections"][name1][name2] = int(val)
                map_dict["connections"][name2][name1] = int(val)
            case _:
                raise ValueError(f"invalid connection metadata '{key}'")
