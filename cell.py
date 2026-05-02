import random
import math
from genome import Genome, Gene
from world import GRID_SIZE


class Cell:
    _next_id = 0

    def __init__(self, position: tuple, genome: Genome,
                 lineage_id: int = None, parent_id: int = None):
        Cell._next_id += 1
        self.id = Cell._next_id
        self.position = position
        self.energy = 50.0
        self.age = 0
        self.genome = genome
        self.lineage_id = lineage_id if lineage_id is not None else self.id
        self.parent_id = parent_id
        self.alive = True

    def tick(self, world, cells: list) -> 'Cell | None':
        size = max(0.01, self.genome.get_trait('SIZE'))
        motility = self.genome.get_trait('MOTILITY')
        self.energy -= 0.1 * size + 0.05 * motility
        self.age += 1

        if motility > 0:
            sense_range = self.genome.get_trait('SENSE_RANGE')
            diet_cell = self.genome.get_trait('DIET_CELL')
            if sense_range > 0:
                target = self._sense_target(world, cells, sense_range, diet_cell)
            else:
                target = None
            if target is not None:
                self._move_toward(target)
            else:
                self._move_random()

        diet_nutrient = self.genome.get_trait('DIET_NUTRIENT')
        if diet_nutrient > 0:
            metabolism = max(0.01, self.genome.get_trait('METABOLISM'))
            x, y = self.position
            self.energy += world.consume_nutrient(x, y, metabolism * diet_nutrient)

        diet_cell = self.genome.get_trait('DIET_CELL')
        if diet_cell > 0:
            offense = max(1.0, self.genome.get_trait('OFFENSE'))
            prey = self._adjacent_prey(cells, offense)
            if prey is not None:
                self.energy += prey.energy * 0.7
                prey.alive = False

        child = None
        threshold = max(10.0, self.genome.get_trait('REPRODUCTION_THRESHOLD'))
        if self.energy > threshold:
            child = self._reproduce()

        if self.energy <= 0 or self.age > 500:
            self.alive = False

        return child

    def _sense_target(self, world, cells: list, sense_range: float, diet_cell: float):
        x, y = self.position

        if diet_cell > 0:
            offense = max(1.0, self.genome.get_trait('OFFENSE'))
            best_prey_pos = None
            best_defense = float('inf')
            for cell in cells:
                if cell is self or not cell.alive:
                    continue
                cx, cy = cell.position
                dx = (cx - x + GRID_SIZE // 2) % GRID_SIZE - GRID_SIZE // 2
                dy = (cy - y + GRID_SIZE // 2) % GRID_SIZE - GRID_SIZE // 2
                if math.sqrt(dx * dx + dy * dy) <= sense_range:
                    defense = cell.genome.get_trait('DEFENSE')
                    if offense > defense and defense < best_defense:
                        best_defense = defense
                        best_prey_pos = cell.position
            if best_prey_pos is not None:
                return best_prey_pos

        radius = max(1, math.ceil(sense_range))
        best_pos = None
        best_nutrient = -1.0
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if math.sqrt(dx * dx + dy * dy) > sense_range:
                    continue
                nx, ny = (x + dx) % GRID_SIZE, (y + dy) % GRID_SIZE
                n = float(world.nutrient_level[nx, ny])
                if n > best_nutrient:
                    best_nutrient = n
                    best_pos = (nx, ny)
        return best_pos

    def _move_toward(self, target: tuple):
        x, y = self.position
        tx, ty = target
        dx = (tx - x + GRID_SIZE // 2) % GRID_SIZE - GRID_SIZE // 2
        dy = (ty - y + GRID_SIZE // 2) % GRID_SIZE - GRID_SIZE // 2
        sx = 1 if dx > 0 else (-1 if dx < 0 else 0)
        sy = 1 if dy > 0 else (-1 if dy < 0 else 0)
        self.position = ((x + sx) % GRID_SIZE, (y + sy) % GRID_SIZE)

    def _move_random(self):
        x, y = self.position
        self.position = ((x + random.randint(-1, 1)) % GRID_SIZE,
                         (y + random.randint(-1, 1)) % GRID_SIZE)

    def _adjacent_prey(self, cells: list, offense: float):
        x, y = self.position
        for cell in cells:
            if cell is self or not cell.alive:
                continue
            cx, cy = cell.position
            dx = abs((cx - x + GRID_SIZE // 2) % GRID_SIZE - GRID_SIZE // 2)
            dy = abs((cy - y + GRID_SIZE // 2) % GRID_SIZE - GRID_SIZE // 2)
            if dx <= 1 and dy <= 1 and offense > cell.genome.get_trait('DEFENSE'):
                return cell
        return None

    def _reproduce(self) -> 'Cell':
        self.energy /= 2.0

        child_genome = self.genome.mutate()

        # structural change (gene added/deleted/type-changed) → new lineage branch
        if (len(child_genome) != len(self.genome) or
                child_genome.gene_type_set() != self.genome.gene_type_set()):
            new_lineage_id = Cell._next_id + 1  # equals child.id after __init__
        else:
            new_lineage_id = self.lineage_id

        x, y = self.position
        child_pos = ((x + random.randint(-1, 1)) % GRID_SIZE,
                     (y + random.randint(-1, 1)) % GRID_SIZE)

        child = Cell(child_pos, child_genome,
                     lineage_id=new_lineage_id, parent_id=self.id)
        child.energy = self.energy
        return child
