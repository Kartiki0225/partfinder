from edit_distance import distance_table, edit_distance


def test_identical_words_are_zero_apart():
    assert edit_distance("filter", "filter") == 0


def test_each_kind_of_mistake_costs_one():
    assert edit_distance("filtr", "filter") == 1    # a letter is missing
    assert edit_distance("fuell", "fuel") == 1      # an extra letter
    assert edit_distance("gaskit", "gasket") == 1   # a wrong letter
    assert edit_distance("fule", "fuel") == 1       # two neighbours swapped


def test_several_mistakes_add_up():
    assert edit_distance("kitten", "sitting") == 3  # the textbook example
    assert edit_distance("injectr", "injector") == 1
    assert edit_distance("tubrochargr", "turbocharger") == 2


def test_distance_to_an_empty_word_is_the_length():
    assert edit_distance("", "pump") == 4
    assert edit_distance("pump", "") == 4
    assert edit_distance("", "") == 0


def test_distance_is_the_same_in_both_directions():
    assert edit_distance("alternater", "alternator") == edit_distance("alternator", "alternater")


def test_the_table_has_one_row_and_column_more_than_the_words():
    table = distance_table("fule", "fuel")
    assert len(table) == 5 and len(table[0]) == 5
    assert table[0] == [0, 1, 2, 3, 4]                   # first row: only insertions
    assert [row[0] for row in table] == [0, 1, 2, 3, 4]  # first column: only deletions
    assert table[-1][-1] == 1
