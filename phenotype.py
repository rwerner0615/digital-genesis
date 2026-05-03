from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from codon_table import CODON_TABLE

BASE_STATS: Dict[str, float] = {
    'motility':               1.0,
    'sense_range':            1.0,
    'offense':                1.0,
    'defense':                1.0,
    'max_age':                200,   # int after floors
    'size':                   3.0,
    'nutrient_eat':           0.0,
    'cell_eat':               0.0,
    'metabolism':             1.0,
    'mutation_rate':          0.3,
    'reproduction_threshold': 50.0,
    'energy_efficiency':      1.0,
    'offspring_count':        1,     # int after floors
    'energy_capacity':        100.0,
}


@dataclass
class ConditionalBonus:
    condition: str
    stat_deltas: Dict[str, float]


@dataclass
class Phenotype:
    stats: Dict[str, float]
    body_parts: Dict[str, int]         # part_type → count
    symmetric_parts: Set[str]          # part_types placed while symmetry active
    behaviors: Set[str]                # active behavior flag names
    conditional_bonuses: List[ConditionalBonus]
    color_override: Optional[Tuple[int, int]]  # (h1, h2) as 0–11 letter indices
    symmetry: bool
    has_head_marker: bool

    def effective_stats(self, active_conditions: Set[str]) -> Dict[str, float]:
        stats = dict(self.stats)
        for bonus in self.conditional_bonuses:
            if bonus.condition in active_conditions:
                for stat, delta in bonus.stat_deltas.items():
                    stats[stat] = stats.get(stat, 0.0) + delta
        return stats


def parse_dna(genome: str) -> Phenotype:
    stats = dict(BASE_STATS)
    body_parts: Dict[str, int] = {}
    symmetric_parts: Set[str] = set()
    behaviors: Set[str] = set()
    conditional_bonuses: List[ConditionalBonus] = []
    color_override: Optional[Tuple[int, int]] = None
    symmetry = False
    has_head_marker = False
    body_stopped = False
    pending_condition: Optional[str] = None

    pos = 0
    while pos < len(genome):
        # Greedy match: try lengths 4, 3, 2
        matched = None
        for length in (4, 3, 2):
            chunk = genome[pos:pos + length]
            if chunk in CODON_TABLE:
                matched = (chunk, length)
                break

        if matched is None:
            pending_condition = None  # junk letter cancels any pending conditional
            pos += 1
            continue

        codon, length = matched
        effect = CODON_TABLE[codon]
        pos += length

        # Special codons are processed first; they always consume any pending conditional.
        if effect.kind == 'special':
            pending_condition = None
            if effect.special == 'reset':
                has_head_marker = True
            elif effect.special == 'stop':
                body_stopped = True
            elif effect.special == 'symmetry':
                symmetry = True
            elif effect.special == 'color_signal':
                if pos + 2 <= len(genome):
                    h1 = ord(genome[pos])     - ord('A')
                    h2 = ord(genome[pos + 1]) - ord('A')
                    color_override = (h1, h2)
                    pos += 2
            continue

        # Body parts after stop have no stat or visual effect.
        stats_applicable = not (effect.kind == 'body_part' and body_stopped)

        # Resolve any pending conditional: if the current codon has stats to
        # double, record the bonus; either way, consume the pending condition.
        if pending_condition is not None:
            if stats_applicable and effect.stat_deltas:
                conditional_bonuses.append(
                    ConditionalBonus(pending_condition, dict(effect.stat_deltas))
                )
            pending_condition = None

        if effect.kind == 'body_part' and not body_stopped:
            pt = effect.part_type
            body_parts[pt] = body_parts.get(pt, 0) + 1
            if symmetry:
                symmetric_parts.add(pt)
            for stat, delta in effect.stat_deltas.items():
                stats[stat] = stats.get(stat, 0.0) + delta

        elif effect.kind == 'behavior':
            behaviors.add(effect.behavior)

        elif effect.kind == 'stat_mod':
            for stat, delta in effect.stat_deltas.items():
                stats[stat] = stats.get(stat, 0.0) + delta

        elif effect.kind == 'conditional':
            pending_condition = effect.condition

    # Apply floors and type coercions
    stats['reproduction_threshold'] = max(20.0, stats['reproduction_threshold'])
    stats['motility']               = max(0.0,  stats['motility'])
    stats['offense']                = max(0.0,  stats['offense'])
    stats['defense']                = max(0.0,  stats['defense'])
    stats['sense_range']            = max(0.0,  stats['sense_range'])
    stats['nutrient_eat']           = max(0.0,  stats['nutrient_eat'])
    stats['cell_eat']               = max(0.0,  stats['cell_eat'])
    stats['size']                   = max(1.0,  stats['size'])
    stats['metabolism']             = max(0.1,  stats['metabolism'])
    stats['mutation_rate']          = min(1.0, max(0.05, stats['mutation_rate']))
    stats['energy_capacity']        = max(10.0, stats['energy_capacity'])
    stats['energy_efficiency']      = max(0.1,  stats['energy_efficiency'])
    stats['max_age']                = max(50,   int(stats['max_age']))
    stats['offspring_count']        = max(1,    int(stats['offspring_count']))

    return Phenotype(
        stats=stats,
        body_parts=body_parts,
        symmetric_parts=symmetric_parts,
        behaviors=behaviors,
        conditional_bonuses=conditional_bonuses,
        color_override=color_override,
        symmetry=symmetry,
        has_head_marker=has_head_marker,
    )
