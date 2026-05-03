import random
import argparse

from world import World, GRID_SIZE, HARD_POPULATION_CAP
from dna import ANCESTOR, mutate
from cell import Cell, build_cell_index


def run(seed: int = 42, max_ticks: int = 1000, print_interval: int = 50) -> list:
    random.seed(seed)
    Cell._next_id = 0

    world = World(seed=seed)
    ancestor = Cell((100, 100), ANCESTOR)
    cells = [ancestor]
    all_lineage_ids: set = {ancestor.lineage_id}

    print(f"seed={seed}  max_ticks={max_ticks}")
    print(f"ancestor dna ({len(ANCESTOR)} letters): {ANCESTOR}")
    print()
    _print_header()
    _print_stats(0, cells, all_lineage_ids)

    for tick in range(1, max_ticks + 1):
        world.tick(len(cells))

        # Build spatial index once per tick, shared by all cell.tick() calls
        cell_index = build_cell_index(cells)
        random.shuffle(cells)

        new_children: list = []
        for cell in cells:
            if cell.alive:
                new_children.extend(cell.tick(world, cell_index))

        cells = [c for c in cells if c.alive] + new_children

        for c in new_children:
            all_lineage_ids.add(c.lineage_id)

        # Population guardian: near-extinction → clone survivors with mutation
        if 0 < len(cells) < 5:
            cells = _population_guardian(cells)
            for c in cells:
                all_lineage_ids.add(c.lineage_id)

        if not cells:
            print(f"EXTINCTION at tick {tick}")
            return cells

        if len(cells) > HARD_POPULATION_CAP:
            random.shuffle(cells)
            cells = cells[:HARD_POPULATION_CAP]

        if tick == 1 or tick % print_interval == 0:
            _print_stats(tick, cells, all_lineage_ids)

    print()
    print("=== final state ===")
    _print_stats(max_ticks, cells, all_lineage_ids)
    return cells


def _population_guardian(cells: list) -> list:
    target = 10
    added = []
    while len(cells) + len(added) < target:
        src = random.choice(cells)
        child_dna = mutate(src.dna, src.phenotype.stats['mutation_rate'])
        pos = (
            (src.position[0] + random.randint(-3, 3)) % GRID_SIZE,
            (src.position[1] + random.randint(-3, 3)) % GRID_SIZE,
        )
        child = Cell(pos, child_dna, parent_id=src.id)
        child.energy = max(30.0, src.energy * 0.7)

        src_bp = frozenset(src.phenotype.body_parts.keys())
        child_bp = frozenset(child.phenotype.body_parts.keys())
        if child_bp == src_bp and child.phenotype.behaviors == src.phenotype.behaviors:
            child.lineage_id = src.lineage_id

        added.append(child)
    return cells + added


def _print_header():
    print(f"{'tick':>6}  {'pop':>5}  {'live/ever':>10}  {'predators':>9}  "
          f"{'avg_dna':>7}  {'avg_energy':>10}")
    print("-" * 60)


def _print_stats(tick: int, cells: list, all_lineage_ids: set):
    n = len(cells)
    live_lineages = len(set(c.lineage_id for c in cells))
    ever_lineages = len(all_lineage_ids)
    predators = sum(1 for c in cells if c.phenotype.stats['cell_eat'] > 0)
    avg_dna = sum(len(c.dna) for c in cells) / n
    avg_energy = sum(c.energy for c in cells) / n
    print(f"{tick:>6}  {n:>5}  {live_lineages:>4}/{ever_lineages:<5}  "
          f"{predators:>9}  {avg_dna:>7.1f}  {avg_energy:>10.1f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DigitalGenesis v2 headless')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--ticks', type=int, default=1000)
    parser.add_argument('--interval', type=int, default=50)
    args = parser.parse_args()
    run(seed=args.seed, max_ticks=args.ticks, print_interval=args.interval)
