import math
import pyray as pr


class Player():
    def __init__(self):
        self.pos = pr.Vector3(0, 0.5, 0)
        self.yaw = 0
        self.pitch = -1

        self.sensitivity = 0.001
        self.direction = pr.Vector3(0, 0, 0)
        self.speed = 3
        pr.disable_cursor()

    def controls(self):
        speed = pr.get_frame_time() * self.speed
        mouse_delta = pr.get_mouse_delta()
        self.yaw -= mouse_delta.x * self.sensitivity
        self.pitch = max(-1.57, min(1.57, self.pitch
                                    - mouse_delta.y * self.sensitivity))
        sin_yaw, cos_yaw = math.sin(self.yaw), math.cos(self.yaw)

        self.direction.x = math.cos(self.pitch) * sin_yaw
        self.direction.y = math.sin(self.pitch)
        self.direction.z = math.cos(self.pitch) * cos_yaw

        forward = pr.is_key_down(pr.KEY_W) - pr.is_key_down(pr.KEY_S)
        sideward = pr.is_key_down(pr.KEY_D) - pr.is_key_down(pr.KEY_A)
        upward = pr.is_key_down(pr.KEY_SPACE) - pr.is_key_down(pr.KEY_C)

        if forward != 0 and sideward != 0:
            speed *= 0.707

        nx, ny, nz = self.pos.x, self.pos.y, self.pos.z

        nx += speed * (sin_yaw * forward - cos_yaw * sideward)
        ny += speed * upward
        nz += speed * (cos_yaw * forward + sin_yaw * sideward)

        self.pos.x, self.pos.y, self.pos.z = nx, ny, nz
