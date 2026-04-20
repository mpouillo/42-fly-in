from collections import defaultdict
import heapq


class Graph(object):
    """ Graph data structure, undirected by default. """

    def __init__(self, map_data, directed=False):
        self._map_data = map_data
        self._directed = directed
        self._graph = defaultdict(dict)
        self.add_connections()
        self.drones = self.drone_state()

    def drone_state(self):
        drone_map = defaultdict(dict)
        for name, data in self._map_data["hubs"].items():
            drone_map[name] = data["metadata"]["max_drones"]
        return drone_map


    def __str__(self):
        return f"{self.__class__.__name__} ({dict(self._graph)})"

    def add_connections(self):
        for connection in self._map_data["connections"]:
            node1, node2 = connection.get("node1"), connection.get("node2")
            data = self._map_data["hubs"][node2]
            match data["metadata"]["zone"]:
                case "blocked":
                    weight = float('inf') # To change later
                case "restricted":
                    weight = 2
                case "priority":
                    weight = 0.5 # To change later
                case _:
                    weight = 1
            self._graph[node1][node2] = weight
            self._graph[node2][node1] = weight

    def get_connections(self):
        connections = []
        for hub1, neighbors in self._graph.items():
            for hub2 in neighbors.keys():
                connections.append((hub1, hub2))
        return connections

    def dijkstra(self, start, end):
        nodes = list(self._graph.keys())
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
        for name1, neighbor in self._graph.items():
            for name2, weight in neighbor.items():
                add_edge(graph, nodes.index(name1), nodes.index(name2), weight)

        # Get shortest path from end to start
        prev = shortest_path(graph, nodes.index(start))

        # Iterate from end to start and convert indexes to strings
        path = [end]
        cur = nodes.index(end)
        while cur != nodes.index(start):
            p = cur
            cur = prev[cur]
            path.append(nodes[cur])
            # Increasing weight if a drone selects a restricted hub
            if self._map_data["hubs"][nodes[p]]["metadata"]["zone"] == (
                "restricted"
            ):
                self._graph[nodes[cur]][nodes[p]] += 1
                self._graph[nodes[p]][nodes[cur]] += 1

        path.reverse()
        return path
