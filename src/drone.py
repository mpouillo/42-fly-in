import math
import pyray as pr
from src.constants import DRONE_SPEED


class Drone:
    def __init__(self, position, direction):
        self.pos = position
        self.model = pr.load_model("assets/drone.obj")
        self.speed = DRONE_SPEED
        self.set_direction(direction)

    def set_direction(self, direction):
        self.yaw = math.atan2(direction.x, direction.z)
        ground_dist = math.sqrt(direction.x ** 2 + direction.z ** 2)
        self.pitch = math.atan2(direction.y, ground_dist)

    def move(self, target) -> bool:

        diff = pr.Vector3(target.x - self.pos.x,
                          target.y - self.pos.y,
                          target.z - self.pos.z)

        distance = pr.vector3_length(diff)
        self.set_direction(diff)

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
