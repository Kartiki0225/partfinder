"""An LRU (least recently used) cache.

It remembers the answers to recent searches. When it is full, it throws away
the entry that has gone unused for the longest time.

Two structures work together so that both operations take O(1) time:
  * a dictionary finds an entry by its key instantly
  * a doubly linked list keeps the entries in order of use, most recent first.
    Moving an entry to the front, or removing the last one, only changes a few links.

    head <-> newest <-> ... <-> oldest <-> tail
"""


class Node:
    def __init__(self, key=None, value=None) -> None:
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.nodes = {}  # key -> Node
        self.hits = 0
        self.misses = 0

        # Two empty marker nodes mean the real nodes always have a neighbour on
        # both sides, so there are no special cases for an empty list.
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.prev = self.head

    def __len__(self) -> int:
        return len(self.nodes)

    def get(self, key):
        """The stored value, or None. Reading an entry makes it the most recent."""
        node = self.nodes.get(key)
        if node is None:
            self.misses += 1
            return None
        self.hits += 1
        self._unlink(node)
        self._add_to_front(node)
        return node.value

    def put(self, key, value) -> None:
        if key in self.nodes:
            node = self.nodes[key]
            node.value = value
            self._unlink(node)
        else:
            node = Node(key, value)
            self.nodes[key] = node
        self._add_to_front(node)

        if len(self.nodes) > self.capacity:
            oldest = self.tail.prev
            self._unlink(oldest)
            del self.nodes[oldest.key]

    def _unlink(self, node: Node) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_to_front(self, node: Node) -> None:
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node
