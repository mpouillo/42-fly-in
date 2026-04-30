import math
import random
import pyray as pr
from src.constants import DRONE_SPEED
from src.entity import Entity

ANIM_SPEED = 3

class DroneAnim:
    def __init__(self):
        self.model: pr.Model = pr.load_model("assets/drone.glb")
        self.anim_offset = pr.Vector3(0, 0, 0)
        self.speed = DRONE_SPEED
        self.anim_step = random.randrange(0, 628) / 100

    def render(self) -> None:
        """Draw Drone model at current position"""
        rotation_axis = pr.Vector3(0, 1, 0)
        rotation_angle = math.degrees(self.yaw) - 90
        pos = pr.vector3_add(self.position, self.anim_offset)
        pr.draw_model_ex(self.model,
                         pos,
                         rotation_axis,
                         rotation_angle,
                         pr.Vector3(0.2, 0.2, 0.2),
                         pr.WHITE)

    def animate(self):
        # Update position depending on animation state
        amplitude = 0.2
        self.anim_offset.y = (1 + math.sin(self.anim_step)) * amplitude

    def update(self):
        self.anim_step = (self.anim_step + pr.get_frame_time() * ANIM_SPEED) % (math.pi * 2)
        self.animate()
        self.render()


class Drone(Entity, DroneAnim):
    def __init__(self, app, drone_id):
        Entity.__init__(self)
        DroneAnim.__init__(self)
        self.app = app
        self.id = drone_id

        self.path = []
        self.step = 0
        self.moving = False
        self.target = None

        self.compute_path()
        self.move(self.path[0].position, True)

    def compute_path(self):
        # Update path, computing it with start at current drone position
        start = self.app.get_start_hub_name()
        end = self.app.get_end_hub_name()
        if not self.path:
            self.path = self.app.graph.dijkstra(start, end)
        else:
            start = self.path[self.step].name
            path_from_start = self.app.graph.dijkstra(start, end)

            # Append end on calls if already at end
            if len(path_from_start) == 1 and path_from_start[0].name in [p.name for p in self.path]:
                self.path.extend(path_from_start)
                return

            # Append new path differently depending on if drone is on a restricted zone
            if self.step > 0 and self.path[self.step].name == self.path[self.step - 1].name and self.app.graph.drone_map[self.path[self.step].name]["type"] == "restricted":
                self.path = self.path[:self.step] + path_from_start[1:]
            else:
                self.path = self.path[:self.step] + path_from_start

    def go_next(self):
        self.compute_path()
        prev_target = self.path[self.step]
        self.step = min(len(self.path) - 1, self.step + 1)
        self.target = self.path[self.step]
        self.app.graph.drone_map[self.target.name]["drones"].append(self.id)
        if prev_target.name != self.target.name:
            self.app.graph.drone_map[prev_target.name]["links"][self.target.name].append(self.id)
        self.moving = True

    def go_prev(self):
        self.step = max(0, self.step - 1)
        self.target = self.path[self.step]
        self.moving = True

    def update(self):
        if self.moving and self.target:
            self.move(self.target.position)
            if self.position == self.target.position:
                self.moving = False
                self.target = None
        super().update()

    def move(self, position: pr.Vector3, instant=False):
        if not position:
            return
        if instant:
            self.position = position
        else:
            super().move(position)

    def unload(self):
        pr.unload_model(self.model)
