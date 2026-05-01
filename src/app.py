import pyray as pr
from typing import List, Any
from collections import namedtuple
from src.graph import Graph
from src.drone import Drone
from src.camera import Camera
from src.constants import (
    TARGET_FPS,
    NODE_SIZE,
    COLOR_MAP,
    LINE_WIDTH,
    CONNECTION_COLOR
)


class App():
    def __init__(self, map_data):
        self.map_data = map_data
        self.graph = Graph(self)

        self.compute_map_dimensions()
        self.color_toggle = False
        self.turns = 0
        self.drones = []
        self.assets = []

    def compute_map_dimensions(self) -> None:
        s_x = min(self.map_data["hubs"].values(), key=lambda hub: hub["x"])
        s_y = min(self.map_data["hubs"].values(), key=lambda hub: hub["y"])
        b_x = max(self.map_data["hubs"].values(), key=lambda hub: hub["x"])
        b_y = max(self.map_data["hubs"].values(), key=lambda hub: hub["y"])

        self.map_size = pr.Vector2(
            b_x["x"] - s_x["x"] + 1, b_y["y"] - s_y["y"] + 1)
        self.map_center = pr.Vector2(
            (b_x["x"] + s_x["x"]) / 2, (b_y["y"] + s_y["y"]) / 2)

    def get_start_hub_name(self):
        for name, hub in self.map_data["hubs"].items():
            if hub["hub_type"] == "start_hub":
                return name
        return None

    def get_end_hub_name(self):
        for name, hub in self.map_data["hubs"].items():
            if hub["hub_type"] == "end_hub":
                return name
        return None

    def init_window(self) -> None:
        screen_width = 1920
        screen_height = 1080
        pr.set_trace_log_level(pr.LOG_ERROR)    # Silence info logs
        pr.init_window(screen_width, screen_height, "Fly-in")
        pr.set_target_fps(TARGET_FPS)
        pr.rl_set_line_width(LINE_WIDTH)

    def load_assets(self) -> List[Any]:
        """Loads and returns a list of assets"""
        Asset = namedtuple("Asset", ["model", "texture", "pos", "scale"])

        # Ground plane
        texture = pr.load_texture_from_image(
            pr.load_image("assets/ground.jpg"))
        plane = pr.load_model_from_mesh(
            pr.gen_mesh_plane(self.map_size.x, self.map_size.y, 1, 1))
        plane.materials[0].maps[pr.MATERIAL_MAP_DIFFUSE].texture = texture
        self.assets.append(Asset(
            plane,
            texture,
            pr.Vector3(self.map_center.x, 0, self.map_center.y),
            1
        ))

    def unload_assets(self, assets: List[Any]):
        for asset in self.assets:
            pr.unload_texture(asset.texture)
            pr.unload_model(asset.model)
        self.assets.clear()

    def load_drones(self):
        for i in range(self.map_data["nb_drones"]):
            self.drones.append(Drone(self, i))

    def run(self):
        camera = Camera(pr.Vector3(-1, 1, 0),
                        pr.Vector3(0, 1, 1),
                        self.map_center)
        self.load_assets()
        self.load_drones()

        while not pr.window_should_close():
            # Camera
            if pr.is_key_pressed(pr.KEY_U):
                camera.toggle_perspective()
            camera.update()

            # Toggle better colors
            if pr.is_key_pressed(pr.KEY_L):
                self.color_toggle = not self.color_toggle

            # Drone movement
            self.graph.reset()
            if not any(drone.moving for drone in self.drones):
                if pr.is_key_pressed(pr.KEY_T) and any(drone.step != len(drone.path) - 1 for drone in self.drones):
                    self.turns += 1
                    print("Turn", self.turns)
                    for drone in self.drones:
                        drone.go_next()
                if pr.is_key_pressed(pr.KEY_R) and any(drone.step != 0 for drone in self.drones):
                    self.turns = max(0, self.turns - 1)
                    print("Turn", self.turns)
                    for drone in self.drones:
                        drone.go_prev()

            pr.begin_drawing()
            pr.clear_background(pr.SKYBLUE)
            pr.begin_mode_3d(camera.camera)

            #   Map rendering
            for asset in self.assets:
                pr.draw_model(asset.model, asset.pos, asset.scale, pr.WHITE)
            self.draw_connections()
            self.draw_hubs()

            #  Drone updates
            for drone in self.drones:
                drone.update()

            pr.end_mode_3d()

            # HUD display
            ft = pr.get_frame_time()
            if ft != 0:
                pr.draw_text("FPS: " + str(round(1 / pr.get_frame_time())), 20, 20, 48, pr.WHITE)
            pr.draw_text("TURN: " + str(self.turns), 20, 80, 48, pr.WHITE)

            pr.end_drawing()

        # Cleanup
        self.unload_assets(self.assets)
        for drone in self.drones:
            drone.unload()

        pr.close_window()

    def draw_connections(self):
        for hub1, neighbors in self.map_data["connections"].items():
            # Draw lines
            for hub2, max_link_capacity in neighbors.items():
                start_x = self.map_data["hubs"][hub1]["x"]
                start_y = self.map_data["hubs"][hub1]["y"]
                end_x = self.map_data["hubs"][hub2]["x"]
                end_y = self.map_data["hubs"][hub2]["y"]
                pr.draw_line_3d((start_x, 0.01, start_y),
                                (end_x, 0.01, end_y), CONNECTION_COLOR)

            # Draw max_link_capacity values
            img = pr.image_text(str(max_link_capacity), 1, pr.RAYWHITE)
            texture = pr.load_texture_from_image(img)
            plane = pr.load_model_from_mesh(pr.gen_mesh_plane(0.1, 0.1, 1, 1))
            plane.materials[0].maps[pr.MATERIAL_MAP_DIFFUSE].texture = texture
            pr.draw_model(
                plane,
                pr.Vector3((end_x + start_x) / 2, 0.02, (end_y + start_y) / 2),
                1,
                pr.WHITE
            )
            pr.unload_model(plane)
            pr.unload_texture(texture)

    def draw_hubs(self):
        for hub in self.map_data.get("hubs", {}).values():
            if self.color_toggle:
                color = self.get_hub_color(hub["zone"])
            else:
                color = COLOR_MAP[hub["color"]]
            pr.draw_cylinder((hub["x"], 0, hub["y"]), NODE_SIZE,
                             NODE_SIZE, 0.05, 32, color)

            # Draw max drones values
            img = pr.image_text(str(hub["max_drones"]), 1, pr.RAYWHITE)
            texture = pr.load_texture_from_image(img)
            plane = pr.load_model_from_mesh(pr.gen_mesh_plane(0.1, 0.1, 1, 1))
            plane.materials[0].maps[pr.MATERIAL_MAP_DIFFUSE].texture = texture
            pr.draw_model(plane, pr.Vector3(hub["x"], 0.07, hub["y"]), 1, pr.WHITE)

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
                return pr.RAYWHITE
