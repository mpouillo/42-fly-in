import math
import pyray as pr
from src.constants import DRONE_SPEED
from src.entity import Entity


class DroneAnim:
    def __init__(self):
        self.model: pr.Model = pr.load_model("assets/drone.obj")
        self.anim_offset = pr.Vector3(0, 0, 0)
        self.speed = DRONE_SPEED

    def render(self) -> None:
        """Draw Drone model at current position"""
        rotation_axis = pr.Vector3(0, 1, 0)
        rotation_angle = math.degrees(self.yaw) - 90
        pr.draw_model_ex(self.model,
                         self.position,
                         rotation_axis,
                         rotation_angle,
                         pr.Vector3(0.2, 0.2, 0.2),
                         pr.WHITE)

    def animate(self):
        # Update position depending on animation state
        pass

    def update(self):
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
        if self.path:
            start = self.path[self.step].name
        else:
            start = self.app.get_start_hub_name()
        end = self.app.get_end_hub_name()
        path_from_start = self.app.graph.dijkstra(start, end)

        self.path.extend(path_from_start) # Fix stuff appending infinitely

    def go_next(self):
        self.step = min(len(self.path), self.step + 1)
        self.target = self.path[self.step]
        self.moving = True

    def go_prev(self):
        self.step = max(0, self.step - 1)
        self.target = self.path[self.step]
        self.moving = True

    def update(self):
        if self.moving and self.target:
            self.move(self.target.position)

            if self.position == self.target.position:
                print([p.name for p in self.path]) # Fix stuff appending infinitely
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
