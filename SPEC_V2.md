# DigitalGenesis v2 — DNA Spec

## Branch
v2-dna (full rewrite — v1 stays on main untouched)

## Goal
Replace the gene-list system with a DNA-style letter-string genome. Creatures' behavior AND appearance are determined entirely by reading their DNA. Nothing about specific traits is hardcoded — only the codon-to-action lookup table.

## Success Criteria (v2 done when all 5 are true)
1. Genome is a string of letters from A-L only. No hardcoded gene types anywhere.
2. Predation, motility, sensing, reproduction all emerge from codon mutations.
3. Creatures render as composed bodies (multiple shapes) that visibly differ based on genome — not dots.
4. Sim runs 5,000+ ticks without total extinction.
5. At least 5 visually distinct creature "morphologies" coexist by tick 5,000.

## Alphabet
12 letters: A, B, C, D, E, F, G, H, I, J, K, L

## Codons
- Variable length: 2, 3, or 4 letters
- Read left-to-right with greedy matching: longest valid codon wins
- If no valid codon matches starting at a position, advance one letter (junk read)
- Total possible unique codons: 22,608. Active codons ~40. Rest = junk DNA.

## Codon Reading Algorithm
position = 0
codons_executed = []
while position < len(genome):
    for length in [4, 3, 2]:
        chunk = genome[position:position+length]
        if chunk in CODON_TABLE:
            codons_executed.append(chunk)
            position += length
            break
    else:
        position += 1  # skip junk letter

## Codon Table

### Body Parts (visual + stat) — 10 codons
Each body part renders visually AND gives a stat bonus. Multiple copies stack.

- AEF: Spike. Triangle radiating outward. +offense
- GHC: Plate. Curved arc on body edge. +defense
- BK: Eye. Small white circle with pupil. +sense_range
- JJ: Flagellum. Squiggly line trailing. +motility
- LCD: Mouth-nutrient. Green dot on body. +nutrient_eat
- LCK: Mouth-cell. Red dot on body. +cell_eat
- HHH: Shell. Outer ring around body. +defense, -motility
- FBL: Tentacle. Long line with thicker end. +sense_range, +cell_eat
- ABE: Fin. Short line on body edge. +motility
- KKK: Body Mass. Increases body radius. +size, +energy_capacity

### Behavior Modifiers — 8 codons
- CDE: Aggressive (chase prey if any sensed)
- DEF: Cowardly (flee from larger cells)
- EFG: Greedy (eat even at full energy)
- FGH: Patient (wait for high-value targets)
- GHI: Social (move toward same-color cells)
- HIJ: Loner (move away from other cells)
- IJK: Active (constant movement)
- JKL: Sedentary (move only when hungry)

### Stat Modifiers — 7 codons
- AAA: +metabolism
- BBB: +mutation_rate
- CCC: -reproduction_threshold (reproduce easier)
- DDD: +reproduction_threshold (reproduce harder, bigger offspring)
- EEE: +max_age
- FFF: +energy_efficiency
- GGG: +offspring_count (twins/triplets when reproducing)

### Conditional Codons — 6 codons
Modify next codon based on state. If condition true, next codon executes with bonus effect.
- ACE: If low energy
- BDF: If predator nearby
- CEG: If food nearby
- DFH: If alone
- EGI: If crowded
- FHJ: If young (age < 50)

### Special — 4 codons
- LLL: Reset/start codon (visual head marker)
- LKL: Stop codon (ends body construction at this point)
- KLK: Symmetry marker (mirrors next body parts to other side)
- LJL: Color signal (next 2 letters set body hue)

Total active codons: 39

## Genome
- Starting ancestor: 30-letter random string from A-L (seeded by --seed)
- Mutations on reproduction:
  - Point mutation (60%): random letter swapped to another random letter
  - Insertion (15%): random letter inserted at random position
  - Deletion (15%): random letter deleted
  - Duplication (10%): random 5-15 letter section copied and inserted

## Cell Properties
A cell is now defined by its DNA + derived state.
- dna: string of letters
- position, energy, age, lineage_id, parent_id (same as v1)
- phenotype: parsed result of reading DNA — list of body parts with positions, plus computed stats (size, motility, defense, offense, etc.)

Phenotype is parsed once per cell at birth, cached for the cell's lifetime.

## Per-Tick Rules
Same skeleton as v1, but stats come from phenotype, not gene-list:
- Upkeep: based on body part count + size
- Movement: based on phenotype.motility, modified by behavior codons
- Sensing: based on phenotype.sense_range
- Eating: based on phenotype.nutrient_eat and phenotype.cell_eat
- Combat: phenotype.offense vs target.defense
- Reproduction: when energy > threshold, mutate DNA, build new phenotype, spawn child

## Visualization
Creatures are no longer dots. Each cell renders as a composed body:
1. Central body circle (size from KKK count)
2. Body parts drawn at fixed angles around the body (8 angles, parts distributed evenly)
3. Color: derived from genome hash (similar lineages = similar colors)
4. Symmetry codon (KLK) mirrors body parts to opposite side

Render each frame from phenotype, no per-frame DNA parsing.

## Architecture
v2-dna/
- codon_table.py: The fixed lookup table
- dna.py: DNA string operations, mutation
- phenotype.py: Read DNA, produce phenotype (stats + body parts)
- cell.py: Cell class, uses phenotype for behavior
- world.py: mostly unchanged from v1
- simulation.py: tick loop
- visualizer.py: NEW renderer for composed bodies
- main.py: entry point
- tests/

## Out of Scope for v2
- Sexual reproduction
- Multicellularity
- Religion/belief codons
- Pheromones
- Day/night, seasons, terrain
These all come in v3+.

## Phases
- Phase 1: codon_table.py + dna.py + phenotype.py + tests
- Phase 2: cell.py + simulation.py rewrite, headless run, confirm evolution works the same as v1 in spirit
- Phase 3: visualizer.py rewrite for composed bodies
- Phase 4: tuning, success criteria, polish

## Tech Stack
Same as v1: Python 3.11+, NumPy, Pygame, pytest.