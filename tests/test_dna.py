import random
import pytest

from codon_table import ALPHABET
from dna import ANCESTOR, mutate, validate


def test_validate_accepts_valid_genome():
    assert validate('ABCDEFGHIJKL') is True
    assert validate('AAAA') is True
    assert validate(ANCESTOR) is True


def test_validate_rejects_empty_string():
    assert validate('') is False


def test_validate_rejects_out_of_alphabet():
    assert validate('ABCM') is False   # M not in alphabet
    assert validate('ABC1') is False
    assert validate('abcdef') is False  # lowercase


def test_ancestor_is_valid():
    assert validate(ANCESTOR) is True


def test_ancestor_length():
    assert len(ANCESTOR) == 29


def test_mutate_output_always_valid():
    random.seed(42)
    for _ in range(200):
        result = mutate(ANCESTOR, 0.3)
        assert validate(result), f"Invalid genome after mutation: {result!r}"


def test_mutate_output_valid_at_high_rate():
    random.seed(7)
    for _ in range(200):
        result = mutate(ANCESTOR, 2.0)
        assert validate(result), f"Invalid genome at high mutation rate: {result!r}"


def test_mutate_zero_rate_never_changes():
    for _ in range(100):
        assert mutate(ANCESTOR, 0.0) == ANCESTOR


def test_mutate_high_rate_produces_changes():
    random.seed(42)
    changed = sum(1 for _ in range(200) if mutate(ANCESTOR, 2.0) != ANCESTOR)
    assert changed > 100  # expect >50% of runs modify the genome


def test_mutate_never_produces_empty_genome():
    random.seed(99)
    g = ANCESTOR
    for _ in range(2000):
        g = mutate(g, 2.0)
    assert len(g) >= 1


def test_mutate_preserves_alphabet_on_short_genome():
    random.seed(0)
    short = 'AB'
    for _ in range(500):
        result = mutate(short, 1.0)
        assert all(c in ALPHABET for c in result)
        assert len(result) >= 1


def test_point_mutation_fires_at_expected_rate():
    # P(point mutation) = rate * 0.60; at rate=1.0 that is 60%.
    # Only length-preserving results can be checked for point mutations; concurrent
    # insertions/deletions/duplications reduce that window, so use a loose lower bound.
    random.seed(123)
    ancestor_list = list(ANCESTOR)
    changes = 0
    trials = 1000
    for _ in range(trials):
        result = list(mutate(ANCESTOR, 1.0))
        if len(result) == len(ancestor_list):
            diffs = sum(a != b for a, b in zip(ancestor_list, result))
            if diffs >= 1:
                changes += 1
    # With P(length preserved) ≈ 0.72 and P(point) = 0.60, expect ~430 but
    # concurrent length changes reduce observed count; floor at 250 for safety.
    assert changes > 250


def test_insertion_can_grow_genome():
    random.seed(5)
    grew = any(len(mutate(ANCESTOR, 2.0)) > len(ANCESTOR) for _ in range(500))
    assert grew


def test_deletion_can_shrink_genome():
    random.seed(5)
    shrank = any(len(mutate(ANCESTOR, 2.0)) < len(ANCESTOR) for _ in range(500))
    assert shrank


def test_duplication_can_significantly_grow_genome():
    random.seed(3)
    big_growth = any(len(mutate(ANCESTOR, 2.0)) > len(ANCESTOR) + 4 for _ in range(500))
    assert big_growth
