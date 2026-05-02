# DigitalGenesis — v1 Spec

## Goal
A single-celled open-ended evolution simulator. One ancestor cell with a variable-length genome evolves into a diverse population over thousands of generations. Predation and ecological niches must emerge from mutation + selection, not be hardcoded.

## Success Criteria (v1 is "done" when all four are true)
1. Sim runs 1000+ generations without total extinction
2. At least 3 distinct lineages with measurably different genomes coexist at gen 1000
3. Predation (DIET == cell) evolves spontaneously from a population that started as pure nutrient-eaters
4. Average genome length increases over the run (complexity ratchet works)

## World
- 200x200 grid, torus topology (wraps at edges)
- Each grid cell has a `nutrient_level` from 0-100
- Nutrients regenerate at +1 per tick, capped at 100
- World tick = one simulation step

## Organisms (Cells)
Each cell has:
- `position`: (x, y) on grid
- `energy`: float, starts at 50
- `age`: int, starts at 0
- `genome`: list of Gene objects (variable length)
- `lineage_id`: tracks ancestry for visualization
- `parent_id`: for phylogenetic tree

## Genome
A genome is a list of genes. Each gene is `(type: str, value: float)`.

Gene types and what they do (multiple genes of same type stack additively):
- `SIZE`: bigger = more energy capacity, but higher upkeep cost
- `METABOLISM`: efficiency of converting nutrients to energy
- `MOTILITY`: movement speed per tick (0 = stationary)
- `SENSE_RANGE`: radius of perception for food/prey
- `REPRODUCTION_THRESHOLD`: energy needed to divide
- `MUTATION_RATE`: per-gene mutation chance during reproduction (yes, mutation rate itself evolves)
- `DIET_NUTRIENT`: ability to eat grid nutrients
- `DIET_CELL`: ability to eat other cells (predation)
- `DEFENSE`: resistance to being eaten
- `OFFENSE`: ability to overcome prey defense

Starting genome (the ancestor): 5 genes — one each of SIZE, METABOLISM, MOTILITY, SENSE_RANGE, DIET_NUTRIENT, all with low values (~1.0).

## Per-Tick Rules (in order)
1. Each cell loses energy: `upkeep = 0.1 * size + 0.05 * motility`
2. Cell ages by 1
3. If SENSE_RANGE > 0, scan within radius. Move one step toward best target (highest nutrient cell, or weakest neighboring prey if DIET_CELL > 0)
4. Else move randomly if MOTILITY > 0
5. If on nutrient-rich cell and DIET_NUTRIENT > 0, absorb: `gain = min(nutrient_level, METABOLISM * DIET_NUTRIENT)`
6. If adjacent to another cell and DIET_CELL > 0 and OFFENSE > target.DEFENSE, eat target: gain target's energy * 0.7
7. If energy > REPRODUCTION_THRESHOLD: divide. Spawn child at adjacent free position with mutated genome. Both parent and child get half the energy.
8. If energy <= 0 or age > 500: die.

## Mutation (on reproduction)
Per-gene, independent rolls based on the cell's MUTATION_RATE:
- 80% chance per gene: tweak value by ±10% (Gaussian)
- 10% chance overall: add new random gene (random type, value 0.5-2.0)
- 5% chance overall: delete a random gene (genome must stay length >= 1)
- 5% chance overall: duplicate a random gene

## Visualization (Pygame)
- 800x600 window minimum
- Left side: world view, cells as colored dots, dot size scales with SIZE gene
- Color: derived from lineage_id (assign new HSV hue when a "major" mutation occurs — e.g., gene added or deleted)
- Right side panel:
  - Current population count
  - Current generation/tick number
  - Average genome length (live updating)
  - Population over time graph (matplotlib embedded, or simple line plot in pygame)
  - Number of distinct lineages
  - Number of cells with DIET_CELL > 0 (predator count)

## Architecture (important — keep clean)
- `world.py`: Grid, nutrient regeneration, spatial lookups
- `genome.py`: Gene, Genome, mutation logic
- `cell.py`: Cell class, behavior rules
- `simulation.py`: main tick loop, headless runnable
- `visualizer.py`: Pygame rendering, takes simulation as input
- `main.py`: entry point with CLI args (--headless, --speed, --seed)

The simulation must be runnable HEADLESS (no Pygame) for fast tuning. Visualizer is a separate layer.

## Testing
Write pytest tests for:
- Mutation produces valid genomes (no negative values where invalid, no empty genomes)
- Reproduction halves parent energy
- Eating transfers correct energy
- Cell at energy 0 dies on next tick
- Sim with 0 cells produces 0 cells (no spontaneous generation)

## Out of Scope for v1
- Multicellularity / sticking
- Neural networks
- Sexual reproduction
- 3D
- Real physics (Box2D, Pymunk)
- Saving/loading sims (just run from seed)

## Tech Stack
- Python 3.11+
- NumPy for grid math
- Pygame for visualization
- Matplotlib for population graphs (or pygame primitives if simpler)
- pytest for tests
- No other dependencies without asking