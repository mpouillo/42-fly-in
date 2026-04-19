from collections import defaultdict, deque
import heapq


class Graph(object):
    """ Graph data structure, undirected by default. """

    def __init__(self, connections, directed=False):
        self._graph = defaultdict(set)
        self._directed = directed
        self.add_connections(connections)

    def __str__(self):
        return f"{self.__class__.__name__} ({dict(self._graph)})"

    def add_connections(self, connections):
        """ Add connections (list of tuple pairs) to graph """
        for node1, node2 in connections:
            self.add(node1, node2)

    def add(self, node1, node2):
        """ Add connection between node1 and node2 """
        self._graph[node1].add(node2)
        if not self._directed:
            self._graph[node2].add(node1)

    def remove(self, node):
        """ Remove all references to node """
        for n, cxns in self._graph.items():
            try:
                cxns.remove(node)
            except KeyError:
                pass
        try:
            del self._graph[node]
        except KeyError:
            pass

    def is_connected(self, node1, node2):
        """ Is node1 directly connected to node2 """
        return node1 in self._graph and node2 in self._graph[node1]

    def find_path(self, node1, node2, path=None):
        """ Find any path between node1 and node2 (may not be the shortest) """
        if path is None:
            path = []
        path = path + [node1]
        if node1 == node2:
            return path
        if node1 not in self._graph:
            return None
        for node in self._graph[node1]:
            if node not in path:
                new_path = self.find_path(node, node2, path)
                if new_path:
                    return new_path
        return None

    def bfs(self, start_name, end_name):
        def solve(start_name):
            q = deque()
            q.append(start_name)

            visited = {name: False for name in self._graph.keys()}
            visited[start_name] = True

            prev = {name: None for name in self._graph.keys()}

            while q:
                node = q.popleft()
                for neighbor in self._graph[node]:
                    if visited[neighbor] == False:
                        q.append(neighbor)
                        visited[node] = True
                        prev[neighbor] = node

            return prev

        def reconstructPath(start_name, end_name, prev):
            path = []
            node = end_name

            while node:
                path.append(node)
                node = prev[node]

            path.reverse()

            if path[0] == start_name:
                return path
            return []

        prev = solve(start_name)
        return reconstructPath(start_name, end_name, prev)

    def dijkstra(self, start, end):
        nodes = list(self._graph.keys())
        v = len(nodes)
        graph = [[] for _ in range(v)]
        prev = [None] * v

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

        for hub in self._graph:
            for neighbor in self._graph[hub]:
                weight = 1
                # match neighbor["metadata"]["type"]
                #   case "restricted":
                #       weight = 2
                #   case "priority"
                #       ...
                add_edge(graph, nodes.index(hub), nodes.index(neighbor), weight)

        prev = shortest_path(graph, nodes.index(start))

        path = [end]
        cur = nodes.index(end)
        while cur != nodes.index(start):
            cur = prev[cur]
            path.append(nodes[cur])

        path.reverse()
        return path


# dijkstra ->
# si zone restricted : valeur "future_weight" incrémentée par chaque drone qui choisit un chemin qui passe par le hub
# -> la valeur est ajoutée au weight de la node pour le calcul du drone suivant
