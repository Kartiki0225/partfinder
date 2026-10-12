"""The search engine: finds parts for whatever the user types, typos included.

Built once, when the program starts:
  * index      a dictionary from each word to the set of parts that contain it
               (an "inverted index": instead of part -> words, it stores word -> parts)
  * trie       every word, for autocomplete and for matching half-typed words
  * by_number  a dictionary from part number to part, for exact lookups

Each search then works in four steps:
  1. split the query into words
  2. match each word: exactly, as the start of a longer word, or by nearest spelling
  3. keep the parts that contain all the words (set intersection)
  4. pick the best few with a heap
"""

import csv
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from edit_distance import distance_table, edit_distance
from heap import top_k
from lru_cache import LRUCache
from trie import Trie

CATALOG = Path(__file__).parent / "data" / "parts.csv"
WORD = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")  # letters and digits, and decimals such as 6.7


@dataclass(frozen=True)
class Part:
    number: str
    name: str
    category: str
    engine: str
    application: str
    price: int
    stock: int

    @property
    def text(self) -> str:
        """Everything about the part that can be searched."""
        return f"{self.name} {self.category} {self.engine} {self.application}"


def load_parts(path: Path = CATALOG) -> list[Part]:
    with open(path, newline="", encoding="utf-8") as file:
        return [
            Part(row["number"], row["name"], row["category"], row["engine"], row["application"],
                 int(row["price"]), int(row["stock"]))
            for row in csv.DictReader(file)
        ]


def tokenize(text: str) -> list[str]:
    """Split text into lower-case words. Single letters are dropped: "6.7 L" gives ["6.7"]."""
    return [word for word in WORD.findall(text.lower()) if len(word) > 1 or word.isdigit()]


def slow_search(parts: list[Part], query: str) -> list[int]:
    """The obvious way: look at every part, one by one. Kept for comparison and for the tests."""
    wanted = set(tokenize(query))
    return [position for position, part in enumerate(parts) if wanted <= set(tokenize(part.text))]


