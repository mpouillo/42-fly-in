import math
import random
import pyray as pr
from src.constants import DRONE_SPEED, ANIM_SPEED
from src.entity import Entity
from typing import List, Any


class Drone(Entity):
    def __init__(self, app: Any, drone_id: int) -> None:
        super().__init__()
        self.app: Any = app
        self.id: int = drone_id

        self.model: pr.Model = pr.load_model("assets/drone.glb")
        self.anim_offset: pr.Vector3 = pr.Vector3(0, 0, 0)
        self.speed: float = DRONE_SPEED
        self.anim_step: float = 0
        self.rand_y_offset: float = random.randrange(0, 628) / 100

        self.path: List[Any] = []
        self.step: int = 0
        self.moving: bool = False
        self.target: Any = None

        self.compute_path()
        self.move(self.path[0].position, True)

    def compute_path(self) -> None:
        # Update path, computing it with start at current drone position

        # Return if at end node but not at end of path
        if (
            self.step < len(self.path) - 1
            and self.path[self.step].name == self.path[-1].name
        ):
            return

        start: str = self.app.get_start_hub_name()
        end: str = self.app.get_end_hub_name()
        if not self.path:
            self.path = self.app.graph.dijkstra(start, end)
        else:
            start = self.path[self.step].name
            path_from_start = self.app.graph.dijkstra(start, end)

            # Append end on calls if already at end
            if (
                len(path_from_start) == 1
                and path_from_start[0].name == self.path[-1].name
            ):
                self.path.extend(path_from_start)
                return

            # Append new path differently depending on
            # if drone is on a restricted zone
            if (
                self.step > 0
                and self.path[self.step].name == self.path[self.step - 1].name
                and self.app.graph.drone_map
                    [self.path[self.step].name]["type"] == "restricted"
            ):
                self.path = self.path[:self.step] + path_from_start[1:]
            elif self.path[self.step].name == self.path[-1].name:
                return
            else:
                self.path = self.path[:self.step + 1] + path_from_start[1:]

    def go_next(self) -> None:
        self.compute_path()
        prev_target: Any = self.path[self.step]
        self.step = min(len(self.path) - 1, self.step + 1)
        self.target = self.path[self.step]
        # Append drone id to hub if not at last hub
        if not self.target.name == self.path[-1].name:
            (self.app.graph.drone_map[self.target.name]
                ["drones"].append(self.id))
        # Append drone to connection if moving to a diff hub
        if prev_target.name != self.target.name:
            (self.app.graph.drone_map[prev_target.name]
                ["links"][self.target.name].append(self.id))
        self.moving = True

    def go_prev(self) -> None:
        self.step = max(0, self.step - 1)
        self.target = self.path[self.step]
        self.moving = True

    def move(self, position: pr.Vector3, instant: bool = False) -> None:
        if not position:
            return
        if instant:
            self.position = position
        else:
            super().move(position)

    def unload(self) -> None:
        pr.unload_model(self.model)

    def animate(self) -> None:
        """Update position depending on animation state."""
        amplitude: float = 0.2
        self.anim_offset.y = (
            (1 + math.sin(self.anim_step + self.rand_y_offset))
            * amplitude
        )

        # Count drones on same hub
        td: int = 0
        for drone in self.app.drones:
            if drone.path[self.step].name == self.path[self.step].name:
                td += 1
            if drone.id == self.id:
                pos = td

        # Animate position depending on how many drones are on the same hub
        if td > 1:
            self.anim_offset.x = (
                math.cos(self.anim_step + (math.pi * 2 * pos / td))
                * amplitude
            )
            self.anim_offset.z = (
                math.sin(self.anim_step + (math.pi * 2 * pos / td))
                * amplitude
            )
        else:
            self.anim_offset.x = 0
            self.anim_offset.z = 0

    def render(self) -> None:
        """Draw Drone model at current position"""
        rotation_axis: pr.Vector3 = pr.Vector3(0, 1, 0)
        rotation_angle: float = math.degrees(self.yaw) - 90
        pos: pr.Vector3 = pr.vector3_add(self.position, self.anim_offset)
        pr.draw_model_ex(self.model,
                         pos,
                         rotation_axis,
                         rotation_angle,
                         pr.Vector3(0.2, 0.2, 0.2),
                         pr.WHITE)

    def update(self) -> None:
        if self.moving and self.target:
            self.move(self.target.position)
            if self.position == self.target.position:
                self.moving = False
                self.target = None
        self.anim_step = (
            (self.anim_step + pr.get_frame_time() * ANIM_SPEED)
            % (math.pi * 2)
        )
        self.animate()
        self.render()
