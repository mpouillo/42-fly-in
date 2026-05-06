import pyray as pr
from typing import Any, Dict, List
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
    def __init__(self, map_data: Dict[Any, Any]) -> None:
        self.map_data: Dict[str, Any] = map_data
        self.graph: Graph = Graph(self)

        self.compute_map_dimensions()
        self.color_toggle: bool = False
        self.turns: int = 0

    def compute_map_dimensions(self) -> None:
        s_x = min(self.map_data["hubs"].values(), key=lambda hub: hub["x"])
        s_y = min(self.map_data["hubs"].values(), key=lambda hub: hub["y"])
        b_x = max(self.map_data["hubs"].values(), key=lambda hub: hub["x"])
        b_y = max(self.map_data["hubs"].values(), key=lambda hub: hub["y"])

        self.map_size: pr.Vector2 = pr.Vector2(
            b_x["x"] - s_x["x"] + 1, b_y["y"] - s_y["y"] + 1)
        self.map_center: pr.Vector2 = pr.Vector2(
            (b_x["x"] + s_x["x"]) / 2, (b_y["y"] + s_y["y"]) / 2)

    def get_start_hub_name(self) -> Any:
        for name, hub in self.map_data["hubs"].items():
            if hub["hub_type"] == "start_hub":
                return name
        return None

    def get_end_hub_name(self) -> Any:
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
        self.width = monitor_width // 3 * 2
        self.height = monitor_height // 3 * 2
        pr.set_window_size(self.width, self.height)
        pr.set_window_position((monitor_width - self.width) // 2,
                               (monitor_height - self.height) // 2)
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
        font = pr.load_font("assets/superstar_memesbruh03.ttf")
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

    def load_drones(self) -> List[Drone]:
        drones: List[Drone] = []
        for i in range(self.map_data["nb_drones"]):
            drones.append(Drone(self, i))
        return drones

    def draw_connections(self) -> None:
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

    def get_hub_color(self, hub_type: str) -> pr.Color:
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

    def draw_hubs(self) -> None:
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

    def print_drone_info(self,
                         drones: List[Drone],
                         reverse: bool = False) -> None:
        print(f"Turn {self.turns}:")
        for drone in drones:
            if (
                drone.step > 0
                and drone.path[drone.step].name
                != drone.path[drone.step - 1].name
                and self.map_data["hubs"][drone.path[drone.step].name]
                ["zone"] == "restricted"
            ):
                print(f"D{drone.id + 1}-{drone.path[drone.step - 1].name}-"
                      f"{drone.path[drone.step].name} ", end="", flush=True)

            elif (
                drone.step > 0
                and drone.path[drone.step].name
                != drone.path[drone.step - 1].name
                or self.map_data["hubs"][drone.path[drone.step].name]
                ["zone"] == "restricted"
            ):
                print(f"D{drone.id + 1}-{drone.target.name} ",
                      end="", flush=True)
        print()

    def draw_hud(self) -> None:
        margin = 40
        position = pr.Vector2(margin, margin)
        ratio = 25
        font_size = min(self.width // ratio, self.height // ratio)
        font = self.assets.get("arial", "font")

        # FPS
        frame_time = pr.get_frame_time()
        if frame_time > 0:
            text = "FPS: " + str(round(1 / frame_time))
            pr.draw_text_ex(font, text, position, font_size, 0, pr.WHITE)

        # Turns
        position.y += font_size + margin // 2
        text = "Turn: " + str(self.turns)
        pr.draw_text_ex(font, text, position, font_size, 0, pr.WHITE)

        # Rectangle data
        rect_size = font_size * 2
        rect_weight = 10

        # Next/Prev
        position = pr.Vector2(margin, (self.height - rect_size - margin) // 2)
        rectangle = pr.Rectangle(position.x, position.y, rect_size, rect_size)
        text = "Next turn"
        text_size = pr.measure_text_ex(font, text, font_size, 0)
        text_pos = pr.Vector2(rectangle.x + rect_size + margin // 2,
                              rectangle.y + (rect_size - text_size.y) / 2)
        poly_pos = pr.Vector2(rectangle.x + rect_size / 2,
                              rectangle.y + rect_size / 2)
        if pr.is_key_down(pr.KEY_RIGHT):
            pr.draw_rectangle_rec(rectangle, pr.WHITE)
            pr.draw_poly(poly_pos, 3, rect_size / 3, 0, pr.BLACK)
        else:
            pr.draw_rectangle_lines_ex(rectangle, rect_weight, pr.WHITE)
            pr.draw_poly(poly_pos, 3, rect_size / 3, 0, pr.WHITE)
        pr.draw_text_ex(font, text, text_pos, font_size, 0, pr.WHITE)

        position = pr.Vector2(margin, (self.height + rect_size + margin) // 2)
        rectangle = pr.Rectangle(position.x, position.y, rect_size, rect_size)
        text = "Prev turn"
        text_size = pr.measure_text_ex(font, text, font_size, 0)
        text_pos = pr.Vector2(rectangle.x + rect_size + margin // 2,
                              rectangle.y + (rect_size - text_size.y) / 2)
        poly_pos = pr.Vector2(rectangle.x + rect_size / 2,
                              rectangle.y + rect_size / 2)
        if pr.is_key_down(pr.KEY_LEFT):
            pr.draw_rectangle_rec(rectangle, pr.WHITE)
            pr.draw_poly(poly_pos, 3, rect_size / 3, 180, pr.BLACK)
        else:
            pr.draw_rectangle_lines_ex(rectangle, rect_weight, pr.WHITE)
            pr.draw_poly(poly_pos, 3, rect_size / 3, 180, pr.WHITE)
        pr.draw_text_ex(font, text, text_pos, font_size, 0, pr.WHITE)

        # Camera
        position = pr.Vector2(self.width - margin, self.height - margin)
        rectangle = pr.Rectangle(position.x - rect_size,
                                 position.y - rect_size,
                                 rect_size, rect_size)
        text = "Toggle view"
        key = "Q"
        text_size = pr.measure_text_ex(font, text, font_size, 0)
        key_size = pr.measure_text_ex(font, key, font_size, 0)
        text_pos = pr.Vector2(rectangle.x - margin // 2 - text_size.x,
                              rectangle.y + (rect_size - text_size.y) / 2)
        key_pos = pr.Vector2(rectangle.x + (rect_size - key_size.x) / 2,
                             rectangle.y + (rect_size - key_size.y) / 2)
        if pr.is_key_down(pr.KEY_Q):
            pr.draw_rectangle_rec(rectangle, pr.WHITE)
            pr.draw_text_ex(font, key, key_pos, font_size, 0, pr.BLACK)
        else:
            pr.draw_rectangle_lines_ex(rectangle, rect_weight, pr.WHITE)
            pr.draw_text_ex(font, key, key_pos, font_size, 0, pr.WHITE)
        pr.draw_text_ex(font, text, text_pos, font_size, 0, pr.WHITE)

        # Colors
        position.y -= rect_size + margin // 2
        rectangle = pr.Rectangle(position.x - rect_size,
                                 position.y - rect_size,
                                 rect_size, rect_size)
        text = "Toggle colors"
        key = "E"
        text_size = pr.measure_text_ex(font, text, font_size, 0)
        key_size = pr.measure_text_ex(font, key, font_size, 0)
        text_pos = pr.Vector2(rectangle.x - margin // 2 - text_size.x,
                              rectangle.y + (rect_size - text_size.y) / 2)
        key_pos = pr.Vector2(rectangle.x + (rect_size - key_size.x) / 2,
                             rectangle.y + (rect_size - key_size.y) / 2)
        if pr.is_key_down(pr.KEY_E):
            pr.draw_rectangle_rec(rectangle, pr.WHITE)
            pr.draw_text_ex(font, key, key_pos, font_size, 0, pr.BLACK)
        else:
            pr.draw_rectangle_lines_ex(rectangle, rect_weight, pr.WHITE)
            pr.draw_text_ex(font, key, key_pos, font_size, 0, pr.WHITE)
        pr.draw_text_ex(font, text, text_pos, font_size, 0, pr.WHITE)

        # Controls
        position = pr.Vector2(margin, self.height - margin - rect_size)
        rectangle = pr.Rectangle(position.x, position.y, rect_size, rect_size)

        text = "A"
        text_size = pr.measure_text_ex(font, text, font_size, 0)
        text_pos = pr.Vector2(rectangle.x + (rect_size - text_size.x) / 2,
                              rectangle.y + (rect_size - text_size.y) / 2)
        if pr.is_key_down(pr.KEY_A):
            pr.draw_rectangle_rec(rectangle, pr.WHITE)
            pr.draw_text_ex(font, text, text_pos, font_size, 0, pr.BLACK)
        else:
            pr.draw_rectangle_lines_ex(rectangle, rect_weight, pr.WHITE)
            pr.draw_text_ex(font, text, text_pos, font_size, 0, pr.WHITE)

        rectangle.x += rect_size + position.x // 2
        text = "S"
        text_size = pr.measure_text_ex(font, text, font_size, 0)
        text_pos = pr.Vector2(rectangle.x + (rect_size - text_size.x) / 2,
                              rectangle.y + (rect_size - text_size.y) / 2)
        if pr.is_key_down(pr.KEY_S):
            pr.draw_rectangle_rec(rectangle, pr.WHITE)
            pr.draw_text_ex(font, text, text_pos, font_size, 0, pr.BLACK)
        else:
            pr.draw_rectangle_lines_ex(rectangle, rect_weight, pr.WHITE)
            pr.draw_text_ex(font, text, text_pos, font_size, 0, pr.WHITE)

        rectangle.x += rect_size + position.x // 2
        text = "D"
        text_size = pr.measure_text_ex(font, text, font_size, 0)
        text_pos = pr.Vector2(rectangle.x + (rect_size - text_size.x) / 2,
                              rectangle.y + (rect_size - text_size.y) / 2)
        if pr.is_key_down(pr.KEY_D):
            pr.draw_rectangle_rec(rectangle, pr.WHITE)
            pr.draw_text_ex(font, text, text_pos, font_size, 0, pr.BLACK)
        else:
            pr.draw_rectangle_lines_ex(rectangle, rect_weight, pr.WHITE)
            pr.draw_text_ex(font, text, text_pos, font_size, 0, pr.WHITE)

        rectangle.x -= rect_size + position.x // 2
        rectangle.y -= rect_size + position.x // 2
        text = "W"
        text_size = pr.measure_text_ex(font, text, font_size, 0)
        text_pos = pr.Vector2(rectangle.x + (rect_size - text_size.x) / 2,
                              rectangle.y + (rect_size - text_size.y) / 2)
        if pr.is_key_down(pr.KEY_W):
            pr.draw_rectangle_rec(rectangle, pr.WHITE)
            pr.draw_text_ex(font, text, text_pos, font_size, 0, pr.BLACK)
        else:
            pr.draw_rectangle_lines_ex(rectangle, rect_weight, pr.WHITE)
            pr.draw_text_ex(font, text, text_pos, font_size, 0, pr.WHITE)

    def run(self) -> None:
        camera = Camera((-1, 1, 0), (1, 0, 0), self.map_center)
        self.assets = self.load_assets()
        self.drones = self.load_drones()

        while not pr.window_should_close():
            # Camera
            if pr.is_key_pressed(pr.KEY_Q):
                camera.toggle_perspective()
            camera.update()

            # Toggle better colors
            if pr.is_key_pressed(pr.KEY_E):
                self.color_toggle = not self.color_toggle

            # Drone movement
            self.graph.reset()
            if not any(drone.moving for drone in self.drones):
                if (
                    pr.is_key_down(pr.KEY_RIGHT)
                    and (any(drone.step < len(drone.path) - 1
                         for drone in self.drones))
                ):
                    self.turns += 1
                    for drone in self.drones:
                        drone.go_next()
                    self.print_drone_info(self.drones)
                if (
                    pr.is_key_down(pr.KEY_LEFT) and
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
            self.draw_hud()
            pr.end_drawing()

        # Cleanup
        self.assets.clear()
        for drone in self.drones:
            drone.unload()

        pr.close_window()