class SearchEngine:
    def __init__(self, parts: list[Part], cache_size: int = 256) -> None:
        self.parts = parts          # a part's position in this list is its id
        self.by_number = {}         # part number -> position
        self.index = {}             # word -> set of positions
        self.name_words = []        # position -> the words of that part's name
        self.trie = Trie()
        self.cache = LRUCache(cache_size)

        for position, part in enumerate(parts):
            self.by_number[part.number] = position
            self.name_words.append(set(tokenize(part.name)))
            for word in set(tokenize(part.text)):
                self.index.setdefault(word, set()).add(position)
                self.trie.insert(word)

    # ------------------------------------------------------------ autocomplete

    def suggest(self, text: str, limit: int = 6) -> list[str]:
        """Complete the word being typed: "fuel fi" gives ["fuel filter", ...]."""
        words = WORD.findall(text.lower())
        if not words or text.endswith(" "):
            return []
        *before, typing = words
        completions = sorted(self.trie.starting_with(typing))  # alphabetical, so ties come out in a fixed order
        most_common = top_k(completions, limit, key=lambda completion: completion[1])
        return [" ".join(before + [word]) for word, _ in most_common if word != typing]

    # ------------------------------------------------------------ matching one word

    def match_word(self, typed: str, still_typing: bool) -> dict:
        """Find the catalog words meant by one typed word.

        An exact match always wins. Otherwise there are two guesses: the word is
        unfinished (a prefix), or it is misspelt. The last word of a query is
        probably unfinished, so the prefix guess is tried first for it. Earlier
        words are finished, so for them the spelling guess is tried first.
        """
        if typed in self.index:
            return {"typed": typed, "kind": "exact", "words": [typed]}

        completions = sorted(word for word, _ in self.trie.starting_with(typed))
        nearest = self.nearest_word(typed)
        as_prefix = {"typed": typed, "kind": "prefix", "words": completions}
        as_typo = {"typed": typed, "kind": "corrected", "words": [nearest]}

        if still_typing:
            guesses = [(completions, as_prefix), (nearest, as_typo)]
        else:
            guesses = [(nearest, as_typo), (completions, as_prefix)]
        for found, answer in guesses:
            if found:
                return answer
        return {"typed": typed, "kind": "unknown", "words": []}

    def nearest_word(self, typed: str) -> str | None:
        """The most common catalog word within one or two typing mistakes of `typed`."""
        if typed[0].isdigit():
            return None  # never "correct" a number
        allowed = 1 if len(typed) <= 4 else 2

        best = None  # (distance, -how common, word): the smallest tuple wins
        for word, positions in self.index.items():
            if abs(len(word) - len(typed)) > allowed:
                continue  # too different in length to be within the allowed distance
            distance = edit_distance(typed, word)
            if distance <= allowed:
                candidate = (distance, -len(positions), word)
                if best is None or candidate < best:
                    best = candidate
        return best[2] if best else None

    # ------------------------------------------------------------ searching

    def search(self, query: str, limit: int = 20) -> dict:
        started = time.perf_counter()
        key = (" ".join(query.lower().split()), limit)

        result = self.cache.get(key)
        cached = result is not None
        if not cached:
            result = self._search(query, limit)
            self.cache.put(key, result)

        microseconds = round((time.perf_counter() - started) * 1_000_000)
        return {**result, "cached": cached, "microseconds": microseconds}

    def _search(self, query: str, limit: int) -> dict:
        # A part number is looked up directly in a dictionary.
        number = query.strip().upper()
        if number in self.by_number:
            part = self.parts[self.by_number[number]]
            return {"showing": number, "corrected": False, "mode": "part number", "total": 1,
                    "steps": [], "results": [asdict(part)]}

        typed_words = tokenize(query)
        last = len(typed_words) - 1
        unfinished = not query.endswith(" ")  # a space after the last word means it is complete
        steps = [self.match_word(typed, still_typing=(i == last and unfinished)) for i, typed in enumerate(typed_words)]
        for step in steps:
            step["positions"] = set().union(*(self.index[word] for word in step["words"]))
        known = [step for step in steps if step["words"]]
        if not known:
            return {"showing": query, "corrected": False, "mode": "no match", "total": 0,
                    "steps": [describe(step) for step in steps], "results": []}

        # Prefer parts that contain every word. If there are none, accept any word.
        matching = set.intersection(*(step["positions"] for step in known))
        mode = "all words"
        if not matching:
            matching = set.union(*(step["positions"] for step in known))
            mode = "any word"

        def rank(position: int) -> tuple:
            """Higher is better. Tuples are compared item by item, left to right."""
            part = self.parts[position]
            words_matched = sum(position in step["positions"] for step in known)
            in_the_name = sum(not self.name_words[position].isdisjoint(step["words"]) for step in known)
            return (words_matched, in_the_name, part.stock > 0, -len(part.name), -position)

        best = top_k(matching, limit, key=rank)
        return {
            "showing": " ".join(step["words"][0] if step["kind"] == "corrected" else step["typed"] for step in steps),
            "corrected": any(step["kind"] == "corrected" for step in steps),
            "mode": mode,
            "total": len(matching),
            "steps": [describe(step) for step in steps],
            "results": [asdict(self.parts[position]) for position in best],
        }

    def stats(self) -> dict:
        return {
            "parts": len(self.parts),
            "words": self.trie.words,
            "trie_nodes": self.trie.nodes,
            "cache_size": len(self.cache),
            "cache_hits": self.cache.hits,
            "cache_misses": self.cache.misses,
        }


def describe(step: dict) -> dict:
    """What the "How this search worked" panel shows for one typed word."""
    shown = {
        "typed": step["typed"],
        "kind": step["kind"],
        "words": step["words"][:8],
        "word_count": len(step["words"]),
        "parts": len(step.get("positions", ())),
    }
    if step["kind"] == "corrected":
        shown["table"] = distance_table(step["typed"], step["words"][0])
    return shown
