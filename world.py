import numpy as np

GRID_SIZE = 200
MAX_NUTRIENT = 100.0
REGEN_RATE = 1.0
SOFT_POPULATION_CAP = 800


class World:
    def __init__(self, seed: int = None):
        rng = np.random.default_rng(seed)
        self.nutrient_level = rng.uniform(10.0, 50.0, (GRID_SIZE, GRID_SIZE))

    def tick(self, population: int = 0):
        if population > SOFT_POPULATION_CAP:
            effective_rate = REGEN_RATE * (SOFT_POPULATION_CAP / population)
        else:
            effective_rate = REGEN_RATE
        np.add(self.nutrient_level, effective_rate, out=self.nutrient_level)
        np.minimum(self.nutrient_level, MAX_NUTRIENT, out=self.nutrient_level)

    def consume_nutrient(self, x: int, y: int, amount: float) -> float:
        x, y = x % GRID_SIZE, y % GRID_SIZE
        available = float(self.nutrient_level[x, y])
        consumed = min(available, max(0.0, amount))
        self.nutrient_level[x, y] -= consumed
        return consumed
