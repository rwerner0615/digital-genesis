"""
Pytest tests covering the 9 spec rules for DigitalGenesis.
Cell._next_id is reset to 0 before every test by the autouse fixture in conftest.py.
"""
import random
import pytest

from genome import Genome, Gene, GENE_TYPES
from cell import Cell
from world import World


# ---------------------------------------------------------------------------
# Rule 1 – Mutation produces valid genomes
# ---------------------------------------------------------------------------

def test_mutation_no_negative_values():
    """Every gene value must be >= 0 after any number of mutations."""
    random.seed(42)
    genome = Genome([Gene('SIZE', 1.0), Gene('METABOLISM', 1.0), Gene('MUTATION_RATE', 0.9)])
    for _ in range(10_000):
        mutated = genome.mutate()
        for g in mutated.genes:
            assert g.value >= 0.0, f"Negative value {g.value} for gene {g.type}"


def test_mutation_never_empty_genome():
    """A genome must always have at least one gene after mutation."""
    random.seed(42)
    genome = Genome([Gene('SIZE', 1.0), Gene('MUTATION_RATE', 0.9)])
    for _ in range(10_000):
        genome = genome.mutate()
        assert len(genome.genes) >= 1


def test_mutation_single_gene_genome_stays_nonempty():
    """Delete is blocked when len == 1; a single-gene genome must never shrink to 0."""
    random.seed(123)
    genome = Genome([Gene('METABOLISM', 2.0)])
    for _ in range(10_000):
        mutated = genome.mutate()
        assert len(mutated.genes) >= 1


# ---------------------------------------------------------------------------
# Rule 2 – Reproduction halves parent energy correctly
# ---------------------------------------------------------------------------

def test_reproduction_halves_parent_energy():
    genome = Genome([Gene('SIZE', 1.0), Gene('REPRODUCTION_THRESHOLD', 200.0)])
    cell = Cell((10, 10), genome)
    cell.energy = 80.0

    child = cell._reproduce()

    assert cell.energy == pytest.approx(40.0)
    assert child.energy == pytest.approx(40.0)


def test_reproduction_child_gets_equal_halved_share():
    genome = Genome([Gene('SIZE', 1.0), Gene('REPRODUCTION_THRESHOLD', 200.0)])
    cell = Cell((50, 50), genome)
    cell.energy = 120.0

    child = cell._reproduce()

    assert cell.energy == pytest.approx(child.energy)
    assert cell.energy == pytest.approx(60.0)


# ---------------------------------------------------------------------------
# Rule 3 – Eating transfers exactly 70 % of prey's energy to the predator
# ---------------------------------------------------------------------------

def test_eating_transfers_70_percent_of_prey_energy():
    world = World(seed=42)

    # Predator at (10, 10); MOTILITY omitted → 0, no movement
    predator = Cell((10, 10), Genome([
        Gene('SIZE', 1.0),
        Gene('DIET_CELL', 1.0),
        Gene('OFFENSE', 2.0),
        Gene('REPRODUCTION_THRESHOLD', 200.0),
    ]))
    predator.energy = 50.0
    pred_energy_before = predator.energy

    # Prey adjacent at (11, 10); no DEFENSE gene → defense = 0
    prey = Cell((11, 10), Genome([Gene('REPRODUCTION_THRESHOLD', 200.0)]))
    prey.energy = 40.0
    prey_energy = prey.energy

    # SIZE=1, MOTILITY=0 → upkeep = 0.1*1 + 0.05*0 = 0.1
    upkeep = 0.1 * 1.0

    predator.tick(world, [predator, prey])

    assert not prey.alive
    assert predator.energy == pytest.approx(pred_energy_before - upkeep + prey_energy * 0.7)


# ---------------------------------------------------------------------------
# Rule 4 – Cell at energy 0 dies on next tick
# ---------------------------------------------------------------------------

def test_zero_energy_cell_dies_on_tick():
    world = World(seed=42)
    # No diet genes → no energy gain; MOTILITY omitted → no movement
    cell = Cell((10, 10), Genome([
        Gene('SIZE', 1.0),
        Gene('REPRODUCTION_THRESHOLD', 200.0),
    ]))
    cell.energy = 0.0

    cell.tick(world, [cell])

    assert not cell.alive


def test_positive_energy_cell_survives_tick():
    world = World(seed=42)
    cell = Cell((10, 10), Genome([
        Gene('SIZE', 0.1),
        Gene('METABOLISM', 5.0),
        Gene('DIET_NUTRIENT', 1.0),
        Gene('REPRODUCTION_THRESHOLD', 200.0),
    ]))
    cell.energy = 100.0

    cell.tick(world, [cell])

    assert cell.alive


# ---------------------------------------------------------------------------
# Rule 5 – Sim with 0 cells produces 0 cells (no spontaneous generation)
# ---------------------------------------------------------------------------

