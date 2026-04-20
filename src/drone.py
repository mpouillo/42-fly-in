import math
import pyray as pr
from src.constants import DRONE_SPEED
from src.entity import Entity
from src.graph import Graph


class Drone(Entity):
    def __init__(self, position, direction):
        super().__init__(position, direction)
        self.model = pr.load_model("assets/drone.obj")
        self.speed = DRONE_SPEED
        self.targets = []
        self.step = 1

    def update(self):
        rotation_axis = pr.Vector3(0, 1, 0)
        rotation_angle = math.degrees(self.yaw) - 90
        pr.draw_model_ex(self.model,
                         self.pos,
                         rotation_axis,
                         rotation_angle,
                         pr.Vector3(0.2, 0.2, 0.2),
                         pr.BLUE)

    def compute_targets(self, graph: Graph, start, end):
        path = graph.dijkstra(start, end)
        if not path:
            self.targets = []
            return
        print(path)
        targets = [pr.Vector3(graph._map_data["hubs"][hub]["x"], 1,
                   graph._map_data["hubs"][hub]["y"]) for hub in path]
        self.targets = targets

    def move(self, graph):
        if not 0 <= self.step < len(self.targets):
            return False
        if not self.check_next_hub_free(graph):
            return False
        if super().move(self.targets[self.step]):
            self.step += 1
            return True

    def unload(self):
        pr.unload_model(self.model)

    def check_next_hub_free(self, graph):
        return True
