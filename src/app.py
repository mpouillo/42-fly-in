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
        self.graph = Graph(map_data)

        self.compute_map_dimensions()
        self.color_toggle = False
        self.turns = 0

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
            if hub["type"] == "start_hub":
                return name
        return None

    def get_end_hub_name(self):
        for name, hub in self.map_data["hubs"].items():
            if hub["type"] == "end_hub":
                return name
        return None

    def init_window(self) -> None:
        screen_width = pr.get_screen_width()
        screen_height = pr.get_screen_height()
        pr.set_trace_log_level(pr.LOG_ERROR)    # Silence info logs
        pr.init_window(screen_width, screen_height, "Fly-in")
        pr.set_target_fps(TARGET_FPS)
        pr.rl_set_line_width(LINE_WIDTH)

    def load_assets(self) -> List[Any]:
        """Loads and returns a list of assets"""
        assets: List[Any] = []
        Asset = namedtuple("Asset", ["model", "texture", "pos", "scale"])

        # Ground plane
        texture = pr.load_texture_from_image(
            pr.load_image("assets/ground.jpg"))
        plane = pr.load_model_from_mesh(
            pr.gen_mesh_plane(self.map_size.x, self.map_size.y, 1, 1))
        plane.materials[0].maps[pr.MATERIAL_MAP_DIFFUSE].texture = texture
        assets.append(Asset(
            plane,
            texture,
            pr.Vector3(self.map_center.x, 0, self.map_center.y),
            1
        ))

        return assets

    def load_drones(self):
        drones: List[Drone] = []
        for i in range(self.map_data["nb_drones"]):
            drone = Drone(i,
                          pr.Vector3(0, 1 + i / self.map_data["nb_drones"], 0),
                          pr.Vector3(1, 0, 0),
                          self.graph)
            drone.compute_targets(self.get_start_hub_name(),
                                  self.get_end_hub_name())
            if i == 0 and not drone.targets:
                print("No valid path found between start_hub and end_hub!")
            drones.append(drone)
        return drones

    def unload_assets(self, assets: List[Any]):
        for asset in assets:
            pr.unload_texture(asset.texture)
            pr.unload_model(asset.model)

    def run(self):
        camera = Camera(pr.Vector3(-1, 1, 0),
                        pr.Vector3(0, 1, 1),
                        self.map_center)
        assets = self.load_assets()
        drones = self.load_drones()

        while not pr.window_should_close():
            # Camera
            if pr.is_key_pressed(pr.KEY_U):
                camera.toggle_perspective()
            camera.update()

            # Toggle better colors
            if pr.is_key_pressed(pr.KEY_L):
                self.color_toggle = not self.color_toggle

            # Drone movement
            if pr.is_key_down(pr.KEY_R):
                if any(not drone.at_goal() for drone in drones):
                    if not any(drone.moving for drone in drones):
                        self.graph.reset_connections()
                        self.turns += 1
                        for drone in drones:
                            drone.move()
                        print("Turn", self.turns)

            pr.begin_drawing()
            pr.clear_background(pr.SKYBLUE)
            pr.begin_mode_3d(camera.camera)

            #   Map rendering
            for asset in assets:
                pr.draw_model(asset.model, asset.pos, asset.scale, pr.WHITE)
            self.draw_connections()
            self.draw_hubs()

            #  Drone updates
            for drone in drones:
                drone.update()
                drone.render()

            pr.end_mode_3d()
            pr.end_drawing()

        # Cleanup
        self.unload_assets(assets)
        for drone in drones:
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
                return pr.RAYWHITE
