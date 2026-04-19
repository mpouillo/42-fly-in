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
        self.graph = Graph(self.connections, False)

        print(self.graph.bfs(self.get_start_hub_name(), self.get_end_hub_name()))

        s_x = min(map_dict["hubs"].values(), key=lambda hub: hub["x"])
        s_y = min(map_dict["hubs"].values(), key=lambda hub: hub["y"])
        b_x = max(map_dict["hubs"].values(), key=lambda hub: hub["x"])
        b_y = max(map_dict["hubs"].values(), key=lambda hub: hub["y"])
        self.map_size = pr.Vector2(b_x["x"] - s_x["x"] + 1, b_y["y"] - s_y["y"] + 1)
        self.map_center = pr.Vector2((b_x["x"] + s_x["x"]) / 2, (b_y["y"] + s_y["y"]) / 2)

        pr.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Fly-in")
        pr.set_target_fps(TARGET_FPS)
        pr.rl_set_line_width(LINE_WIDTH)

        self.color_toggle = False

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
        path = self.graph.dijkstra(self.get_start_hub_name(),
                                    self.get_end_hub_name())
        hub_list = [pr.Vector3(self.map_dict["hubs"][hub]["x"], 1,
                    self.map_dict["hubs"][hub]["y"]) for hub in path]
        drone = Drone(hub_list[0], pr.Vector3(1, 0, 0))
        i = 1
        running = False

        texture = pr.load_texture_from_image(pr.load_image("assets/ground.jpg"))
        plane = pr.load_model_from_mesh(pr.gen_mesh_plane(self.map_size.x, self.map_size.y, 1, 1))
        plane.materials[0].maps[pr.MATERIAL_MAP_DIFFUSE].texture = texture

        while not pr.window_should_close():
            player.controls()
            camera.position = player.pos
            camera.target = pr.vector3_add(player.pos, player.direction)

            pr.begin_drawing()
            pr.clear_background(pr.SKYBLUE)
            pr.begin_mode_3d(camera)

            pr.draw_model(plane, pr.Vector3(self.map_center.x, 0, self.map_center.y), 1, pr.WHITE)

            self.draw_connections()
            self.draw_hubs()

            if i == len(hub_list):
                running = False
            if running:
                if not drone.move(hub_list[i]):
                    i += 1
                    running = False

            if pr.is_key_pressed(pr.KEY_BACKSPACE):
                running = not running

            if pr.is_key_pressed(pr.KEY_L):
                self.color_toggle = not self.color_toggle

            drone.update()
            pr.end_mode_3d()
            pr.draw_text("Total turns: " + str(i - 1), 11, 11, 24, pr.BLACK)
            pr.draw_text("Total turns: " + str(i - 1), 10, 10, 24, pr.RAYWHITE)
            pr.end_drawing()

        drone.unload()
        pr.close_window()

    def draw_connections(self):
        for c in self.connections:
            start_x = self.map_dict["hubs"][c[0]]["x"]
            start_y = self.map_dict["hubs"][c[0]]["y"]
            end_x = self.map_dict["hubs"][c[1]]["x"]
            end_y = self.map_dict["hubs"][c[1]]["y"]
            pr.draw_line_3d((start_x, 0.01, start_y),
                            (end_x, 0.01, end_y), pr.BLUE)

    def draw_hubs(self):
        for hub in self.map_dict.get("hubs", {}).values():
            if self.color_toggle:
                color = self.get_hub_color(hub["metadata"]["zone"])
            else:
                color = COLOR_MAP[hub['metadata']["color"]]
            pr.draw_cylinder((hub["x"], 0.02, hub["y"]), NODE_SIZE,
                             NODE_SIZE, 0.05, 32, color)

    def get_hub_color(self, hub_type: str):
        match hub_type:
            case "normal":
                return pr.GREEN
            case "blocked":
                return pr.BLACK
            case "restricted":
                return pr.RED
            case "priority":
                return pr.YELLOW
            case _:
                return pr.PURPLE
