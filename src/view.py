import pyray as pr
from src.graph import Graph
from src.player import Player
from src.drone import Drone
from src.constants import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    CAMERA_FOV,
    TARGET_FPS,
    NODE_SIZE,
    COLOR_MAP,
    LINE_WIDTH
)


class Game():
    def __init__(self, map_dict):
        self.map_dict = map_dict
        self.connections = self.get_connections_from_map(map_dict)
        self.graph = Graph(self.connections, True)

        hub_max = max(map_dict["hubs"].values(),
                      key=lambda hub: hub["x"] + hub["y"])
        hub_min = min(map_dict["hubs"].values(),
                      key=lambda hub: hub["x"] + hub["y"])
        self.map_size = (hub_max["x"] + hub_max["y"]
                         - (hub_min["x"] + hub_min["y"]))

        pr.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Fly-in")
        pr.set_target_fps(TARGET_FPS)
        pr.rl_set_line_width(LINE_WIDTH)

    @staticmethod
    def get_connections_from_map(map_dict):
        connections = []
        c_mapping = map_dict.get("connections")
        if not c_mapping:
            return []

        for c in c_mapping:
            node1, node2 = c.get("node1"), c.get("node2")
            connections.append((node1, node2))

        return connections

    def get_start_hub_name(self):
        for name, hub in self.map_dict["hubs"].items():
            if hub["type"] == "start_hub":
                return name
        return None

    def get_end_hub_name(self):
        for name, hub in self.map_dict["hubs"].items():
            if hub["type"] == "end_hub":
                return name
        return None

    def run(self):
        player = Player()
        camera = pr.Camera3D((0, 1, 0), (1, 1, 0), (0, 1, 0),
                             CAMERA_FOV, pr.CAMERA_PERSPECTIVE)
        path = self.graph.find_path(self.get_start_hub_name(),
                                    self.get_end_hub_name())
        hub_list = [pr.Vector3(self.map_dict["hubs"][hub]["x"], 1,
                    self.map_dict["hubs"][hub]["y"]) for hub in path]
        drone = Drone(hub_list[0])
        i = 0
        started = False

        while not pr.window_should_close():
            player.controls()
            camera.position = player.pos
            camera.target = pr.vector3_add(player.pos, player.direction)

            pr.begin_drawing()
            pr.clear_background(pr.SKYBLUE)
            pr.begin_mode_3d(camera)

            pr.draw_grid(self.map_size * 10, NODE_SIZE)
            pr.draw_plane((0, -0.01, 0),
                          (self.map_size * 2, self.map_size * 2), pr.WHITE)
            self.draw_connections()
            self.draw_hubs()

            if i == len(hub_list):
                started = False
            if started:
                if not drone.move(hub_list[i]):
                    i += 1

            if pr.is_key_pressed(pr.KEY_BACKSPACE):
                started = not started

            drone.update()
            pr.end_mode_3d()
            pr.end_drawing()

        drone.unload()
        pr.close_window()

    def draw_connections(self):
        for c in self.connections:
            start_x = self.map_dict["hubs"][c[0]]["x"]
            start_y = self.map_dict["hubs"][c[0]]["y"]
            end_x = self.map_dict["hubs"][c[1]]["x"]
            end_y = self.map_dict["hubs"][c[1]]["y"]
            pr.draw_line_3d((start_x, 0, start_y),
                            (end_x, 0, end_y), pr.BLUE)

    def draw_hubs(self):
        for hub in self.map_dict.get("hubs", {}).values():
            color = COLOR_MAP[hub['metadata']["color"]]
            pr.draw_cylinder((hub["x"], 0, hub["y"]), NODE_SIZE,
                             NODE_SIZE, 0.01, 32, color)
