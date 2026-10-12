import pytest

from search import Part, SearchEngine, load_parts, slow_search, tokenize

SMALL_CATALOG = [
    Part("PF-1", "Fuel Filter", "Filtration", "6.7 L", "Truck", 900, 12),
    Part("PF-2", "Fuel Filter Kit", "Filtration", "6.7 L", "Bus", 1500, 0),
    Part("PF-3", "Oil Filter", "Filtration", "8.9 L", "Truck", 700, 40),
    Part("PF-4", "Fuel Pump", "Fuel System", "6.7 L", "Generator", 21000, 3),
    Part("PF-5", "Turbocharger", "Air Handling", "15 L", "Truck", 88000, 2),
    Part("PF-6", "Oil Pressure Sensor", "Lubrication", "8.9 L", "Marine", 2400, 9),
    Part("PF-7", "Injector Nozzle", "Fuel System", "6.7 L", "Truck", 5200, 30),
    Part("PF-8", "Alternator", "Electrical", "15 L", "Bus", 26000, 5),
]


@pytest.fixture
def engine():
    return SearchEngine(SMALL_CATALOG)


def numbers(result):
    return [part["number"] for part in result["results"]]


def test_tokenize_lowers_case_keeps_decimals_and_drops_single_letters():
    assert tokenize("Fuel Filter, 6.7 L (Truck)") == ["fuel", "filter", "6.7", "truck"]


def test_every_word_must_match(engine):
    result = engine.search("fuel filter")
    assert sorted(numbers(result)) == ["PF-1", "PF-2"]
    assert result["mode"] == "all words"


def test_words_can_come_from_any_field(engine):
    assert numbers(engine.search("filter truck 8.9")) == ["PF-3"]


def test_a_misspelt_word_is_corrected(engine):
    result = engine.search("fule filter")
    assert result["corrected"] is True
    assert result["showing"] == "fuel filter"
    assert sorted(numbers(result)) == ["PF-1", "PF-2"]


def test_swapped_letters_in_a_long_word_are_corrected(engine):
    assert numbers(engine.search("tubrocharger")) == ["PF-5"]


def test_the_last_word_may_be_unfinished(engine):
    result = engine.search("oil pres")
    assert numbers(result) == ["PF-6"]
    assert [step["kind"] for step in result["steps"]] == ["exact", "prefix"]


def test_a_finished_word_is_treated_as_a_typo_before_a_prefix(engine):
    # "filtr" could start "filtration", but it is not the last word, so "filter" is tried first.
    result = engine.search("filtr truck")
    assert result["steps"][0]["kind"] == "corrected"
    assert result["steps"][0]["words"] == ["filter"]


def test_a_part_number_is_found_whatever_the_case(engine):
    for query in ("PF-5", "pf-5", "  Pf-5 "):
        result = engine.search(query)
        assert result["mode"] == "part number"
        assert numbers(result) == ["PF-5"]


def test_numbers_are_never_spell_corrected(engine):
    assert engine.search("6.8")["total"] == 0


def test_when_no_part_has_every_word_any_word_is_accepted(engine):
    result = engine.search("turbocharger alternator")
    assert result["mode"] == "any word"
    assert sorted(numbers(result)) == ["PF-5", "PF-8"]


def test_an_unknown_word_is_ignored_if_the_others_match(engine):
    result = engine.search("zzzzzz alternator")
    assert numbers(result) == ["PF-8"]
    assert result["steps"][0]["kind"] == "unknown"


def test_nothing_matches_a_query_of_unknown_words(engine):
    result = engine.search("zzzzzz qqqqqq")
    assert result["total"] == 0 and result["results"] == []


def test_parts_in_stock_come_before_parts_out_of_stock(engine):
    assert numbers(engine.search("fuel filter")) == ["PF-1", "PF-2"]  # PF-2 has no stock


def test_a_word_in_the_name_beats_the_same_word_in_the_category(engine):
    # "fuel" is in the name of PF-1, PF-2 and PF-4, but only in the category of PF-7.
    assert numbers(engine.search("fuel"))[-1] == "PF-7"


def test_limit_cuts_the_list_but_not_the_total(engine):
    result = engine.search("truck", limit=2)
    assert len(result["results"]) == 2
    assert result["total"] == 4


def test_suggestions_complete_the_word_being_typed(engine):
    assert engine.suggest("fuel fi") == ["fuel filter", "fuel filtration"]
    assert engine.suggest("tur") == ["turbocharger"]
    assert engine.suggest("fuel ") == []      # nothing is being typed after the space
    assert engine.suggest("") == []


def test_suggestions_put_the_most_common_word_first(engine):
    # "fuel" appears in four parts, more than any other word starting with "f".
    assert engine.suggest("f")[0] == "fuel"


def test_a_repeated_search_is_answered_from_the_cache(engine):
    first = engine.search("oil filter")
    second = engine.search("  OIL   filter")   # the same query after tidying
    assert first["cached"] is False
    assert second["cached"] is True
    assert numbers(first) == numbers(second)


# ---------------------------------------------------------------- the full catalog

@pytest.fixture(scope="module")
def full():
    parts = load_parts()
    return parts, SearchEngine(parts)


@pytest.mark.parametrize("query", ["fuel filter", "turbocharger", "oil pressure sensor 8.9", "gasket generator 15", "premium bus"])
def test_the_index_finds_exactly_what_a_full_scan_finds(full, query):
    parts, engine = full
    expected = slow_search(parts, query)
    result = engine.search(query + " ", limit=len(parts))  # the space marks the last word as finished
    assert result["total"] == len(expected)
    assert sorted(part["number"] for part in result["results"]) == sorted(parts[i].number for i in expected)


def test_the_catalog_has_twenty_thousand_unique_part_numbers(full):
    parts, engine = full
    assert len(parts) == 20_000
    assert len(engine.by_number) == 20_000


def test_common_typos_reach_the_right_word(full):
    _, engine = full
    typos = {"fule": "fuel", "filtr": "filter", "tubrocharger": "turbocharger", "injecter": "injector",
             "gaskit": "gasket", "alternater": "alternator", "radiater": "radiator", "pistn": "piston"}
    for typed, meant in typos.items():
        assert engine.nearest_word(typed) == meant
