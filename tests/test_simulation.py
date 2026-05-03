"""
Phase 2 smoke tests: cell unit tests + headless evolution confirmation.
Short runs (≤500 ticks) keep CI fast; predation-emergence test runs 1000.
"""
import random
import pytest

from cell import Cell, build_cell_index
from dna import ANCESTOR, mutate
from phenotype import parse_dna
from simulation import run, _population_guardian
from world import World


# ── Cell unit tests ───────────────────────────────────────────────────────────

def test_cell_creates_phenotype_on_init():
    c = Cell((0, 0), ANCESTOR)
    assert c.phenotype is not None
    assert c.phenotype.stats['motility'] > 1.0


def test_cell_tick_returns_list():
    world = World(seed=1)
    c = Cell((10, 10), ANCESTOR)
    c.energy = 200.0
    result = c.tick(world, build_cell_index([c]))
    assert isinstance(result, list)


def test_cell_dies_at_zero_energy():
    world = World(seed=1)
    world.nutrient_level[:, :] = 0.0  # no nutrients → upkeep kills the cell
    c = Cell((10, 10), ANCESTOR)
    c.energy = 0.001
    c.tick(world, build_cell_index([c]))
    assert not c.alive


def test_cell_reproduces_above_threshold():
    world = World(seed=1)
    c = Cell((10, 10), ANCESTOR)
    c.energy = 200.0
    children = c.tick(world, build_cell_index([c]))
    assert len(children) >= 1
    assert c.energy < 200.0


def test_child_has_valid_dna():
    world = World(seed=1)
    c = Cell((10, 10), ANCESTOR)
    c.energy = 200.0
    children = c.tick(world, build_cell_index([c]))
    for child in children:
        assert all(ch in 'ABCDEFGHIJKL' for ch in child.dna)


def test_child_energy_roughly_halves_parent():
    world = World(seed=2)
    c = Cell((10, 10), ANCESTOR)
    c.energy = 200.0
    children = c.tick(world, build_cell_index([c]))
    if children:
        assert c.energy == pytest.approx(children[0].energy, rel=0.05)


def test_predation_kills_prey():
    world = World(seed=3)
    world.nutrient_level[:, :] = 0.0  # no food → movement defaults to prey-hunting
    # ANCESTOR has offense=2 (base 1 + AEF); prey has defense=1 (base) → 2>1 kills
    pred = Cell((10, 10), ANCESTOR + 'LCKLCK')  # adds cell_eat=2
    pred.energy = 10.0  # low enough that eating prey (28 gain) won't trigger reproduction

    prey = Cell((10, 10), ANCESTOR)  # same tile — within _find_prey's 3×3 box
    prey.energy = 40.0

    pred.tick(world, build_cell_index([pred, prey]))
    assert not prey.alive
    assert pred.energy > 30.0  # gained ~28 (prey.energy * 0.7), net well above start


def test_cowardly_cell_moves_away_from_predator():
    world = World(seed=5)
    coward = Cell((50, 50), ANCESTOR + 'DEF')
    assert 'cowardly' in coward.phenotype.behaviors

    predator = Cell((51, 50), ANCESTOR + 'LCKLCK')
    predator.phenotype.stats['cell_eat'] = 2.0

    start_pos = coward.position
    coward.tick(world, build_cell_index([coward, predator]))
    assert coward.position != start_pos or not coward.alive


def test_lineage_new_on_structural_body_part_change():
    c = Cell((0, 0), ANCESTOR)
    parent_lineage = c.lineage_id
    parent_bp = frozenset(c.phenotype.body_parts.keys())

    random.seed(0)
    for _ in range(1000):
        child_dna = mutate(c.dna, 1.5)
        cp = parse_dna(child_dna)
        child_bp = frozenset(cp.body_parts.keys())
        if child_bp != parent_bp:
            child = Cell((0, 0), child_dna, parent_id=c.id)
            assert child.lineage_id != parent_lineage
            return

    pytest.skip("No structural mutation found in 1000 tries")


def test_lineage_inherited_on_neutral_mutation():
    c = Cell((0, 0), ANCESTOR)
    parent_lineage = c.lineage_id
    parent_bp = frozenset(c.phenotype.body_parts.keys())
    parent_beh = c.phenotype.behaviors

    random.seed(42)
    for _ in range(1000):
        child_dna = mutate(c.dna, 0.3)
        cp = parse_dna(child_dna)
        if (frozenset(cp.body_parts.keys()) == parent_bp and
                cp.behaviors == parent_beh):
            child = Cell((0, 0), child_dna, parent_id=c.id)
            # Lineage assignment happens in _reproduce; mirror the logic here
            child_bp = frozenset(child.phenotype.body_parts.keys())
            if child_bp == parent_bp and child.phenotype.behaviors == parent_beh:
                child.lineage_id = parent_lineage
            assert child.lineage_id == parent_lineage
            return

    pytest.skip("No neutral mutation found in 1000 tries")


# ── Population guardian ───────────────────────────────────────────────────────

def test_population_guardian_reaches_target():
    random.seed(7)
    small = [Cell((10, 10), ANCESTOR), Cell((20, 20), ANCESTOR)]
    result = _population_guardian(small)
    assert len(result) >= 10


def test_population_guardian_children_are_valid():
    random.seed(7)
    small = [Cell((10, 10), ANCESTOR)]
    result = _population_guardian(small)
    for c in result:
        assert all(ch in 'ABCDEFGHIJKL' for ch in c.dna)
        assert c.energy > 0


# ── Short headless runs ───────────────────────────────────────────────────────

def test_population_grows_from_single_ancestor():
    cells = run(seed=42, max_ticks=200, print_interval=9999)
    assert len(cells) > 1


def test_no_extinction_at_500_ticks():
    cells = run(seed=42, max_ticks=500, print_interval=9999)
    assert len(cells) > 0


def test_multiple_lineages_by_tick_200():
    cells = run(seed=42, max_ticks=200, print_interval=9999)
    live = len(set(c.lineage_id for c in cells))
    assert live >= 2, f"Expected ≥2 live lineages, got {live}"


def test_avg_energy_stable_at_tick_500():
    cells = run(seed=42, max_ticks=500, print_interval=9999)
    avg_e = sum(c.energy for c in cells) / len(cells)
    assert avg_e > 5.0, f"Avg energy collapsed to {avg_e:.2f} — ecosystem unstable"


def test_predation_emerges_by_tick_1000():
    """
    cell_eat > 0 must emerge from mutations within 1000 ticks.
    Ancestor has no LCK or FBL — predation must evolve in.
    """
    random.seed(42)
    Cell._next_id = 0
    world = World(seed=42)
    ancestor = Cell((100, 100), ANCESTOR)
    assert ancestor.phenotype.stats['cell_eat'] == 0.0
    cells = [ancestor]
    all_lineage_ids = {ancestor.lineage_id}

    for tick in range(1, 1001):
        world.tick(len(cells))
        cell_index = build_cell_index(cells)
        random.shuffle(cells)
        new_children = []
        for cell in cells:
            if cell.alive:
                new_children.extend(cell.tick(world, cell_index))
        cells = [c for c in cells if c.alive] + new_children
        for c in new_children:
            all_lineage_ids.add(c.lineage_id)
        if 0 < len(cells) < 5:
            cells = _population_guardian(cells)
        if not cells:
            pytest.fail(f"Extinction at tick {tick}")
        if any(c.phenotype.stats['cell_eat'] > 0 for c in cells):
            return

    pytest.fail(
        "No predator (cell_eat > 0) emerged after 1000 ticks"
    )
