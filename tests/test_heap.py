import random

from heap import MinHeap, top_k


def test_items_come_out_smallest_first():
    heap = MinHeap()
    for number in [5, 3, 8, 1, 9, 2]:
        heap.push(number)
    assert [heap.pop() for _ in range(len(heap))] == [1, 2, 3, 5, 8, 9]


def test_peek_shows_the_smallest_without_removing_it():
    heap = MinHeap()
    heap.push(4)
    heap.push(2)
    assert heap.peek() == 2
    assert len(heap) == 2


def test_heap_sorts_a_thousand_random_numbers():
    random.seed(1)
    numbers = [random.randint(0, 10_000) for _ in range(1000)]
    heap = MinHeap()
    for number in numbers:
        heap.push(number)
    assert [heap.pop() for _ in range(1000)] == sorted(numbers)


def test_top_k_returns_the_best_first():
    assert top_k([4, 9, 1, 7, 3], 3, key=lambda n: n) == [9, 7, 4]


def test_top_k_with_fewer_items_than_k_returns_them_all():
    assert top_k([2, 5], 10, key=lambda n: n) == [5, 2]


def test_top_k_uses_the_key_not_the_item():
    words = ["oil", "turbocharger", "pump"]
    assert top_k(words, 2, key=len) == ["turbocharger", "pump"]


def test_top_k_keeps_the_earlier_item_when_keys_are_equal():
    assert top_k(["aa", "bb", "cc"], 2, key=len) == ["aa", "bb"]


def test_top_k_agrees_with_sorting_everything():
    random.seed(2)
    numbers = [random.random() for _ in range(500)]
    assert top_k(numbers, 20, key=lambda n: n) == sorted(numbers, reverse=True)[:20]
