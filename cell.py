import random
import math
from typing import Dict, List, Optional

from world import GRID_SIZE
from dna import mutate
from phenotype import parse_dna

_HALF = GRID_SIZE // 2

# Spatial hash constants — bucket size ≈ base sense_range
BUCKET_SIZE = 4
GRID_BUCKETS = GRID_SIZE // BUCKET_SIZE  # 50 buckets per axis


def _torus_dx(a: int, b: int) -> int:
    return (b - a + _HALF) % GRID_SIZE - _HALF


def _torus_dist_sq(x1: int, y1: int, x2: int, y2: int) -> int:
    dx = _torus_dx(x1, x2)
    dy = _torus_dx(y1, y2)
    return dx * dx + dy * dy


def _step(d: int) -> int:
    return 1 if d > 0 else (-1 if d < 0 else 0)


def build_cell_index(cells: list) -> Dict:
    """Spatial hash: (bx, by) → list[Cell]. Built once per tick, shared by all cells."""
    index: Dict = {}
    for c in cells:
        if c.alive:
            key = (c.position[0] // BUCKET_SIZE, c.position[1] // BUCKET_SIZE)
            lst = index.get(key)
            if lst is None:
                index[key] = [c]
            else:
                lst.append(c)
    return index


def _nearby(index: Dict, x: int, y: int, sr: float, exclude: 'Cell') -> list:
    """Alive cells within radius sr, excluding self. Dead cells skipped inline."""
    sr_sq = sr * sr
    bx = x // BUCKET_SIZE
    by = y // BUCKET_SIZE
    br = int(sr / BUCKET_SIZE) + 1
    out = []
    for dbx in range(-br, br + 1):
        for dby in range(-br, br + 1):
            bucket = index.get(((bx + dbx) % GRID_BUCKETS,
                                (by + dby) % GRID_BUCKETS))
            if not bucket:
                continue
            for c in bucket:
                if c is exclude or not c.alive:
                    continue
                if _torus_dist_sq(x, y, c.position[0], c.position[1]) <= sr_sq:
                    out.append(c)
    return out


class Cell:
    _next_id = 0

    def __init__(self, position: tuple, dna: str,
                 lineage_id: int = None, parent_id: int = None):
        Cell._next_id += 1
        self.id = Cell._next_id
        self.position = position
        self.dna = dna
        self.phenotype = parse_dna(dna)
        self.energy = 50.0
        self.age = 0
        self.lineage_id = lineage_id if lineage_id is not None else self.id
        self.parent_id = parent_id
        self.alive = True

    # ------------------------------------------------------------------
    # Main per-tick entry — returns list of newborn children (may be empty)
    # ------------------------------------------------------------------

    def tick(self, world, cell_index: dict) -> List['Cell']:
        stats = self.phenotype.stats
        behaviors = self.phenotype.behaviors
        x, y = self.position
        sr = stats['sense_range']

        # One spatial query, shared by condition eval + movement
        near = _nearby(cell_index, x, y, sr, self)

        active_conds = self._eval_conditions(near, world, x, y, stats)
        eff = self.phenotype.effective_stats(active_conds)

        total_parts = sum(self.phenotype.body_parts.values())
        self.energy -= (0.1 * eff['size'] + 0.015 * total_parts + 0.01 * len(self.dna)) / eff['energy_efficiency']
        self.age += 1

        if eff['motility'] > 0:
            eff_sr = eff['sense_range']
            if eff_sr > sr:  # conditional bonus widened range → re-query
                near = _nearby(cell_index, x, y, eff_sr, self)
            self._move(world, near, eff, behaviors, active_conds)

        if eff['nutrient_eat'] > 0:
            if 'greedy' in behaviors or self.energy < eff['energy_capacity'] * 0.9:
                px, py = self.position
                gained = world.consume_nutrient(px, py, eff['metabolism'] * eff['nutrient_eat'])
                self.energy = min(self.energy + gained, eff['energy_capacity'])

        if eff['cell_eat'] > 0:
            px, py = self.position
            adj = _nearby(cell_index, px, py, 1.5, self)  # 3×3 box
            prey = self._find_prey(adj, eff['offense'], 'patient' in behaviors)
            if prey is not None:
                self.energy = min(self.energy + prey.energy * 0.7, eff['energy_capacity'])
                prey.alive = False

        children: List['Cell'] = []
        if self.energy > eff['reproduction_threshold']:
            children = self._reproduce(eff)

        if self.energy <= 0 or self.age > eff['max_age']:
            self.alive = False

        return children

    # ------------------------------------------------------------------
    # Condition evaluation
    # ------------------------------------------------------------------

    def _eval_conditions(self, near: list, world, x: int, y: int,
                          stats: dict) -> set:
        active: set = set()

        if self.age < 50:
            active.add('young')
        if self.energy < stats['energy_capacity'] * 0.3:
            active.add('low_energy')

        n = len(near)
        if n == 0:
            active.add('alone')
        elif n > 5:
            active.add('crowded')

        for c in near:
            if c.phenotype.stats['cell_eat'] > 0:
                active.add('predator_nearby')
                break

        # O(1) food check: current tile only
        if world.nutrient_level[x % GRID_SIZE, y % GRID_SIZE] > 5.0:
            active.add('food_nearby')

        return active

    # ------------------------------------------------------------------
    # Movement — priority-ordered behavior tree
    # ------------------------------------------------------------------

    def _move(self, world, near: list, eff: dict, behaviors: set, conds: set):
        if 'sedentary' in behaviors and 'active' not in behaviors:
            if self.energy > eff['reproduction_threshold'] * 0.4:
                return

        # 1. Low energy → seek nutrients urgently
        if 'low_energy' in conds:
            t = self._best_nutrient(world, eff['sense_range'])
            return self._move_toward(t) if t else self._move_random()

        # 2. Predator nearby + cowardly → flee predator
        if 'predator_nearby' in conds and 'cowardly' in behaviors:
            for c in near:
                if c.phenotype.stats['cell_eat'] > 0:
                    return self._move_away(c.position)

        # 3. Food nearby + can eat nutrients → approach food
        if 'food_nearby' in conds and eff['nutrient_eat'] > 0:
            t = self._best_nutrient(world, eff['sense_range'])
            if t:
                return self._move_toward(t)

        # 4. Cowardly (no immediate predator) → flee nearest visible cell
        if 'cowardly' in behaviors and near:
            return self._move_away(near[0].position)

        # 5. Aggressive cell eater → chase weakest reachable prey
        if 'aggressive' in behaviors and eff['cell_eat'] > 0:
            t = self._best_prey_pos(near, eff['offense'])
            if t:
                return self._move_toward(t)

        # 6. Social → approach same-lineage cell
        if 'social' in behaviors:
            for c in near:
                if c.lineage_id == self.lineage_id:
                    return self._move_toward(c.position)

        # 7. Loner → flee all visible
        if 'loner' in behaviors and near:
            return self._move_away(near[0].position)

        # Default: hunt prey or seek nutrients
        if eff['cell_eat'] > 0:
            t = self._best_prey_pos(near, eff['offense'])
            if t:
                return self._move_toward(t)

        t = self._best_nutrient(world, eff['sense_range'])
        if t:
            return self._move_toward(t)

        self._move_random()

    # ------------------------------------------------------------------
    # Sensing helpers
    # ------------------------------------------------------------------

    def _best_nutrient(self, world, sense_range: float) -> Optional[tuple]:
        x, y = self.position
        radius = max(1, math.ceil(sense_range))
        sr_sq = sense_range * sense_range
        best_pos, best_val = None, -1.0
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy > sr_sq:
                    continue
                nx, ny = (x + dx) % GRID_SIZE, (y + dy) % GRID_SIZE
                v = float(world.nutrient_level[nx, ny])
                if v > best_val:
                    best_val = v
                    best_pos = (nx, ny)
        return best_pos

    def _best_prey_pos(self, near: list, offense: float) -> Optional[tuple]:
        best_pos, best_def = None, float('inf')
        for c in near:
            d = c.phenotype.stats['defense']
            if offense > d and d < best_def:
                best_def = d
                best_pos = c.position
        return best_pos

    def _find_prey(self, adj: list, offense: float, patient: bool) -> Optional['Cell']:
        x, y = self.position
        best, best_val = None, -1.0
        for c in adj:
            cx, cy = c.position
            dx = abs(_torus_dx(x, cx))
            dy = abs(_torus_dx(y, cy))
            if dx <= 1 and dy <= 1 and offense > c.phenotype.stats['defense']:
                val = c.energy if patient else 1.0 / (c.phenotype.stats['defense'] + 1)
                if val > best_val:
                    best_val = val
                    best = c
        return best

    # ------------------------------------------------------------------
    # Movement primitives
    # ------------------------------------------------------------------

    def _move_toward(self, target: tuple):
        x, y = self.position
        self.position = (
            (x + _step(_torus_dx(x, int(target[0])))) % GRID_SIZE,
            (y + _step(_torus_dx(y, int(target[1])))) % GRID_SIZE,
        )

    def _move_away(self, threat: tuple):
        x, y = self.position
        self.position = (
            (x - _step(_torus_dx(x, int(threat[0])))) % GRID_SIZE,
            (y - _step(_torus_dx(y, int(threat[1])))) % GRID_SIZE,
        )

    def _move_random(self):
        x, y = self.position
        self.position = (
            (x + random.randint(-1, 1)) % GRID_SIZE,
            (y + random.randint(-1, 1)) % GRID_SIZE,
        )

    # ------------------------------------------------------------------
    # Reproduction
    # ------------------------------------------------------------------

    def _reproduce(self, eff: dict) -> List['Cell']:
        n = eff['offspring_count']
        self.energy /= (1 + n)

        x, y = self.position
        mr = eff['mutation_rate']
        parent_bp = frozenset(self.phenotype.body_parts.keys())
        parent_beh = self.phenotype.behaviors

        children = []
        for _ in range(n):
            child_dna = mutate(self.dna, mr)
            child = Cell(
                ((x + random.randint(-1, 1)) % GRID_SIZE,
                 (y + random.randint(-1, 1)) % GRID_SIZE),
                child_dna,
                parent_id=self.id,
            )
            child.energy = self.energy

            child_bp = frozenset(child.phenotype.body_parts.keys())
            if child_bp == parent_bp and child.phenotype.behaviors == parent_beh:
                child.lineage_id = self.lineage_id

            children.append(child)

        return children
