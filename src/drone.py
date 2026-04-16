import math
import pyray as pr
from src.constants import DRONE_SIZE


class Drone:
    def __init__(self, start_pos):
        self.pos = start_pos
        self.direction = pr.Vector3(1, 0, 1)

        self.yaw = math.atan2(self.direction.x, self.direction.z)
        self.pitch = math.radians(-45)

    def move(self, x, y):
        dx, dy, dz = x - self.pos.x, y - self.pos.y, 0
        self.yaw = math.atan2(dx, dz)
        ground_dist = math.sqrt(dx**2 + dz**2)
        self.pitch = math.atan2(dy, ground_dist)

        sin_yaw, cos_yaw = math.sin(self.yaw), math.cos(self.yaw)
        self.direction.x = math.cos(self.pitch) * sin_yaw
        self.direction.y = math.sin(self.pitch)
        self.direction.z = math.cos(self.pitch) * cos_yaw

        self.pos.x, self.pos.z = x, y

    def update(self):
        pr.draw_capsule(self.pos, self.pos, DRONE_SIZE, 32, 32, pr.RED)
