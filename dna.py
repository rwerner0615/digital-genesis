import random
from codon_table import ALPHABET

ANCESTOR = 'LCDJJABEBKAEFCCCAAALCDJJABEBK'


def validate(genome: str) -> bool:
    return bool(genome) and all(c in ALPHABET for c in genome)


def mutate(genome: str, mutation_rate: float) -> str:
    letters = list(genome)

    # Point mutation: swap one random letter
    if random.random() < mutation_rate * 0.60 and letters:
        i = random.randrange(len(letters))
        letters[i] = random.choice(ALPHABET)

    # Insertion: add one random letter at a random position
    if random.random() < mutation_rate * 0.15:
        i = random.randint(0, len(letters))
        letters.insert(i, random.choice(ALPHABET))

    # Deletion: remove one random letter (guard: keep at least 1)
    if random.random() < mutation_rate * 0.15 and len(letters) > 1:
        i = random.randrange(len(letters))
        letters.pop(i)

    # Duplication: copy a 5–15 letter section and insert it elsewhere
    if random.random() < mutation_rate * 0.10 and len(letters) >= 5:
        start = random.randrange(len(letters) - 4)
        seg_len = random.randint(5, min(15, len(letters) - start))
        segment = letters[start:start + seg_len]
        insert_pos = random.randint(0, len(letters))
        letters[insert_pos:insert_pos] = segment

    return ''.join(letters)
