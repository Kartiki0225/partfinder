"""Edit distance: how many typing mistakes separate two words.

One mistake is one of:
    insert a letter        filtr  -> filter
    delete a letter        fuell  -> fuel
    replace a letter       gaskit -> gasket
    swap two neighbours    fule   -> fuel

It is solved with dynamic programming. table[i][j] is the distance between the
first i letters of `typed` and the first j letters of `word`. Each cell is
worked out from cells that are already filled in, so no work is ever repeated.
"""


def distance_table(typed: str, word: str) -> list[list[int]]:
    rows, cols = len(typed) + 1, len(word) + 1
    table = [[0] * cols for _ in range(rows)]

    # Turning the first i letters into nothing takes i deletions, and
    # turning nothing into the first j letters takes j insertions.
    for i in range(rows):
        table[i][0] = i
    for j in range(cols):
        table[0][j] = j

    for i in range(1, rows):
        for j in range(1, cols):
            same = typed[i - 1] == word[j - 1]
            table[i][j] = min(
                table[i - 1][j] + 1,                        # delete a letter
                table[i][j - 1] + 1,                        # insert a letter
                table[i - 1][j - 1] + (0 if same else 1),   # keep or replace a letter
            )
            swapped = i > 1 and j > 1 and typed[i - 1] == word[j - 2] and typed[i - 2] == word[j - 1]
            if swapped:
                table[i][j] = min(table[i][j], table[i - 2][j - 2] + 1)  # swap two neighbours
    return table


def edit_distance(typed: str, word: str) -> int:
    """The answer is the bottom-right cell: all of `typed` against all of `word`."""
    return distance_table(typed, word)[-1][-1]
