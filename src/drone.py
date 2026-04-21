import math
import pyray as pr
from collections import namedtuple
from src.constants import DRONE_SPEED
from src.entity import Entity
from src.graph import Graph


class Drone(Entity):
    def __init__(self, drone_id, position, direction, drone_map):
        super().__init__(position, direction)
        self.model = pr.load_model("assets/drone.obj")
        self.drone_map = drone_map
        self.id = drone_id
        self.speed = DRONE_SPEED
        self.targets = []
        self.step = 1
        self.sleep = False
        self.moving = False

    def update(self):
        rotation_axis = pr.Vector3(0, 1, 0)
        rotation_angle = math.degrees(self.yaw) - 90
        pr.draw_model_ex(self.model,
                         self.position,
                         rotation_axis,
                         rotation_angle,
                         pr.Vector3(0.2, 0.2, 0.2),
                         pr.BLUE)

    def compute_targets(self, graph: Graph, start, end):
        path = graph.dijkstra(start, end)
        if not path:
            self.targets = []
            return

        Target = namedtuple("Target", ["name", "position"])
        self.targets = [Target(
                hub, pr.Vector3(graph._map_data["hubs"][hub]["x"], 1,
                                graph._map_data["hubs"][hub]["y"])
            ) for hub in path
        ]
        self.drone_map[self.targets[self.step - 1].name]["drones"].append(self.id)

    def at_goal(self):
        return self.step >= len(self.targets)

    def move(self):
        if not self.moving:
            return

        target = self.targets[self.step]
        drones_on_hub = self.drone_map[target.name]["drones"]
        new_y = drones_on_hub.index(self.id) / len(drones_on_hub)
        if super().move(
            pr.vector3_add(target.position, pr.Vector3(0, new_y, 0))
        ):
            self.step += 1
            self.stop()
            if self.at_goal():
                self.drone_map[target.name]["drones"].remove(self.id)

    def can_move(self):
        current = self.drone_map[self.targets[self.step - 1].name]
        target = self.drone_map[self.targets[self.step].name]

        if self.id in target["drones"]:
            return True

        if current["type"] == "restricted":
            self.sleep = not self.sleep

        if not self.sleep and target["capacity"] > len(target["drones"]):
            target["drones"].append(self.id)
            return True
        else:
            return False

    def stop(self):
        self.moving = False

    def run(self):
        if self.at_goal():
            return

        current = self.drone_map[self.targets[self.step - 1].name]
        target = self.drone_map[self.targets[self.step].name]

        if current["type"] == "restricted":
            self.sleep = not self.sleep

        if not self.sleep and target["capacity"] > len(target["drones"]):
            target["drones"].append(self.id)
            current["drones"].remove(self.id)

        if self.id in target["drones"]:
            self.moving = True

    def unload(self):
        pr.unload_model(self.model)
