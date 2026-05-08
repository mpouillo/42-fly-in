from collections import defaultdict, namedtuple
import heapq
import pyray as pr
from typing import Any, Dict, List

Target = namedtuple("Target", ["name", "position"])


class Graph(object):
    """
    Graph data structure, undirected by default.

    Keyword arguments:
    app -- the parent application
    """

    def __init__(self, app: Any) -> None:
        """Initialize required default values."""
        self.app: Any = app
        self.map_data: Dict[str, Any] = self.app.map_data
        self.weight_graph: Dict[str, Any] = defaultdict(dict)
        self.drone_map: Dict[str, Any] = defaultdict(dict)

        self.init_graph()
        self.init_drone_data()
        self.hubs: List[str] = list(self.weight_graph.keys())

    def __str__(self) -> str:
        """Return a view of the internal weighted graph."""
        return f"{self.__class__.__name__} ({dict(self.weight_graph)})"

    def init_graph(self) -> None:
        """Initialize weight_graph from map_data values."""
        weight: float = 0
        for hub1, neighbors in self.map_data["connections"].items():
            for hub2, max_link_capacity in neighbors.items():
                hub2_data = self.map_data["hubs"][hub2]
                match hub2_data["zone"]:
                    case "restricted":
                        weight = 2
                    case "priority":
                        weight = 0.99
                    case _:
                        weight = 1
                self.weight_graph[hub1][hub2] = weight
                self.weight_graph[hub2][hub1] = weight

    def init_drone_data(self) -> None:
        """Initialize drone_map from map_data values."""
        for name, data in self.map_data["hubs"].items():
            self.drone_map[name] = {
                "capacity": data["max_drones"],
                "type": data["zone"],
                "drones": [],
                "links": defaultdict(list)
            }
        for hub1, neighbors in self.map_data["connections"].items():
            for hub2 in neighbors.keys():
                self.drone_map[hub1]["links"][hub2] = []

    def blocked_this_turn(self, a: int, b: int) -> float:
        """Return additional weight if drone is blocked this turn."""
        hub1: str = self.hubs[a]
        hub2: str = self.hubs[b]

        # Adds 1 weight if hub is full this turn
        if (
            len(self.drone_map[hub2]["drones"])
            >= self.drone_map[hub2]["capacity"]
            or len(self.drone_map[hub1]["links"][hub2])
            >= self.map_data["connections"][hub1][hub2]
        ):
            return 1

        # Allows a free hub to be picked over an equally weighted occupied one
        if (
            0 < len(self.drone_map[hub2]["drones"])
                < self.drone_map[hub2]["capacity"]
        ):
            return 0.001

        return 0

    def dijkstra(self, start: str, end: str) -> List[Target]:
        """Compute and return shortest path from start to end hubs."""
        nodes: List[str] = self.hubs
        graph: List[Any] = [[] for _ in range(len(nodes))]
        prev: List[None] = [None] * len(nodes)

        def shortest_path(graph: List[Any], start: int) -> List[Any]:
            """Return a list of shortest previous hub for each hub."""
            pq: List[Any] = []
            dist: List[float] = [float('inf')] * len(graph)

            heapq.heappush(pq, (0, start))
            dist[start] = 0

            while pq:
                distance, a = heapq.heappop(pq)
                for b, weight in graph[a]:
                    w = dist[a] + weight
                    if a == start:
                        w += self.blocked_this_turn(a, b)
                    if w < dist[b]:
                        prev[b] = a
                        dist[b] = w
                        heapq.heappush(pq, (dist[b], b))
            return (prev)

        def add_edge(graph: List[Any], a: int, b: int, weight: int) -> None:
            """Add an edge to a graph."""
            graph[a].append((b, weight))

        # Create graph with index values instead of strings
        for name1, neighbor in self.weight_graph.items():
            for name2, weight in neighbor.items():
                # Skip blocked hubs
                if (
                    self.map_data["hubs"][name1]["zone"] == "blocked"
                    or self.map_data["hubs"][name2]["zone"] == "blocked"
                    or self.map_data["connections"][name1][name2] < 1
                    or self.map_data["connections"][name2][name1] < 1
                    or self.map_data["hubs"][name1]["max_drones"] < 1
                    or self.map_data["hubs"][name2]["max_drones"] < 1
                ):
                    continue
                add_edge(graph, nodes.index(name1), nodes.index(name2), weight)

        # Get shortest path from end to start
        prev = shortest_path(graph, nodes.index(start))

        # Iterate from end to start and convert indexes to strings
        path: List[str] = [end]
        cur: Any = nodes.index(end)
        nex: Any = None
        while cur != nodes.index(start):
            nex = cur
            cur = prev[cur]
            if cur is None:
                break
            path.append(nodes[cur])
            # Double restricted nodes in path
            if (self.drone_map[nodes[cur]]["type"] == "restricted"):
                path.append(nodes[cur])
            # x2 nodes if blocked that turn (max_drones or max_link_capacity)
            if (
                len(self.drone_map[nodes[nex]]["drones"])
                >= self.drone_map[nodes[nex]]["capacity"]
                or len(self.drone_map[nodes[cur]]["links"][nodes[nex]])
                >= self.map_data["connections"][nodes[cur]][nodes[nex]]
            ):
                path.append(nodes[cur])

        if cur is None:
            path = [start]

        path.reverse()
        # Convert path to named tuples ("name": name, "position": (x, 1, y))
        targets: List[Target] = []
        for i, hub in enumerate(path):
            if (
                0 < i < len(path) - 1
                and path[i] == path[i + 1]
                and self.map_data["hubs"][path[i]]["zone"] == "restricted"
            ):
                x = (self.map_data["hubs"][path[i]]["x"]
                     + self.map_data["hubs"][path[i - 1]]["x"]) / 2
                z = (self.map_data["hubs"][path[i]]["y"]
                     + self.map_data["hubs"][path[i - 1]]["y"]) / 2
            else:
                x = self.map_data["hubs"][hub]["x"]
                z = self.map_data["hubs"][hub]["y"]
            step = Target(hub, pr.Vector3(x, 1, z))
            targets.append(step)

        return targets

    def reset(self) -> None:
        """Reset values for drone_map."""
        for hub, data in self.drone_map.items():
            self.drone_map[hub]["drones"] = []
            for link in data["links"]:
                self.drone_map[hub]["links"][link] = []
