from dataclasses import dataclass, field
from typing import Dict, Optional

ALPHABET = 'ABCDEFGHIJKL'


@dataclass
class CodonEffect:
    kind: str  # 'body_part' | 'behavior' | 'stat_mod' | 'conditional' | 'special'
    part_type: Optional[str] = None   # canonical name used by renderer
    visual: Optional[str] = None      # display label
    stat_deltas: Dict[str, float] = field(default_factory=dict)
    behavior: Optional[str] = None    # behavior flag name
    condition: Optional[str] = None   # condition name for conditional codons
    special: Optional[str] = None     # special action name


CODON_TABLE: Dict[str, CodonEffect] = {
    # ── Body Parts ─────────────────────────────────────────────────────────────
    'AEF': CodonEffect(kind='body_part', part_type='spike',          visual='Spike',
                       stat_deltas={'offense': 1}),
    'GHC': CodonEffect(kind='body_part', part_type='plate',          visual='Plate',
                       stat_deltas={'defense': 1}),
    'BK':  CodonEffect(kind='body_part', part_type='eye',            visual='Eye',
                       stat_deltas={'sense_range': 1}),
    'JJ':  CodonEffect(kind='body_part', part_type='flagellum',      visual='Flagellum',
                       stat_deltas={'motility': 1}),
    'LCD': CodonEffect(kind='body_part', part_type='mouth_nutrient', visual='Mouth-N',
                       stat_deltas={'nutrient_eat': 1}),
    'LCK': CodonEffect(kind='body_part', part_type='mouth_cell',     visual='Mouth-C',
                       stat_deltas={'cell_eat': 1}),
    'HHH': CodonEffect(kind='body_part', part_type='shell',          visual='Shell',
                       stat_deltas={'defense': 2, 'motility': -0.5}),
    'FBL': CodonEffect(kind='body_part', part_type='tentacle',       visual='Tentacle',
                       stat_deltas={'sense_range': 1, 'cell_eat': 1}),
    'ABE': CodonEffect(kind='body_part', part_type='fin',            visual='Fin',
                       stat_deltas={'motility': 1}),
    'KKK': CodonEffect(kind='body_part', part_type='body_mass',      visual='Body Mass',
                       stat_deltas={'size': 1, 'energy_capacity': 20}),

    # ── Behavior Modifiers ─────────────────────────────────────────────────────
    'CDE': CodonEffect(kind='behavior', behavior='aggressive'),
    'DEF': CodonEffect(kind='behavior', behavior='cowardly'),
    'EFG': CodonEffect(kind='behavior', behavior='greedy'),
    'FGH': CodonEffect(kind='behavior', behavior='patient'),
    'GHI': CodonEffect(kind='behavior', behavior='social'),
    'HIJ': CodonEffect(kind='behavior', behavior='loner'),
    'IJK': CodonEffect(kind='behavior', behavior='active'),
    'JKL': CodonEffect(kind='behavior', behavior='sedentary'),

    # ── Stat Modifiers ─────────────────────────────────────────────────────────
    'AAA': CodonEffect(kind='stat_mod', stat_deltas={'metabolism': 0.5}),
    'BBB': CodonEffect(kind='stat_mod', stat_deltas={'mutation_rate': 0.05}),
    'CCC': CodonEffect(kind='stat_mod', stat_deltas={'reproduction_threshold': -5}),
    'DDD': CodonEffect(kind='stat_mod', stat_deltas={'reproduction_threshold': 10}),
    'EEE': CodonEffect(kind='stat_mod', stat_deltas={'max_age': 50}),
    'FFF': CodonEffect(kind='stat_mod', stat_deltas={'energy_efficiency': 0.2}),
    'GGG': CodonEffect(kind='stat_mod', stat_deltas={'offspring_count': 1}),

    # ── Conditional Codons ─────────────────────────────────────────────────────
    # When condition is true at runtime, the next codon's stat_deltas fire again.
    'ACE': CodonEffect(kind='conditional', condition='low_energy'),
    'BDF': CodonEffect(kind='conditional', condition='predator_nearby'),
    'CEG': CodonEffect(kind='conditional', condition='food_nearby'),
    'DFH': CodonEffect(kind='conditional', condition='alone'),
    'EGI': CodonEffect(kind='conditional', condition='crowded'),
    'FHJ': CodonEffect(kind='conditional', condition='young'),

    # ── Special ────────────────────────────────────────────────────────────────
    'LLL': CodonEffect(kind='special', special='reset'),
    'LKL': CodonEffect(kind='special', special='stop'),
    'KLK': CodonEffect(kind='special', special='symmetry'),
    'LJL': CodonEffect(kind='special', special='color_signal'),
}
