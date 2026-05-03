import random
from codon_table import ALPHABET

ANCESTOR = 'LCDJJABEBKAEFCCCAAALCDJJABEBK'

# Hard cap: prevents BBB-driven mutation_rate feedback from causing genome explosion.
# 120 letters supports rich diversity (~45 active codons) without runaway upkeep.
MAX_GENOME_LENGTH = 120


def validate(genome: str) -> bool:
    return bool(genome) and all(c in ALPHABET for c in genome)


def mutate(genome: str, mutation_rate: float) -> str:
    letters = list(genome)

    # Point mutation: swap one random letter
    if random.random() < mutation_rate * 0.60 and letters:
        i = random.randrange(len(letters))
        letters[i] = random.choice(ALPHABET)

    # Insertion: add one random letter (suppressed at cap)
    if random.random() < mutation_rate * 0.15 and len(letters) < MAX_GENOME_LENGTH:
        i = random.randint(0, len(letters))
        letters.insert(i, random.choice(ALPHABET))

    # Deletion: remove one random letter (guard: keep at least 1)
    if random.random() < mutation_rate * 0.15 and len(letters) > 1:
        i = random.randrange(len(letters))
        letters.pop(i)

    # Duplication: copy a 5–15 letter section (suppressed at cap, segment capped too)
    if random.random() < mutation_rate * 0.10 and len(letters) >= 5 and len(letters) < MAX_GENOME_LENGTH:
        start = random.randrange(len(letters) - 4)
        max_seg = min(15, len(letters) - start, MAX_GENOME_LENGTH - len(letters))
        if max_seg >= 1:
            seg_len = random.randint(1, max_seg)
            segment = letters[start:start + seg_len]
            insert_pos = random.randint(0, len(letters))
            letters[insert_pos:insert_pos] = segment

    return ''.join(letters)
