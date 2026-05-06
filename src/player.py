import math
import pyray as pr
from src.constants import MOVEMENT_SPEED


class Player():
    def __init__(self,
                 position: pr.Vector2,
                 direction: pr.Vector2):
        self.position: pr.Vector2 = position
        self.direction: pr.Vector2 = direction

        self.yaw: float = math.atan2(self.direction.x, self.direction.z)
        self.pitch: float = math.atan(self.direction.y)

        self.sensitivity: float = 0.001
        self.speed: float = MOVEMENT_SPEED
        pr.disable_cursor()

    def controls(self) -> None:
        speed: float = pr.get_frame_time() * self.speed
        mouse_delta: pr.Vector2 = pr.get_mouse_delta()
        self.yaw -= mouse_delta.x * self.sensitivity
        self.pitch = max(-1.57, min(1.57, self.pitch
                                    - mouse_delta.y * self.sensitivity))

        """Settings for keyboard-based camera movement"""
        # if pr.is_key_down(pr.KEY_RIGHT):
        #     self.yaw -= 0.07
        # if pr.is_key_down(pr.KEY_LEFT):
        #     self.yaw += 0.07
        # if pr.is_key_down(pr.KEY_DOWN):
        #     self.pitch = max(math.radians(-90), self.pitch - 0.07)
        # if pr.is_key_down(pr.KEY_UP):
        #     self.pitch = min(math.radians(90), self.pitch + 0.07)

        sin_yaw: float = math.sin(self.yaw)
        cos_yaw: float = math.cos(self.yaw)
        self.direction.x = math.cos(self.pitch) * sin_yaw
        self.direction.y = math.sin(self.pitch)
        self.direction.z = math.cos(self.pitch) * cos_yaw

        forward: int = pr.is_key_down(pr.KEY_W) - pr.is_key_down(pr.KEY_S)
        sideward: int = pr.is_key_down(pr.KEY_D) - pr.is_key_down(pr.KEY_A)
        upward: int = pr.is_key_down(pr.KEY_SPACE) - pr.is_key_down(pr.KEY_C)

        if forward != 0 and sideward != 0:
            speed *= 0.707

        nx: float = self.position.x
        ny: float = self.position.y
        nz: float = self.position.z

        nx += speed * (sin_yaw * forward - cos_yaw * sideward)
        ny += speed * upward
        nz += speed * (cos_yaw * forward + sin_yaw * sideward)

        self.position.x, self.position.y, self.position.z = nx, max(1, ny), nz
