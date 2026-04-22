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
        if not hasattr(self, "model"):
            print("wsh quoi")
        self.app = app
        self.id = drone_id

        self.moving = False
        self.target = None
        self.hub = None

        self.move(self.app.get_start_hub_name(), True)

    def compute_path(self):
        start = self.hub
        end = self.app.get_end_hub_name()
        path = self.app.graph.dijkstra(start, end)

        if not path:
            path = [self.hub]

        return path

    def go_to(self, target):
        self.target = target
        self.moving = True
        pass

    def update(self):
        if self.target:
            self.move(self.target.position)

            if self.position == self.target.position:
                self.hub = self.target
                self.target = None
                self.moving = False

        super().update()

    def move(self, position: pr.Vector3, instant=False):
        if not position or position == self.position:
            return

        if instant:
            self.position = position
        else:
            # interpolate position
            pass

    def unload(self):
        pr.unload_model(self.model)
