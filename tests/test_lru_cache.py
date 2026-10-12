from lru_cache import LRUCache


def test_a_stored_value_can_be_read_back():
    cache = LRUCache(2)
    cache.put("fuel", 1)
    assert cache.get("fuel") == 1


def test_a_missing_key_gives_none():
    assert LRUCache(2).get("nothing") is None


def test_the_least_recently_used_entry_is_thrown_out_when_full():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)          # "a" is the oldest, so it goes
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3
    assert len(cache) == 2


def test_reading_an_entry_protects_it_from_being_thrown_out():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")             # "a" is now the most recent, "b" the oldest
    cache.put("c", 3)
    assert cache.get("a") == 1
    assert cache.get("b") is None


def test_putting_an_existing_key_updates_it_without_growing():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("a", 99)
    assert cache.get("a") == 99
    assert len(cache) == 1


def test_hits_and_misses_are_counted():
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.get("a")
    cache.get("a")
    cache.get("zzz")
    assert (cache.hits, cache.misses) == (2, 1)


def test_a_long_run_never_exceeds_the_capacity():
    cache = LRUCache(50)
    for number in range(1000):
        cache.put(number, number * 2)
    assert len(cache) == 50
    assert cache.get(999) == 1998      # the newest is still there
    assert cache.get(949) is None      # just outside the last 50
