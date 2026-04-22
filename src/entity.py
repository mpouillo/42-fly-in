import math
import pyray as pr


class Entity:
    def __init__(self, position: pr.Vector3, direction: pr.Vector3):
        self.position = position
        self.direction = direction
        self.speed: float = 1
        self.set_direction(direction)

    def set_direction(self, new_direction: pr.Vector3) -> None:
        self.yaw = math.atan2(new_direction.x, new_direction.z)
        ground_dist = math.sqrt(new_direction.x ** 2 + new_direction.z ** 2)
        self.pitch = math.atan2(new_direction.y, ground_dist)
        self.direction.x = math.cos(self.pitch) * math.sin(self.yaw)
        self.direction.y = math.sin(self.pitch)
        self.direction.z = math.cos(self.pitch) * math.cos(self.yaw)

    def move(self, target: pr.Vector3) -> bool:
        """
        Updates position each frame, related to speed.
        Returns False if it still needs to move, or True if it arrived.
        """
        diff = pr.Vector3(target.x - self.position.x,
                          target.y - self.position.y,
                          target.z - self.position.z)

        distance = pr.vector3_length(diff)
        self.set_direction(diff)

        if distance > 0.1:
            move_step = pr.vector3_scale(pr.vector3_normalize(diff),
                                         self.speed * pr.get_frame_time())
            self.position = pr.vector3_add(self.position, move_step)
            return False

        # If arrived (distance < 0.5)
        return True
