from collections import defaultdict, namedtuple
import heapq
import pyray as pr


class Graph(object):
    """ Graph data structure, undirected by default. """

    def __init__(self, app):
        self.app = app
        self.map_data = self.app.map_data
        self.weight_graph = defaultdict(dict)
        self.drone_map = defaultdict(dict)

        self.init_graph()
        self.init_drone_data()
        self.nodes = list(self.weight_graph.keys())

    def __str__(self):
        return f"{self.__class__.__name__} ({dict(self.weight_graph)})"

    def init_graph(self):
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

    def init_drone_data(self):
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

    def blocked_this_turn(self, a, b) -> float:
        a, b = self.nodes[a], self.nodes[b]
        # Adds 1 weight if hub is full this turn
        if (
            len(self.drone_map[b]["drones"]) >= self.drone_map[b]["capacity"]
            or len(self.drone_map[a]["links"][b])
            >= self.map_data["connections"][a][b]
        ):
            return 1
        # Allows a free hub to be picked over an equally weighted occupied one
        if (
            0 < len(self.drone_map[b]["drones"])
                < self.drone_map[b]["capacity"]
        ):
            return 0.5
        return 0

    def dijkstra(self, start, end):
        nodes = self.nodes
        graph = [[] for _ in range(len(nodes))]
        prev = [None] * len(nodes)

        def shortest_path(graph, start):
            pq = []
            dist = [float('inf')] * len(graph)

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

        def add_edge(graph, a, b, weight):
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
        path = [end]
        cur = nodes.index(end)
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
        # Convert path ton named tuples ("name": name, "position": (x, 1, y))
        Target = namedtuple("Target", ["name", "position"])
        targets = []
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
        for hub, data in self.drone_map.items():
            self.drone_map[hub]["drones"] = []
            for link in data["links"]:
                self.drone_map[hub]["links"][link] = []
