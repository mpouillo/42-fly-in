import pyray as pr
from typing import List
from src.graph import Graph
from src.assets import Assets
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
        pr.set_trace_log_level(pr.LOG_ERROR)    # Silence info logs
        pr.init_window(1280, 720, "Fly-in")
        monitor = pr.get_current_monitor()
        monitor_width = pr.get_monitor_width(monitor)
        monitor_height = pr.get_monitor_height(monitor)
        width = monitor_width // 3 * 2
        height = monitor_height // 3 * 2
        pr.set_window_size(width, height)
        pr.set_window_position((monitor_width - width) // 2,
                               (monitor_height - height) // 2)
        pr.set_target_fps(TARGET_FPS)
        pr.rl_set_line_width(LINE_WIDTH)

    def load_assets(self) -> Assets:
        """Loads and returns a list of assets"""
        assets = Assets()

        # Ground plane
        img = pr.load_image("assets/ground.jpg")
        assets.add("ground", "image", img)
        texture = pr.load_texture_from_image(img)
        assets.add("ground", "texture", texture)
        mesh = pr.gen_mesh_plane(self.map_size.x, self.map_size.y, 1, 1)
        assets.add("ground", "mesh", mesh)
        model = pr.load_model_from_mesh(mesh)
        model.materials[0].maps[pr.MATERIAL_MAP_DIFFUSE].texture = texture
        assets.add("ground", "model", model)

        # Font
        font = pr.load_font("assets/arial.ttf")
        assets.add("arial", "font", font)

        text, img, texture, mesh, model = None, None, None, None, None

        # Connections max_link_capacity
        for hub1, neighbors in self.map_data["connections"].items():
            for hub2, max_link_capacity in neighbors.items():
                connection_name = f"{hub1}-{hub2}"
                text = str(max_link_capacity)
                img = pr.image_text_ex(font, text, 96, 0, pr.RAYWHITE)
                assets.add(connection_name, "image", img)
                texture = pr.load_texture_from_image(img)
                assets.add(connection_name, "texture", texture)
                mesh = pr.gen_mesh_plane(0.1 * len(text) / 2, 0.1, 1, 1)
                assets.add(connection_name, "mesh", mesh)
                model = pr.load_model_from_mesh(mesh)
                model.materials[0].maps[pr.MATERIAL_MAP_DIFFUSE]\
                    .texture = texture
                assets.add(connection_name, "model", model)

        text, img, texture, mesh, model = None, None, None, None, None

        # Hubs max_drones
        for hub, data in self.map_data["hubs"].items():
            text = str(data["max_drones"])
            img = pr.image_text_ex(font, text, 96, 0, pr.RAYWHITE)
            assets.add(hub, "image", img)
            texture = pr.load_texture_from_image(img)
            assets.add(hub, "texture", texture)
            mesh = pr.gen_mesh_plane(0.2 * len(text) / 2, 0.2, 1, 1)
            assets.add(hub, "mesh", mesh)
            model = pr.load_model_from_mesh(mesh)
            model.materials[0].maps[pr.MATERIAL_MAP_DIFFUSE].texture = texture
            assets.add(hub, "model", model)

        return assets

    def load_drones(self):
        for i in range(self.map_data["nb_drones"]):
            self.drones.append(Drone(self, i))

    def run(self):
        camera = Camera(pr.Vector3(-1, 1, 0),
                        pr.Vector3(1, 0, 0),
                        self.map_center)
        self.assets = self.load_assets()
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
                if (
                    pr.is_key_down(pr.KEY_T)
                    and (any(drone.step < len(drone.path) - 1
                         for drone in self.drones))
                ):
                    self.turns += 1
                    for drone in self.drones:
                        drone.go_next()
                    self.print_drone_info(self.drones)
                if (
                    pr.is_key_down(pr.KEY_R) and
                    any(drone.step != 0 for drone in self.drones)
                ):
                    self.turns = max(0, self.turns - 1)
                    for drone in self.drones:
                        drone.go_prev()
                    self.print_drone_info(self.drones, True)

            pr.begin_drawing()
            pr.clear_background(pr.SKYBLUE)
            pr.begin_mode_3d(camera.camera)

            #   Map rendering
            ground = self.assets.get("ground", "model")
            pr.draw_model(ground, pr.Vector3(self.map_center.x, 0,
                          self.map_center.y), 1, pr.WHITE)
            self.draw_connections()
            self.draw_hubs()

            #  Drone updates
            for drone in self.drones:
                drone.update()

            pr.end_mode_3d()

            # HUD display
            ft = pr.get_frame_time()
            if ft != 0:
                pr.draw_text(
                    "FPS: " + str(round(1 / pr.get_frame_time())),
                    20, 20, 48, pr.WHITE
                )
            pr.draw_text("TURN: " + str(self.turns), 20, 80, 48, pr.WHITE)

            pr.end_drawing()

        # Cleanup
        self.assets.clear()
        for drone in self.drones:
            drone.unload()

        pr.close_window()

    def print_drone_info(self, drones: List[Drone], reverse=False) -> None:
        for drone in drones:
            if (
                drone.path[drone.step].name
                != drone.path[drone.step - 1].name
                and self.map_data["hubs"][drone.path[drone.step].name]
                ["zone"] == "restricted"
            ):
                print(f"D{drone.id + 1}-{drone.path[drone.step - 1].name}-"
                      f"{drone.path[drone.step].name} ", end="", flush=True)

            elif (
                drone.path[drone.step].name
                != drone.path[drone.step - 1].name
                or self.map_data["hubs"][drone.path[drone.step].name]
                ["zone"] == "restricted"
            ):
                print(f"D{drone.id + 1}-{drone.target.name} ",
                      end="", flush=True)

        print()

    def draw_connections(self):
        for hub1, neighbors in self.map_data["connections"].items():
            # Draw lines
            for hub2, max_link_capacity in neighbors.items():
                connection_name = f"{hub1}-{hub2}"
                start_x = self.map_data["hubs"][hub1]["x"]
                start_y = self.map_data["hubs"][hub1]["y"]
                end_x = self.map_data["hubs"][hub2]["x"]
                end_y = self.map_data["hubs"][hub2]["y"]
                pr.draw_line_3d((start_x, 0.01, start_y),
                                (end_x, 0.01, end_y), CONNECTION_COLOR)
                # Max_link_capacity
                pr.draw_model(self.assets.get(connection_name, "model"),
                              pr.Vector3((end_x + start_x) / 2, 0.02,
                                         (end_y + start_y) / 2), 1, pr.WHITE)

    def draw_hubs(self):
        for hub, data in self.map_data["hubs"].items():
            if self.color_toggle:
                color = self.get_hub_color(data["zone"])
            else:
                color = COLOR_MAP[data["color"]]

            pr.draw_cylinder((data["x"], 0, data["y"]), NODE_SIZE,
                             NODE_SIZE, 0.05, 32, color)
            # Max_drones
            pr.draw_model(self.assets.get(hub, "model"),
                          (data["x"], 0.06, data["y"]), 1, pr.RAYWHITE)

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
