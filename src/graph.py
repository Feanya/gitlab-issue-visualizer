from model.classes import Epic
from src.utils import dict_string


class EpicGraph:
    def __init__(self, epics: dict[int, Epic]):
        self.length = len(epics.values())

        # Give each epic a graph_id independent of its uid
        self.epics: dict[int, Epic] = {}
        for k, epic in enumerate(epics.values()):
            self.epics[k] = epic

        # Graph relations
        self.next: dict[int, list[int]] = {}
        self.previous: dict[int, list[int]] = {}
        self.related: dict[int, list[int]] = {}
        self.includes: dict[int, list[int]] = {}
        self.includedBy: dict[int, list[int]] = {}
        # Tree properties
        self.node_heights: dict[int, int] = {}  # Largest Distance from a root node, as a node may have multiple roots
        self.node_parents: dict[int, int] = {}  # Direct parent node
        self.tree_widths: dict[int, int] = {}  # Largest number children of a node or its children

        self.analyze_graph()
        self.swap_related_trees()

        # print("Nodes:\n", dict_string(self.epics, padding=4), "\n----")
        # print("Next:\n", dict_string(self.next, padding=4, include_falsy=False), "\n----")
        # print("Previous:\n", dict_string(self.previous, padding=4, include_falsy=False), "\n----")
        # print("Related:\n", dict_string(self.related, padding=4, include_falsy=False), "\n----")
        # print("Included:\n", dict_string(self.includes, padding=4, include_falsy=False), "\n----")
        # print("IncludedBy:\n", dict_string(self.includedBy, padding=4, include_falsy=False), "\n----")

    def __len__(self):
        return self.length

    def find_epic_with_epic_id(self, epic_id: int) -> Epic:
        """This returns the epic that belongs to the given epic_id"""

        for k, v in self.epics.items():
            if v.uid == epic_id:
                return v
        return None

    def find_graph_id_with_epic_id(self, epic_id: int) -> Epic:
        """This returns the graph_id where the epic with the given epic_id can be found"""

        for k, v in self.epics.items():
            if v.uid is epic_id:
                return k
        return None

    def analyze_graph(self):
        """Analyse the epics in regard to their relationships and the height and width of the tree subgraph they
        belong to.
        """

        for k in range(len(self)):
            self.next[k] = []
            self.previous[k] = []
            self.includes[k] = []
            self.includedBy[k] = []
            self.related[k] = []

        for n, epic in self.epics.items():

            # analyze the description to find links
            if epic.description:
                lines = epic.description.splitlines()
                for line in lines:
                    if 'previous' in line \
                            or 'next' in line \
                            or 'include' in line \
                            or 'related' in line:
                        target_epic_id = None
                        for t in line.split():
                            if 'https:' in t:
                                target_epic_id = int(t.split('/')[-1].rstrip('+'))
                                target_graph_id = self.find_graph_id_with_epic_id(target_epic_id)
                            else:
                                continue
                            if target_graph_id:
                                # next and previous connections as directed edges
                                if 'previous' in line:
                                    if target_graph_id not in self.previous[n]:
                                        self.previous[n].append(target_graph_id)
                                    if n not in self.next[target_graph_id]:
                                        self.next[target_graph_id].append(n)
                                elif 'next' in line:
                                    if target_graph_id not in self.next[n]:
                                        self.next[n].append(target_graph_id)
                                    if n not in self.previous[target_graph_id]:
                                        self.previous[target_graph_id].append(n)
                                # includes as directed edges
                                elif 'include' in line:
                                    self.includes[n].append(target_graph_id)
                                    self.includedBy[target_graph_id].append(n)
                                # related as undirected edges
                                elif 'related' in line:
                                    self.related[n].append(target_graph_id)
                                    if n not in self.related[target_graph_id]:
                                        self.related[target_graph_id].append(n)
                                else:
                                    raise ValueError(
                                        f"An epic description has a target id but no valid relation. {epic.uid} -> {target_epic_id}")

        for i in range(len(self)):
            self.node_heights[i] = self.get_height(i)
            self.tree_widths[i] = self.get_width(i)

    def swap_related_trees(self):
        """A heuristic that checks whether any two trees are related to each other, and swaps them with unrelated
        trees to have related ones closer to each other """

        roots = self.get_roots()
        trees = []
        for root in roots:
            trees.append(self.get_tree(root))
        related_roots = self.get_related_tree_roots(trees)
        for i in range(len(related_roots)):
            a, b = related_roots[i]
            self.swap_graph_ids(a + 1, b)  # Put b next to a
            # Update references to future occurrences of (a+1) and b,
            # to not swap the wrong trees in case they appear more than once.
            for j in range(i + 1, len(related_roots)):
                if b == related_roots[j][0]:
                    related_roots[j] = (a + 1, related_roots[j][1])
                elif b == related_roots[j][1]:
                    related_roots[j] = (related_roots[j][0], a + 1)
                elif (a + 1) == related_roots[j][0]:
                    related_roots[j] = (b, related_roots[j][1])
                elif (a + 1) == related_roots[j][1]:
                    related_roots[j] = (related_roots[j][0], b)

    def get_height(self, node_id):
        """Recursively determine the height and parent of the given node.

        If a node has multiple parents the one with the largest height will be chosen

        Returns - the height of the given node_id
        """

        if node_id in self.node_heights.keys():
            return self.node_heights[node_id]

        prev_nodes = [prev_node for prev_node in self.previous[node_id] if prev_node is not None]
        prev_nodes.extend([including_node for including_node in self.includedBy[node_id] if including_node is not None])

        if not prev_nodes:
            self.node_heights[node_id] = 0
            self.node_parents[node_id] = node_id
            return 0

        prev_nodes.sort(key=lambda n: self.get_height(n), reverse=True)
        self.node_heights[node_id] = 1 + self.get_height(prev_nodes[0])
        self.node_parents[node_id] = prev_nodes[0]

        return self.node_heights[node_id]

    def get_width(self, node_id):
        """Recursively determines the width of a tree, with node_id as its root,
        by adding the widths of its child subtrees

        Returns - the width of the given node_id
        """

        if node_id in self.tree_widths.keys():
            return self.tree_widths[node_id]

        next_nodes = [next_node for next_node in self.next[node_id] if next_node is not None]
        next_nodes.extend([included_node for included_node in self.includes[node_id] if included_node is not None])

        if not next_nodes:
            self.tree_widths[node_id] = 1
            return 1

        self.tree_widths[node_id] = sum([self.get_width(node) for node in next_nodes])
        return self.tree_widths[node_id]

    def swap_graph_ids(self, a: int, b: int):
        """Swaps the nodes with the ids a and b"""

        temp = self.epics[a]
        self.epics[a] = self.epics[b]
        self.epics[b] = temp

        list_dicts: list[dict[int, list[int]]] = [self.next, self.previous, self.related,
                                                  self.includes, self.includedBy]
        int_dicts: list[dict[int, int]] = [self.node_heights, self.node_parents, self.tree_widths]
        for dictionary in list_dicts:
            # swap lists
            temp = dictionary[a]
            dictionary[a] = dictionary[b]
            dictionary[b] = temp
            # update all references
            for k, v in dictionary.items():
                if a in v and b in v:
                    continue
                elif a in v:
                    v.remove(a)
                    v.append(b)
                elif b in v:
                    v.remove(b)
                    v.append(a)
        for dictionary in int_dicts:
            # swap lists
            temp = dictionary[a]
            dictionary[a] = dictionary[b]
            dictionary[b] = temp
            # update all references
            for k, v in dictionary.items():
                if v == a:
                    dictionary[k] = b
                elif v == b:
                    dictionary[k] = a

    def get_roots(self) -> [int]:
        """Returns all roots in the graph.

        Roots are nodes without any previous or includedBy nodes.
        """

        roots = []
        for i in self.epics.keys():
            if self.previous[i]:
                continue
            if self.includedBy[i]:
                continue
            roots.append(i)
        return roots

    def get_orphans(self, roots: list[int] = None) -> [int]:
        """Returns all orphans in the graph.

        Orphans are nodes without any connections to other nodes.

        Arguments:
            roots: Optional, a list of root nodes in case it already calculated beforehand.
        """
        if roots is None:
            roots = self.get_roots()
        orphans = []
        for root in roots:
            if self.next[root]:
                continue
            if self.includes[root]:
                continue
            if self.related[root]:
                continue
            orphans.append(root)
        return orphans

    def get_tree(self, root: int) -> [int]:
        """Recursively returns a list of nodes that are part of the given root's tree
        using the next and includes relationships. The root is always the first element of the list"""

        linked_nodes = [root]
        for next in self.next[root]:
            linked_nodes.extend(self.get_tree(next))
        for included in self.includes[root]:
            linked_nodes.extend(self.get_tree(included))
        return linked_nodes

    def get_related_tree_roots(self, trees: list[list[int]]) -> list[tuple[int, int]]:
        """Given a list of trees, this function returns a list of pairs of the trees' roots,
        if those trees' nodes are related through any relation."""
        related_trees: list[tuple[int, int]] = []
        for i in range(0, len(trees) - 1):
            related_nodes = [self.related[node] for node in trees[i]]
            related_nodes.extend([self.includes[node] for node in trees[i]])
            related_nodes.extend([self.includedBy[node] for node in trees[i]])
            related_nodes.extend([self.next[node] for node in trees[i]])
            related_nodes.extend([self.previous[node] for node in trees[i]])

            related_nodes = [node for nodes in related_nodes for node in nodes]  # Flattens the list
            for j in range(i + 1, len(trees)):
                for node in related_nodes:
                    if node in trees[j]:
                        related_trees.append((i, j))
                        break

        related_tree_roots: list[tuple[int, int]] = [(trees[i][0], trees[j][0]) for (i, j) in related_trees]
        return related_tree_roots
