"""How much faster is the index than looking at every part?

Run:  python benchmark.py

Two ways of finding the parts that contain every word of a query are timed:
  scan   check all 20,000 parts one by one (their words are split in advance,
         so this is the scan at its best)
  index  look each word up in the dictionary and intersect the sets
"""

import time

from search import SearchEngine, load_parts, tokenize

QUERIES = ["fuel filter", "turbocharger", "oil pressure sensor", "piston ring set 6.7", "gasket generator 15"]
REPEATS = 200


def average_microseconds(function) -> float:
    started = time.perf_counter()
    for _ in range(REPEATS):
        function()
    return (time.perf_counter() - started) / REPEATS * 1_000_000


def main() -> None:
    parts = load_parts()
    engine = SearchEngine(parts)
    word_sets = [set(tokenize(part.text)) for part in parts]

    print(f"{len(parts)} parts, {engine.trie.words} different words\n")
    print(f"{'Query':24} {'Matches':>8} {'Scan':>10} {'Index':>10} {'Faster':>8}")
    total_scan = total_index = 0.0
    for query in QUERIES:
        wanted = set(tokenize(query))

        def scan():
            return [position for position, words in enumerate(word_sets) if wanted <= words]

        def index():
            return set.intersection(*(engine.index[word] for word in wanted))

        assert set(scan()) == index()  # both ways must agree
        scan_time, index_time = average_microseconds(scan), average_microseconds(index)
        total_scan += scan_time
        total_index += index_time
        print(f"{query:24} {len(index()):>8} {scan_time:>8.0f}us {index_time:>8.0f}us {scan_time / index_time:>7.0f}x")

    print(f"\nOn average the index is {total_scan / total_index:.0f} times faster than the scan.")

    # A complete search also ranks the matches and builds the answer.
    engine.cache.capacity = 0  # switch the cache off so every search does the full work
    full = sum(average_microseconds(lambda q=query: engine.search(q)) for query in QUERIES) / len(QUERIES)
    print(f"A complete search, with ranking, takes {full:.0f} microseconds on average.")


if __name__ == "__main__":
    main()
