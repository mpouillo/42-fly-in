from collections import defaultdict, namedtuple
import heapq
import pyray as pr


class Graph(object):
    """ Graph data structure, undirected by default. """

    def __init__(self, map_data):
        self.map_data = map_data
        self.weight_graph = defaultdict(dict)
        self.drone_map = defaultdict(dict)

        self.init_graph()
        self.init_drone_data()

    def __str__(self):
        return f"{self.__class__.__name__} ({dict(self.weight_graph)})"

    def init_graph(self):
        for hub1, neighbors in self.map_data["connections"].items():
            for hub2, max_link_capacity in neighbors.items():
                hub2_data = self.map_data["hubs"][hub2]
                match hub2_data["metadata"]["zone"]:
                    case "blocked":
                        weight = float('inf')
                    case "restricted":
                        weight = 2
                    case "priority":
                        weight = 0.5
                    case _:
                        weight = 1
                self.weight_graph[hub1][hub2] = weight
                self.weight_graph[hub2][hub1] = weight

    # def get_connections(self):
    #     connections = []
    #     for hub1, neighbors in self.weight_graph.items():
    #         for hub2 in neighbors.keys():
    #             connections.append((hub1, hub2))
    #     return connections

    def init_drone_data(self):
        for name, data in self.map_data["hubs"].items():
            self.drone_map[name] = {
                "capacity": data["metadata"]["max_drones"],
                "type": data["metadata"]["zone"],
                "drones": [],
                "links": defaultdict(dict)
            }
        for hub1, neighbors in self.map_data["connections"].items():
            for hub2 in neighbors.keys():
                self.drone_map[hub1]["links"][hub2] = []

    def dijkstra(self, start, end):
        nodes = list(self.weight_graph.keys())
        graph = [[] for _ in range(len(nodes))]
        prev = [None] * len(nodes)

        def add_edge(graph, a, b, weight):
            graph[a].append((b, weight))
            graph[b].append((a, weight))

        def shortest_path(graph, start):
            pq = []
            dist = [float('inf')] * len(graph)

            heapq.heappush(pq, (0, start))
            dist[start] = 0

            while pq:
                distance, u = heapq.heappop(pq)
                for v, weight in graph[u]:
                    new_weight = dist[u] + weight
                    if dist[v] > new_weight:
                        prev[v] = u
                        dist[v] = new_weight
                        heapq.heappush(pq, (dist[v], v))

            return (prev)

        # Create graph with index values instead of strings
        for name1, neighbor in self.weight_graph.items():
            for name2, weight in neighbor.items():
                if weight == float('inf'):
                    continue
                add_edge(graph, nodes.index(name1), nodes.index(name2), weight)

        # Get shortest path from end to start
        prev = shortest_path(graph, nodes.index(start))

        # Iterate from end to start and convert indexes to strings
        path = [end]
        cur = nodes.index(end)
        # restricted_hub = False
        while cur is not None and cur != nodes.index(start):
            # p = cur
            cur = prev[cur]
            path.append(nodes[cur])
            #if (
            #    not restricted_hub
            #    and self.map_data["hubs"][nodes[p]]["metadata"]["zone"] == (
            #        "restricted"
            #    )
            #):
            #    self.weight_graph[nodes[cur]][nodes[p]] += 1
            #    self.weight_graph[nodes[p]][nodes[cur]] += 1
            #    restricted_hub = True

        if cur is None:
            path = [start]

        Target = namedtuple("Target", ["name", "position"])
        named_path = [Target(
                hub, pr.Vector3(self.map_data["hubs"][hub]["x"], 1,
                                self.map_data["hubs"][hub]["y"])
            ) for hub in path
        ]

        named_path.reverse()
        return named_path

    def reset_connections(self) -> None:
        for hub, data in self.drone_map.items():
            for link in data["links"]:
                self.drone_map[hub]["links"][link] = []
