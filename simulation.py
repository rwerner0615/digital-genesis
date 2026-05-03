import random
import argparse
from world import World
from genome import Genome, Gene
from cell import Cell

ANCESTOR_GENOME = Genome([
    Gene('SIZE', 1.0),
    Gene('METABOLISM', 1.0),
    Gene('MOTILITY', 1.0),
    Gene('SENSE_RANGE', 1.0),
    Gene('DIET_NUTRIENT', 1.0),
    Gene('MUTATION_RATE', 0.3),
    Gene('REPRODUCTION_THRESHOLD', 50.0),
])


def run(seed: int = 42, max_ticks: int = 1000, print_interval: int = 50) -> list:
    random.seed(seed)
    Cell._next_id = 0

    world = World(seed=seed)
    ancestor = Cell((100, 100), Genome([Gene(g.type, g.value) for g in ANCESTOR_GENOME.genes]))
    cells = [ancestor]

    print(f"seed={seed}  max_ticks={max_ticks}")
    print(f"ancestor: {ancestor.genome}")
    print()
    print(f"{'tick':>6}  {'pop':>6}  {'lineages':>8}  {'avg_genes':>9}  "
          f"{'avg_energy':>10}  {'predators':>9}  {'mut_rate':>8}")
    print("-" * 72)

    for tick in range(1, max_ticks + 1):
        world.tick(len(cells))
        random.shuffle(cells)

        new_children = []
        for cell in cells:
            if cell.alive:
                child = cell.tick(world, cells)
                if child is not None:
                    new_children.append(child)

        cells = [c for c in cells if c.alive] + new_children

        if not cells:
            print(f"EXTINCTION at tick {tick}")
            return cells

        if tick == 1 or tick % print_interval == 0:
            _print_stats(tick, cells)

    print()
    print("=== final state ===")
    _print_stats(max_ticks, cells)
    return cells


def _print_stats(tick: int, cells: list):
    n = len(cells)
    avg_genes = sum(len(c.genome) for c in cells) / n
    avg_energy = sum(c.energy for c in cells) / n
    predators = sum(1 for c in cells if c.genome.get_trait('DIET_CELL') > 0)
    lineages = len(set(c.lineage_id for c in cells))
    avg_mr = sum(c.genome.get_trait('MUTATION_RATE') for c in cells) / n
    print(f"{tick:>6}  {n:>6}  {lineages:>8}  {avg_genes:>9.2f}  "
          f"{avg_energy:>10.1f}  {predators:>9}  {avg_mr:>8.3f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DigitalGenesis headless simulation')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--ticks', type=int, default=1000)
    parser.add_argument('--interval', type=int, default=50)
    args = parser.parse_args()
    run(seed=args.seed, max_ticks=args.ticks, print_interval=args.interval)
