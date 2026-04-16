import pyray as pr
from src.graph import Graph
from src.player import Player
from src.constants import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    CAMERA_FOV,
    TARGET_FPS,
    NODE_SIZE,
    COLOR_MAP
)


class Game():
    def __init__(self):
        pass

    def startup(self):
        pass

    def render(self):
        pass

    def update(self):
        pass

    def shutdown(self):
        pass


def get_connections_from_map(map_dict):
    connections = []
    connect_list = map_dict.get("connections")
    if not connect_list:
        return []

    for c in connect_list:
        node1, node2 = c.get("node1"), c.get("node2")
        connections.append((node1, node2))

    return connections


def run_gui(map_dict):

    connections = get_connections_from_map(map_dict)
    graph = Graph(connections, True)
    graph

    pr.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Fly-in")
    pr.set_target_fps(TARGET_FPS)

    pr.rl_set_line_width(3)
    map_size = 10
    camera = pr.Camera3D((0, 0.5, 0), (1, 0.5, 1), (0, 1, 0),
                         CAMERA_FOV, pr.CAMERA_PERSPECTIVE)
    player = Player()

    while not pr.window_should_close():
        player.controls()
        camera.position = player.pos
        camera.target = pr.vector3_add(player.pos, player.direction)

        pr.begin_drawing()
        pr.clear_background(pr.SKYBLUE)
        pr.begin_mode_3d(camera)

        pr.draw_grid(map_size * 10, NODE_SIZE)
        pr.draw_plane((0, -0.01, 0), (map_size * 2, map_size * 2), pr.WHITE)

        for c in connections:
            start_x = map_dict["hubs"][c[0]]["x"]
            start_y = map_dict["hubs"][c[0]]["y"]
            end_x = map_dict["hubs"][c[1]]["x"]
            end_y = map_dict["hubs"][c[1]]["y"]
            pr.draw_line_3d((start_x, 0, start_y), (end_x, 0, end_y), pr.BLUE)

        for hub in map_dict.get("hubs", {}).values():
            color = COLOR_MAP[hub['metadata']["color"]]
            pr.draw_plane((hub["x"], 0.01, hub["y"]),
                          (NODE_SIZE, NODE_SIZE), color)

        pr.end_mode_3d()

        pr.end_drawing()

    pr.close_window()
