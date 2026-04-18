import math
import pyray as pr
from src.constants import DRONE_SPEED


class Drone:
    def __init__(self, start_pos):
        self.pos = start_pos
        self.direction = pr.Vector3(1, 0, 1)
        self.model = pr.load_model("assets/drone.obj")
        self.speed = DRONE_SPEED

        self.yaw = math.radians(90)
        self.pitch = 0.0

    def move(self, target) -> bool:

        diff = pr.Vector3(target.x - self.pos.x,
                          target.y - self.pos.y,
                          target.z - self.pos.z)

        distance = pr.vector3_length(diff)

        # Update angle
        self.yaw = math.atan2(diff.x, diff.z)
        ground_dist = math.sqrt(diff.x ** 2 + diff.z ** 2)
        self.pitch = math.atan2(diff.y, ground_dist)

        # Update position
        if distance > 0.1:
            move_step = pr.vector3_scale(
                pr.vector3_normalize(diff), self.speed * pr.get_frame_time()
            )
            self.pos = pr.vector3_add(self.pos, move_step)
            return True
        else:
            return False

    def update(self):
        rotation_axis = pr.Vector3(0, 1, 0)
        rotation_angle = math.degrees(self.yaw) - 90
        pr.draw_model_ex(self.model,
                         self.pos,
                         rotation_axis,
                         rotation_angle,
                         pr.Vector3(0.2, 0.2, 0.2),
                         pr.BLUE)

    def unload(self):
        pr.unload_model(self.model)
