from codon_table import ALPHABET, CODON_TABLE


def test_all_codons_use_valid_alphabet():
    for codon in CODON_TABLE:
        assert all(c in ALPHABET for c in codon), f"Invalid character in codon '{codon}'"


def test_codon_lengths_are_two_to_four():
    for codon in CODON_TABLE:
        assert 2 <= len(codon) <= 4, f"Codon '{codon}' has invalid length {len(codon)}"


def test_no_duplicate_codon_keys():
    keys = list(CODON_TABLE.keys())
    assert len(keys) == len(set(keys))


def test_active_codon_count():
    assert len(CODON_TABLE) == 35


def test_body_part_count():
    assert sum(1 for e in CODON_TABLE.values() if e.kind == 'body_part') == 10


def test_behavior_count():
    assert sum(1 for e in CODON_TABLE.values() if e.kind == 'behavior') == 8


def test_stat_mod_count():
    assert sum(1 for e in CODON_TABLE.values() if e.kind == 'stat_mod') == 7


def test_conditional_count():
    assert sum(1 for e in CODON_TABLE.values() if e.kind == 'conditional') == 6


def test_special_count():
    assert sum(1 for e in CODON_TABLE.values() if e.kind == 'special') == 4


def test_body_parts_have_part_type_and_visual():
    for codon, effect in CODON_TABLE.items():
        if effect.kind == 'body_part':
            assert effect.part_type is not None, f"'{codon}' missing part_type"
            assert effect.visual is not None,    f"'{codon}' missing visual"


def test_body_part_stat_deltas_are_nonempty():
    for codon, effect in CODON_TABLE.items():
        if effect.kind == 'body_part':
            assert effect.stat_deltas, f"'{codon}' has no stat_deltas"


def test_behaviors_have_behavior_field():
    for codon, effect in CODON_TABLE.items():
        if effect.kind == 'behavior':
            assert effect.behavior is not None, f"'{codon}' missing behavior field"


def test_stat_mods_have_nonempty_stat_deltas():
    for codon, effect in CODON_TABLE.items():
        if effect.kind == 'stat_mod':
            assert effect.stat_deltas, f"'{codon}' has no stat_deltas"


def test_conditionals_have_condition_field():
    for codon, effect in CODON_TABLE.items():
        if effect.kind == 'conditional':
            assert effect.condition is not None, f"'{codon}' missing condition"


def test_specials_have_special_field():
    for codon, effect in CODON_TABLE.items():
        if effect.kind == 'special':
            assert effect.special is not None, f"'{codon}' missing special"


def test_all_known_specials_present():
    specials = {e.special for e in CODON_TABLE.values() if e.kind == 'special'}
    assert specials == {'reset', 'stop', 'symmetry', 'color_signal'}


def test_all_known_behaviors_present():
    behaviors = {e.behavior for e in CODON_TABLE.values() if e.kind == 'behavior'}
    assert behaviors == {
        'aggressive', 'cowardly', 'greedy', 'patient',
        'social', 'loner', 'active', 'sedentary',
    }


def test_all_known_conditions_present():
    conditions = {e.condition for e in CODON_TABLE.values() if e.kind == 'conditional'}
    assert conditions == {
        'low_energy', 'predator_nearby', 'food_nearby',
        'alone', 'crowded', 'young',
    }


def test_alphabet_has_twelve_letters():
    assert len(ALPHABET) == 12
    assert len(set(ALPHABET)) == 12
