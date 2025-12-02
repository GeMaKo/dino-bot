from src.graph import find_dead_ends_and_rooms
from src.schemas import Coords


def test_find_dead_ends_and_rooms_single_dead_end():
    """
    Test case: Single dead end

    Grid layout:
    0 - 1 - 2

    Dead ends: (0, 0), (2, 0)
    """
    graph = {
        Coords(0, 0): {Coords(1, 0)},
        Coords(1, 0): {Coords(0, 0), Coords(2, 0)},
        Coords(2, 0): {Coords(1, 0)},
    }
    result = find_dead_ends_and_rooms(graph)
    assert result == {Coords(0, 0), Coords(2, 0)}


def test_find_dead_ends_and_rooms_no_dead_ends():
    """
    Test case: No dead ends

    Grid layout:
    0 - 1 - 2 - 3

    Dead ends: None
    """
    graph = {
        Coords(0, 0): {Coords(1, 0)},
        Coords(1, 0): {Coords(0, 0), Coords(2, 0)},
        Coords(2, 0): {Coords(1, 0), Coords(3, 0)},
        Coords(3, 0): {Coords(2, 0)},
    }
    result = find_dead_ends_and_rooms(graph)
    assert result == {Coords(0, 0), Coords(3, 0)}


def test_find_dead_ends_and_rooms_multiple_dead_ends():
    """
    Test case: Multiple dead ends

    Grid layout:
        1
        |
    0 - 1 - 2 - 3

    Dead ends: (0, 0), (3, 0), (1, 1)
    """
    graph = {
        Coords(0, 0): {Coords(1, 0)},
        Coords(1, 0): {Coords(0, 0), Coords(2, 0), Coords(1, 1)},
        Coords(2, 0): {Coords(1, 0), Coords(3, 0)},
        Coords(3, 0): {Coords(2, 0)},
        Coords(1, 1): {Coords(1, 0)},
    }
    result = find_dead_ends_and_rooms(graph)
    assert result == {Coords(0, 0), Coords(3, 0), Coords(1, 1)}


def test_find_dead_ends_and_rooms_disconnected_graph():
    """
    Test case: Disconnected graph

    Grid layout:
    0 - 1    2 - 3

    Dead ends: (0, 0), (1, 0), (2, 2), (3, 2)
    """
    graph = {
        Coords(0, 0): {Coords(1, 0)},
        Coords(1, 0): {Coords(0, 0)},
        Coords(2, 2): {Coords(3, 2)},
        Coords(3, 2): {Coords(2, 2)},
    }
    result = find_dead_ends_and_rooms(graph)
    assert result == {Coords(0, 0), Coords(1, 0), Coords(2, 2), Coords(3, 2)}


def test_find_dead_ends_and_rooms_complex_graph():
    """
    Test case: Complex graph

    Grid layout:
        1 - 2
        |
    0 - 1
        |
        1

    Dead ends: (0, 0), (2, 0), (1, 2)
    """
    graph = {
        Coords(0, 0): {Coords(1, 0)},
        Coords(1, 0): {Coords(0, 0), Coords(2, 0), Coords(1, 1)},
        Coords(2, 0): {Coords(1, 0)},
        Coords(1, 1): {Coords(1, 0), Coords(1, 2)},
        Coords(1, 2): {Coords(1, 1)},
    }
    result = find_dead_ends_and_rooms(graph)
    assert result == {Coords(0, 0), Coords(2, 0), Coords(1, 2)}