def test_empty_sim_stays_empty():
    world = World(seed=42)
    cells = []

    for _ in range(20):
        world.tick()
        random.shuffle(cells)
        new_children = []
        for cell in cells:
            if cell.alive:
                child = cell.tick(world, cells)
                if child is not None:
                    new_children.append(child)
        cells = [c for c in cells if c.alive] + new_children

    assert cells == []


# ---------------------------------------------------------------------------
# Rule 6 (CRITICAL) – Predation emerges from a pure DIET_NUTRIENT ancestor
# ---------------------------------------------------------------------------

def test_predation_emerges_from_nutrient_only_ancestor():
    """
    Core project claim: predation (DIET_CELL > 0) must be reachable from a
    nutrient-only ancestor through valid mutation chains — no injection, just
    the gene-add mutation firing on DIET_CELL by chance.

    Start a fully seeded deterministic sim with one ancestor whose DIET_CELL==0
    and assert that within MAX_TICKS ticks at least one descendant gains DIET_CELL>0.
    """
    random.seed(42)
    Cell._next_id = 0

    ancestor_genes = [
        Gene('SIZE', 1.0),
        Gene('METABOLISM', 1.0),
        Gene('MOTILITY', 1.0),
        Gene('SENSE_RANGE', 1.0),
        Gene('DIET_NUTRIENT', 1.0),
        Gene('MUTATION_RATE', 0.3),
        Gene('REPRODUCTION_THRESHOLD', 50.0),
    ]
    start_genome = Genome(ancestor_genes)
    assert start_genome.get_trait('DIET_CELL') == 0.0, "Ancestor must not have DIET_CELL"

    world = World(seed=42)
    cells = [Cell((100, 100), Genome([Gene(g.type, g.value) for g in ancestor_genes]))]

    MAX_TICKS = 3000
    MAX_POP = 500  # cap to keep runtime bounded

    for tick in range(MAX_TICKS):
        world.tick()
        random.shuffle(cells)

        new_children = []
        for cell in cells:
            if cell.alive:
                child = cell.tick(world, cells)
                if child is not None:
                    new_children.append(child)

        cells = [c for c in cells if c.alive] + new_children

        if len(cells) > MAX_POP:
            cells = random.sample(cells, MAX_POP)

        if not cells:
            pytest.fail(f"Population went extinct at tick {tick + 1}")

        if any(c.genome.get_trait('DIET_CELL') > 0 for c in cells):
            return  # predation emerged — test passes

    pytest.fail(
        f"No predator emerged after {MAX_TICKS} ticks — "
        "predation cannot evolve from a pure nutrient-eating ancestor"
    )


# ---------------------------------------------------------------------------
# Rule 7 – Genome length CAN increase via gene-add and duplicate mutations
# ---------------------------------------------------------------------------

def test_genome_length_can_increase():
    random.seed(0)
    base = Genome([Gene('SIZE', 1.0), Gene('MUTATION_RATE', 0.5)])
    initial_len = len(base)

    for _ in range(500):
        if len(base.mutate()) > initial_len:
            return  # pass

    pytest.fail("Genome length never increased via gene-add or duplicate in 500 mutations")


# ---------------------------------------------------------------------------
# Rule 8 – Genome length CAN decrease via delete mutations
# ---------------------------------------------------------------------------

def test_genome_length_can_decrease():
    random.seed(0)
    # Need >= 2 genes so the delete branch (len > 1 guard) is reachable
    base = Genome([Gene('SIZE', 1.0), Gene('METABOLISM', 1.0), Gene('MUTATION_RATE', 0.5)])
    initial_len = len(base)

    for _ in range(500):
        if len(base.mutate()) < initial_len:
            return  # pass

    pytest.fail("Genome length never decreased via delete mutation in 500 mutations")


# ---------------------------------------------------------------------------
# Rule 9 – MUTATION_RATE floor of 0.1 applies even with no MUTATION_RATE genes
# ---------------------------------------------------------------------------

def test_mutation_rate_floor_with_no_mr_genes():
    """
    A cell whose genome has no MUTATION_RATE genes has get_trait==0.0,
    but the code applies a floor of 0.1.  Verify mutations still occur.
    """
    random.seed(0)
    base = Genome([Gene('SIZE', 1.0)])
    assert base.get_trait('MUTATION_RATE') == 0.0

    for _ in range(500):
        result = base.mutate()
        # A length change is unambiguous proof of mutation; a value change is equally valid.
        if (len(result) != len(base) or
                result.genes[0].value != base.genes[0].value):
            return  # floor is effective

    pytest.fail(
        "No mutations in 500 iterations with MUTATION_RATE=0 — "
        "the 0.1 floor is not being applied"
    )
