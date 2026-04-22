import math
import pyray as pr
from collections import namedtuple
from typing import List, Any
from src.constants import DRONE_SPEED
from src.entity import Entity
from src.graph import Graph


class Drone(Entity):
    def __init__(self,
                 drone_id: int,
                 position: pr.Vector3,
                 direction: pr.Vector3,
                 graph: Graph):
        super().__init__(position, direction)
        self.id: int = drone_id
        self.graph: Graph = graph

        self.model: pr.Model = pr.load_model("assets/drone.obj")
        self.speed: float = DRONE_SPEED

        self.moving: bool = False
        self.sleep: bool = False
        self.targets: List[namedtuple] = []
        self.step: int = 1

    def render(self) -> None:
        """Draw Drone model at current position"""
        rotation_axis = pr.Vector3(0, 1, 0)
        rotation_angle = math.degrees(self.yaw) - 90
        pr.draw_model_ex(self.model,
                         self.position,
                         rotation_axis,
                         rotation_angle,
                         pr.Vector3(0.2, 0.2, 0.2),
                         pr.RAYWHITE)

    def compute_targets(self, start: str, end: str) -> None:
        path: List[Any] = self.graph.dijkstra(start, end)
        if not path:
            self.targets = []
            return

        # Create list of named tuples
        Target = namedtuple("Target", ["name", "position"])
        self.targets = [Target(
                hub, pr.Vector3(self.graph.map_data["hubs"][hub]["x"], 1,
                                self.graph.map_data["hubs"][hub]["y"])
            ) for hub in path
        ]

        # Add drone to first hub
        self.graph.drone_map[
            self.targets[self.step - 1].name
        ]["drones"].append(self.id)

    def at_goal(self) -> bool:
        """Return whether drone is currently at last target"""
        return self.step >= len(self.targets)

    def is_restricted_hub(self, hub: str) -> bool:
        """Explicit name."""
        return self.graph.drone_map[hub]["type"] == "restricted"

    def update(self) -> None:
        """Try moving to current target"""
        if not self.moving:
            return

        target = self.targets[self.step]
        drones_on_hub = self.graph.drone_map[target.name]["drones"]
        new_y = drones_on_hub.index(self.id) / len(drones_on_hub)

        if super().move(
            pr.vector3_add(target.position, pr.Vector3(0, new_y, 0))
        ):
            self.step += 1
            self.stop()

    def stop(self) -> None:
        """Stops drone and align horizontally"""
        self.moving = False
        new_direction = pr.Vector3(
            self.direction.x, math.sin(0), self.direction.z)
        self.set_direction(new_direction)
        self.render()

    def move(self) -> None:
        """Attempt to set self.moving to True if requirements are met"""
        if self.at_goal():
            self.sleep = True
            self.step -= 1

        current = self.targets[self.step - 1].name
        target = self.targets[self.step].name

        # If current hub is restricted, set it once as next target
        if self.is_restricted_hub(current):
            self.sleep = not self.sleep
            self.step -= self.sleep is True

        current = self.targets[self.step - 1].name
        target = self.targets[self.step].name

        if not self.can_move(current, target):
            return

        self.moving = True

    def can_move(self, current, target):
        current_data = self.graph.drone_map[current]
        target_data = self.graph.drone_map[target]

        if self.id in target_data["drones"]:
            return True

        if (
            target_data["capacity"] > len(target_data["drones"])
            and (self.graph.map_data["connections"][current][target]
                 > len(current_data["links"][target]))
        ):
            target_data["drones"].append(self.id)
            current_data["drones"].remove(self.id)
            current_data["links"][target].append(self.id)
            return True

        return False

    def unload(self):
        pr.unload_model(self.model)
