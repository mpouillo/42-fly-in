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
    def __init__(self, map_data):
        self.map_data = map_data
        self.graph = Graph(map_data)

        s_x = min(map_data["hubs"].values(), key=lambda hub: hub["x"])
        s_y = min(map_data["hubs"].values(), key=lambda hub: hub["y"])
        b_x = max(map_data["hubs"].values(), key=lambda hub: hub["x"])
        b_y = max(map_data["hubs"].values(), key=lambda hub: hub["y"])
        self.map_size = pr.Vector2(
            b_x["x"] - s_x["x"] + 1, b_y["y"] - s_y["y"] + 1)
        self.map_center = pr.Vector2(
            (b_x["x"] + s_x["x"]) / 2, (b_y["y"] + s_y["y"]) / 2)

        pr.set_trace_log_level(pr.LOG_ERROR)    # Silence info logs
        pr.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Fly-in")
        pr.set_target_fps(TARGET_FPS)
        pr.rl_set_line_width(LINE_WIDTH)

        self.color_toggle = False

    def get_start_hub_name(self):
        for name, hub in self.map_data["hubs"].items():
            if hub["type"] == "start_hub":
                return name
        return None

    def get_end_hub_name(self):
        for name, hub in self.map_data["hubs"].items():
            if hub["type"] == "end_hub":
                return name
        return None

    def run(self):
        player = Player()
        camera = pr.Camera3D((0, 1, 0), (1, 1, 0), (0, 1, 0),
                             CAMERA_FOV, pr.CAMERA_PERSPECTIVE)

        texture = pr.load_texture_from_image(
            pr.load_image("assets/ground.jpg"))
        plane = pr.load_model_from_mesh(
            pr.gen_mesh_plane(self.map_size.x, self.map_size.y, 1, 1))
        plane.materials[0].maps[pr.MATERIAL_MAP_DIFFUSE].texture = texture

        drones = []
        for i in range(self.map_data["nb_drones"]):
            drone = Drone(pr.Vector3(0, i, 0), pr.Vector3(1, 0, 0))
            drone.compute_targets(self.graph, self.get_start_hub_name(),
                                  self.get_end_hub_name())
            drones.append(drone)

        while not pr.window_should_close():
            player.controls()
            camera.position = player.pos
            camera.target = pr.vector3_add(player.pos, player.direction)

            pr.begin_drawing()
            pr.clear_background(pr.SKYBLUE)
            pr.begin_mode_3d(camera)

            # Drone movement
            if pr.is_key_pressed(pr.KEY_BACKSPACE):
                if not any(drone.moving for drone in drones):
                    for drone in drones:
                        drone.run()

            #   Map rendering
            pr.draw_model(plane, pr.Vector3(
                self.map_center.x, 0, self.map_center.y), 1, pr.WHITE)
            self.draw_connections()
            self.draw_hubs()

            #  Drone updates
            for drone in drones:
                drone.move(self.graph)

            #   Toggle better colors
            if pr.is_key_pressed(pr.KEY_L):
                self.color_toggle = not self.color_toggle

            for drone in drones:
                drone.update()
            pr.end_mode_3d()
            pr.end_drawing()

        for drone in drones:
            drone.unload()
        pr.close_window()

    def draw_connections(self):
        for connection in self.graph.get_connections():
            start_x = self.map_data["hubs"][connection[0]]["x"]
            start_y = self.map_data["hubs"][connection[0]]["y"]
            end_x = self.map_data["hubs"][connection[1]]["x"]
            end_y = self.map_data["hubs"][connection[1]]["y"]
            pr.draw_line_3d((start_x, 0.01, start_y),
                            (end_x, 0.01, end_y), pr.BLUE)

    def draw_hubs(self):
        for hub in self.map_data.get("hubs", {}).values():
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
