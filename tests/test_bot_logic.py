from src.bot_logic import solve_set_cover
from src.schemas import Coords


def test_solve_set_cover_all_sets_empty():
    A = Coords(0, 0)
    B = Coords(0, 1)
    universe = {A, B}
    covery_sets = {
        Coords(1, 1): set(),
        Coords(2, 2): set(),
    }
    result = solve_set_cover(covery_sets.copy(), universe)
    assert result == set()


def test_solve_set_cover_universe_empty_all_sets_empty():
    universe = set()
    covery_sets = {
        Coords(1, 1): set(),
        Coords(2, 2): set(),
    }
    result = solve_set_cover(covery_sets.copy(), universe)
    assert result == set()


def test_solve_set_cover_single_set_covers_all():
    A = Coords(0, 0)
    B = Coords(0, 1)
    C = Coords(1, 0)
    universe = {A, B, C}
    covery_sets = {
        Coords(5, 5): {A, B, C},
        Coords(6, 6): {A},
    }
    result = solve_set_cover(covery_sets.copy(), universe)
    # Only one set needed
    assert result == {Coords(5, 5)}


def test_solve_set_cover_duplicate_sets():
    A = Coords(0, 0)
    B = Coords(0, 1)
    universe = {A, B}
    covery_sets = {
        Coords(1, 1): {A, B},
        Coords(2, 2): {A, B},
    }
    result = solve_set_cover(covery_sets.copy(), universe)
    # Only one set needed, greedy may pick either
    assert len(result) == 1
    assert next(iter(result)) in covery_sets


def test_solve_set_cover_all_sets_overlap():
    A = Coords(0, 0)
    B = Coords(0, 1)
    universe = {A, B}
    covery_sets = {
        Coords(1, 1): {A, B},
        Coords(2, 2): {A, B},
        Coords(3, 3): {A, B},
    }
    result = solve_set_cover(covery_sets.copy(), universe)
    # Only one set needed
    assert len(result) == 1


def test_solve_set_cover_partial_overlap():
    A = Coords(0, 0)
    B = Coords(0, 1)
    C = Coords(1, 0)
    universe = {A, B, C}
    covery_sets = {
        Coords(1, 1): {A, B},
        Coords(2, 2): {B, C},
    }
    result = solve_set_cover(covery_sets.copy(), universe)
    # Greedy will pick both sets to cover all
    assert result == {Coords(1, 1), Coords(2, 2)}


def test_solve_set_cover_large_disjoint_sets():
    # Universe of 6 elements, each set covers 2 disjoint elements
    A = Coords(0, 0)
    B = Coords(0, 1)
    C = Coords(1, 0)
    D = Coords(1, 1)
    E = Coords(2, 0)
    F = Coords(2, 1)
    universe = {A, B, C, D, E, F}
    covery_sets = {
        Coords(10, 10): {A, B},
        Coords(20, 20): {C, D},
        Coords(30, 30): {E, F},
    }
    result = solve_set_cover(covery_sets.copy(), universe)
    # All sets needed to cover universe
    assert result == {Coords(10, 10), Coords(20, 20), Coords(30, 30)}


def test_solve_set_cover_large_overlap_sets():
    # Universe of 5 elements, sets overlap
    A = Coords(0, 0)
    B = Coords(0, 1)
    C = Coords(1, 0)
    D = Coords(1, 1)
    E = Coords(2, 0)
    universe = {A, B, C, D, E}
    covery_sets = {
        Coords(10, 10): {A, B, C},
        Coords(20, 20): {C, D, E},
        Coords(30, 30): {A, D},
    }
    result = solve_set_cover(covery_sets.copy(), universe)
    # Greedy will pick first two sets to cover all
    assert result == {Coords(10, 10), Coords(20, 20)}


def test_solve_set_cover_large_single_set():
    # Universe of 10 elements, one set covers all
    universe = {Coords(x, 0) for x in range(10)}
    covery_sets = {
        Coords(99, 99): set(universe),
        Coords(1, 1): {Coords(0, 0)},
        Coords(2, 2): {Coords(1, 0)},
    }
    result = solve_set_cover(covery_sets.copy(), universe)
    assert result == {Coords(99, 99)}


def test_solve_set_cover_large_partial_cover():
    # Universe of 8 elements, sets overlap partially
    universe = {Coords(x, 0) for x in range(8)}
    covery_sets = {
        Coords(1, 1): {Coords(0, 0), Coords(1, 0), Coords(2, 0)},
        Coords(2, 2): {Coords(2, 0), Coords(3, 0), Coords(4, 0)},
        Coords(3, 3): {Coords(4, 0), Coords(5, 0), Coords(6, 0)},
        Coords(4, 4): {Coords(6, 0), Coords(7, 0)},
    }
    result = solve_set_cover(covery_sets.copy(), universe)
    # Greedy should pick all sets to cover all elements
    assert result == {Coords(1, 1), Coords(2, 2), Coords(3, 3), Coords(4, 4)}


def test_solve_set_cover_large_no_cover_possible():
    # Universe contains elements not present in any set
    universe = {Coords(x, 0) for x in range(5)}
    covery_sets = {
        Coords(1, 1): {Coords(0, 0), Coords(1, 0)},
        Coords(2, 2): {Coords(2, 0), Coords(3, 0)},
    }
    result = solve_set_cover(covery_sets.copy(), universe)
    # Coords(4, 0) cannot be covered
    assert result == set()
