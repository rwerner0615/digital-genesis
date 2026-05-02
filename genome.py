import random
import numpy as np
from dataclasses import dataclass
from typing import List

GENE_TYPES = [
    'SIZE', 'METABOLISM', 'MOTILITY', 'SENSE_RANGE',
    'REPRODUCTION_THRESHOLD', 'MUTATION_RATE',
    'DIET_NUTRIENT', 'DIET_CELL', 'DEFENSE', 'OFFENSE',
]


@dataclass
class Gene:
    type: str
    value: float


class Genome:
    def __init__(self, genes: List[Gene]):
        self.genes = list(genes)

    def get_trait(self, gene_type: str) -> float:
        return sum(g.value for g in self.genes if g.type == gene_type)

    def gene_type_set(self) -> frozenset:
        return frozenset(g.type for g in self.genes)

    def to_vector(self) -> np.ndarray:
        return np.array([self.get_trait(gt) for gt in GENE_TYPES])

    def mutate(self) -> 'Genome':
        mr = max(0.1, self.get_trait('MUTATION_RATE'))
        genes = [Gene(g.type, g.value) for g in self.genes]

        for gene in genes:
            if random.random() < mr * 0.80:
                gene.value = max(0.0, gene.value * (1.0 + random.gauss(0, 0.1)))

        if random.random() < mr * 0.10:
            genes.append(Gene(random.choice(GENE_TYPES), random.uniform(0.5, 2.0)))

        if random.random() < mr * 0.05 and len(genes) > 1:
            genes.pop(random.randrange(len(genes)))

        if random.random() < mr * 0.05 and genes:
            src = random.choice(genes)
            genes.append(Gene(src.type, src.value))

        return Genome(genes)

    def __len__(self) -> int:
        return len(self.genes)

    def __repr__(self) -> str:
        parts = [f'{g.type}={g.value:.2f}' for g in self.genes]
        return f"Genome([{', '.join(parts)}])"
