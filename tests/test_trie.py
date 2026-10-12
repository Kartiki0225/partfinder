from trie import Trie


def build(*words):
    trie = Trie()
    for word in words:
        trie.insert(word)
    return trie


def test_a_stored_word_is_found_and_others_are_not():
    trie = build("fuel", "filter")
    assert "fuel" in trie
    assert "fue" not in trie       # only the start of a word
    assert "fuels" not in trie     # longer than any stored word
    assert "pump" not in trie


def test_inserting_a_word_again_raises_its_count():
    trie = build("filter", "filter", "filter", "fuel")
    assert trie.count("filter") == 3
    assert trie.count("fuel") == 1
    assert trie.count("oil") == 0
    assert trie.words == 2


def test_starting_with_returns_every_word_under_the_prefix():
    trie = build("filter", "filtration", "fan", "fuel", "pump")
    assert dict(trie.starting_with("fi")) == {"filter": 1, "filtration": 1}


def test_a_word_is_a_prefix_of_itself():
    trie = build("fan", "fanbelt")
    assert sorted(word for word, _ in trie.starting_with("fan")) == ["fan", "fanbelt"]


def test_an_unknown_prefix_gives_nothing():
    assert build("fuel").starting_with("x") == []


def test_the_empty_prefix_gives_every_word():
    trie = build("oil", "pump", "seal")
    assert sorted(word for word, _ in trie.starting_with("")) == ["oil", "pump", "seal"]


def test_words_with_the_same_start_share_nodes():
    # "filter" needs 6 nodes. "filtration" shares f-i-l-t and adds 6 more. Plus the root.
    trie = build("filter", "filtration")
    assert trie.nodes == 1 + 6 + 6
