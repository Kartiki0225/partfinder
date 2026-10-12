r"""A trie (prefix tree): the data structure behind autocomplete.

Every word is stored letter by letter along a path from the root. Words that
start the same way share the start of their path, so finding every word that
begins with "fi" means walking two steps down and collecting what is below.

        (root)
        /    \
       f      p
      / \      \
     i   u      u
     |   |      |
     l   e      m
     |   |      |
     t   l*     p*        * marks the end of a word: "fuel", "pump"
     ...
"""


class TrieNode:
    def __init__(self) -> None:
        self.children = {}  # letter -> TrieNode
        self.count = 0      # how many times a word ending here was inserted (0 = not a word)


class Trie:
    def __init__(self) -> None:
        self.root = TrieNode()
        self.words = 0  # number of different words stored
        self.nodes = 1  # number of nodes, counting the root

    def insert(self, word: str) -> None:
        """Add a word. Inserting the same word again raises its count."""
        node = self.root
        for letter in word:
            if letter not in node.children:
                node.children[letter] = TrieNode()
                self.nodes += 1
            node = node.children[letter]
        if node.count == 0:
            self.words += 1
        node.count += 1

    def _find(self, prefix: str) -> TrieNode | None:
        """Walk down the letters of prefix. None if the path does not exist."""
        node = self.root
        for letter in prefix:
            node = node.children.get(letter)
            if node is None:
                return None
        return node

    def count(self, word: str) -> int:
        """How many times this exact word was inserted (0 if never)."""
        node = self._find(word)
        return node.count if node else 0

    def __contains__(self, word: str) -> bool:
        return self.count(word) > 0

    def starting_with(self, prefix: str) -> list[tuple[str, int]]:
        """Every stored word that begins with prefix, as (word, count) pairs."""
        start = self._find(prefix)
        if start is None:
            return []

        found = []
        stack = [(start, prefix)]  # depth-first search without recursion
        while stack:
            node, word = stack.pop()
            if node.count:
                found.append((word, node.count))
            for letter, child in node.children.items():
                stack.append((child, word + letter))
        return found
