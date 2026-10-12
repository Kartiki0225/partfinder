"""A binary min-heap, and the "top k" trick built on it.

A min-heap keeps its smallest item at the top. It is stored in a plain list:
the children of the item at position i sit at positions 2i + 1 and 2i + 2.

Finding the best k results out of n does not need a full sort. Keep a heap of
only k items. For each new item: add it, and if the heap now holds k + 1 items,
remove the smallest. What remains at the end is the k largest.
That costs O(n log k) instead of O(n log n) for sorting everything.
"""


class MinHeap:
    def __init__(self) -> None:
        self.items = []

    def __len__(self) -> int:
        return len(self.items)

    def peek(self):
        """The smallest item, without removing it."""
        return self.items[0]

    def push(self, item) -> None:
        """Add an item at the end, then let it rise to its place."""
        self.items.append(item)
        self._sift_up(len(self.items) - 1)

    def pop(self):
        """Remove and return the smallest item."""
        smallest = self.items[0]
        last = self.items.pop()
        if self.items:
            self.items[0] = last  # move the last item to the top, then let it sink
            self._sift_down(0)
        return smallest

    def _sift_up(self, index: int) -> None:
        while index > 0:
            parent = (index - 1) // 2
            if self.items[index] >= self.items[parent]:
                break
            self.items[index], self.items[parent] = self.items[parent], self.items[index]
            index = parent

    def _sift_down(self, index: int) -> None:
        size = len(self.items)
        while True:
            left, right = 2 * index + 1, 2 * index + 2
            smallest = index
            if left < size and self.items[left] < self.items[smallest]:
                smallest = left
            if right < size and self.items[right] < self.items[smallest]:
                smallest = right
            if smallest == index:
                break
            self.items[index], self.items[smallest] = self.items[smallest], self.items[index]
            index = smallest


def top_k(items, k: int, key) -> list:
    """The k items with the highest key, best first."""
    heap = MinHeap()
    for position, item in enumerate(items):
        # The position breaks ties, so two items with equal keys are never compared directly.
        heap.push((key(item), -position, item))
        if len(heap) > k:
            heap.pop()  # drop the weakest of the k + 1

    best = []
    while heap:
        best.append(heap.pop()[2])
    best.reverse()  # they came out weakest first
    return best
