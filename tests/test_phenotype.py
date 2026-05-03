import pytest

from dna import ANCESTOR
from phenotype import BASE_STATS, ConditionalBonus, parse_dna


# ── Empty / junk genomes ──────────────────────────────────────────────────────

def test_empty_genome_yields_base_stats():
    p = parse_dna('')
    for key, val in BASE_STATS.items():
        assert p.stats[key] == pytest.approx(val), f"Mismatch on stat '{key}'"


def test_empty_genome_has_no_parts_or_behaviors():
    p = parse_dna('')
    assert p.body_parts == {}
    assert p.behaviors == set()
    assert p.conditional_bonuses == []
    assert not p.symmetry
    assert not p.has_head_marker
    assert p.color_override is None


def test_single_junk_letter_yields_base_stats():
    # 'A' alone cannot form any 2–4 letter codon → pure junk advance
    p = parse_dna('A')
    assert p.stats['motility'] == pytest.approx(BASE_STATS['motility'])
    assert p.body_parts == {}


# ── Ancestor genome ───────────────────────────────────────────────────────────

def test_ancestor_stats():
    p = parse_dna(ANCESTOR)
    assert p.stats['nutrient_eat']           == pytest.approx(2.0)
    assert p.stats['motility']               == pytest.approx(5.0)   # base 1 + 4×(JJ, ABE, JJ, ABE)
    assert p.stats['sense_range']            == pytest.approx(3.0)   # base 1 + 2×BK
    assert p.stats['offense']                == pytest.approx(2.0)   # base 1 + 1×AEF
    assert p.stats['metabolism']             == pytest.approx(1.5)   # base 1 + AAA
    assert p.stats['reproduction_threshold'] == pytest.approx(45.0)  # base 50 − CCC


def test_ancestor_body_parts():
    p = parse_dna(ANCESTOR)
    assert p.body_parts['mouth_nutrient'] == 2
    assert p.body_parts['flagellum']      == 2
    assert p.body_parts['fin']            == 2
    assert p.body_parts['eye']            == 2
    assert p.body_parts['spike']          == 1
    assert 'shell' not in p.body_parts


def test_ancestor_no_behaviors():
    p = parse_dna(ANCESTOR)
    assert p.behaviors == set()


def test_ancestor_no_conditional_bonuses():
    p = parse_dna(ANCESTOR)
    assert p.conditional_bonuses == []


def test_ancestor_no_color_override():
    p = parse_dna(ANCESTOR)
    assert p.color_override is None


# ── Greedy matching ───────────────────────────────────────────────────────────

def test_greedy_matches_three_letter_over_junk():
    # 'LCD' should be parsed as one mouth_nutrient codon, not junk
    p = parse_dna('LCD')
    assert p.body_parts.get('mouth_nutrient', 0) == 1


def test_two_letter_codon_matches():
    p = parse_dna('BK')
    assert p.body_parts.get('eye', 0) == 1
    assert p.stats['sense_range'] == pytest.approx(2.0)  # base 1 + 1


def test_adjacent_distinct_codons_both_fire():
    # AEF (spike) immediately followed by GHC (plate)
    p = parse_dna('AEFGHC')
    assert p.body_parts.get('spike', 0) == 1
    assert p.body_parts.get('plate', 0) == 1


def test_two_letter_codon_at_end_of_genome():
    p = parse_dna('AEFJJ')  # AEF then JJ at positions 3–4
    assert p.body_parts.get('flagellum', 0) == 1


# ── Stop codon (LKL) ──────────────────────────────────────────────────────────

def test_stop_codon_prevents_body_part_after_it():
    p = parse_dna('AEFLKLABE')  # AEF before stop, ABE after
    assert p.body_parts.get('spike', 0) == 1   # before stop: present
    assert p.body_parts.get('fin',   0) == 0   # after stop: absent


def test_stop_codon_preserves_stats_from_before():
    p = parse_dna('AEFLKLABE')
    assert p.stats['offense'] == pytest.approx(2.0)  # base 1 + AEF


def test_stop_codon_allows_behavior_after():
    p = parse_dna('LKLCDE')
    assert 'aggressive' in p.behaviors


def test_stop_codon_allows_stat_mod_after():
    p = parse_dna('LKLAAA')
    assert p.stats['metabolism'] == pytest.approx(1.5)  # base 1 + 0.5


def test_stop_codon_allows_stat_mod_but_no_body_part_stats():
    # HHH gives +2 defense and -0.5 motility as a body_part codon.
    # After LKL, HHH should produce neither.
    p = parse_dna('LKLHHH')
    assert p.stats['defense'] == pytest.approx(1.0)   # unchanged base
    assert p.stats['motility'] == pytest.approx(1.0)  # unchanged base


# ── Symmetry codon (KLK) ──────────────────────────────────────────────────────

def test_symmetry_flag_set():
    p = parse_dna('KLK')
    assert p.symmetry is True


def test_no_symmetry_without_klk():
    p = parse_dna(ANCESTOR)
    assert p.symmetry is False


def test_symmetry_marks_parts_added_after_it():
    p = parse_dna('KLKAEF')  # KLK then spike
    assert 'spike' in p.symmetric_parts


def test_parts_before_klk_not_in_symmetric_parts():
    p = parse_dna('AEFKLK')  # spike then KLK
    assert 'spike' not in p.symmetric_parts


def test_symmetry_does_not_affect_behaviors():
    p = parse_dna('KLKCDE')
    assert 'aggressive' in p.behaviors  # behavior still fires
    assert p.symmetry is True


# ── Color signal (LJL) ────────────────────────────────────────────────────────

def test_color_override_set_from_two_letters():
    # LJL then 'A'(=0) 'B'(=1) → override (0, 1)
    p = parse_dna('LJLAB')
    assert p.color_override == (0, 1)


def test_color_override_uses_last_ljl():
    # Two LJL codons: second one wins (override is last-write)
    p = parse_dna('LJLABLJLCD')  # first → (0,1), second → (2,3)
    assert p.color_override == (2, 3)


def test_color_override_none_without_ljl():
    p = parse_dna(ANCESTOR)
    assert p.color_override is None


def test_color_signal_requires_two_letters():
    # LJL at end with only one letter left → no override
    p = parse_dna('LJLA')
    assert p.color_override is None


def test_color_signal_at_very_end_no_letters():
    p = parse_dna('LJL')
    assert p.color_override is None


def test_ljl_color_letters_not_parsed_as_codons():
    # 'JJ' would be a flagellum codon; if LJL consumes those letters as color
    # data they must NOT also produce a body part.
    # A=0 B=1 C=2 D=3 E=4 F=5 G=6 H=7 I=8 J=9 K=10 L=11
    p = parse_dna('LJLJJ')   # LJL then 'J'(=9) 'J'(=9) → color override, no flagellum
    assert p.color_override == (9, 9)
    assert p.body_parts.get('flagellum', 0) == 0


# ── Reset / head marker (LLL) ─────────────────────────────────────────────────

def test_head_marker_flag_set():
    p = parse_dna('LLL')
    assert p.has_head_marker is True


def test_head_marker_false_without_lll():
    p = parse_dna(ANCESTOR)
    assert p.has_head_marker is False


# ── Conditional codons ────────────────────────────────────────────────────────

def test_conditional_creates_bonus_for_next_stat_codon():
    # ACE (if low_energy) → ABE (+1 motility): bonus stored, base stat also applied
    p = parse_dna('ACEABE')
    assert p.stats['motility'] == pytest.approx(2.0)  # base 1 + ABE
    assert len(p.conditional_bonuses) == 1
    cb = p.conditional_bonuses[0]
    assert cb.condition == 'low_energy'
    assert cb.stat_deltas == {'motility': pytest.approx(1.0)}


def test_effective_stats_without_condition():
    p = parse_dna('ACEABE')
    stats = p.effective_stats(set())
    assert stats['motility'] == pytest.approx(2.0)


def test_effective_stats_with_condition_active():
    p = parse_dna('ACEABE')
    stats = p.effective_stats({'low_energy'})
    assert stats['motility'] == pytest.approx(3.0)  # base + ABE + bonus


def test_effective_stats_wrong_condition_inactive():
    p = parse_dna('ACEABE')
    stats = p.effective_stats({'predator_nearby'})
    assert stats['motility'] == pytest.approx(2.0)  # bonus does not fire


def test_conditional_before_special_creates_no_bonus():
    # ACE then LKL (special): special consumes pending condition, no bonus
    p = parse_dna('ACELKL')
    assert p.conditional_bonuses == []


def test_junk_between_conditional_and_codon_cancels_bonus():
    # ACE then 'M'... wait, M is not in alphabet. Use a single letter that
    # forms only junk: 'A' alone (no 2-letter codon starts at pos 3 in 'ACEA')
    # 'ACEA' → ACE matches (pos 0–2), then 'A' is junk (no 2+ letter match).
    p = parse_dna('ACEAAEF')
    # After ACE: pending = low_energy. 'A' → junk, clears pending.
    # AEF fires normally without conditional.
    assert len(p.conditional_bonuses) == 0
    assert p.body_parts.get('spike', 0) == 1


def test_conditional_before_behavior_codon_consumed_no_bonus():
    # Behavior codons have no stat_deltas, so conditional produces no numeric bonus.
    p = parse_dna('ACECDE')  # ACE then CDE (aggressive)
    assert p.conditional_bonuses == []
    assert 'aggressive' in p.behaviors


def test_two_consecutive_conditionals_last_one_applies():
    # ACE then BDF then ABE:
    # ACE sets pending=low_energy; BDF encountered: pending exists but BDF has no stats
    # → pending cleared, pending set to predator_nearby; ABE: bonus for predator_nearby
    p = parse_dna('ACEBDFABE')
    assert len(p.conditional_bonuses) == 1
    assert p.conditional_bonuses[0].condition == 'predator_nearby'


def test_conditional_before_stopped_body_part_no_bonus():
    # ACE then LKL (stop) then ABE: special clears pending; body part ignored after stop
    p = parse_dna('ACELKLABE')
    assert p.conditional_bonuses == []
    assert p.body_parts.get('fin', 0) == 0


# ── Stat floors and caps ──────────────────────────────────────────────────────

def test_reproduction_threshold_floor_at_20():
    # 7 × CCC = −35 from base 50 = 15 → floored to 20
    p = parse_dna('CCC' * 7)
    assert p.stats['reproduction_threshold'] == pytest.approx(20.0)


def test_motility_floor_at_zero():
    # 3 × HHH = −1.5 motility from base 1.0 = −0.5 → floored to 0
    p = parse_dna('HHH' * 3)
    assert p.stats['motility'] == pytest.approx(0.0)


def test_shell_stat_deltas_applied():
    p = parse_dna('HHH')
    assert p.stats['defense'] == pytest.approx(3.0)  # base 1 + 2
    assert p.stats['motility'] == pytest.approx(0.5) # base 1 − 0.5


def test_kkk_body_mass_stats():
    p = parse_dna('KKK')
    assert p.stats['size']            == pytest.approx(4.0)   # base 3 + 1
    assert p.stats['energy_capacity'] == pytest.approx(120.0) # base 100 + 20


def test_fbl_tentacle_gives_two_stats():
    p = parse_dna('FBL')
    assert p.stats['sense_range'] == pytest.approx(2.0)  # base 1 + 1
    assert p.stats['cell_eat']    == pytest.approx(1.0)  # base 0 + 1


def test_stat_mod_eee_increases_max_age():
    p = parse_dna('EEE')
    assert p.stats['max_age'] == 250  # base 200 + 50 (int)


def test_stat_mod_ggg_increases_offspring_count():
    p = parse_dna('GGG')
    assert p.stats['offspring_count'] == 2  # base 1 + 1 (int)


def test_multiple_behaviors_can_coexist():
    p = parse_dna('CDEHIJ')  # aggressive + loner
    assert 'aggressive' in p.behaviors
    assert 'loner' in p.behaviors


def test_same_body_part_stacks():
    # Two AEF codons → spike count = 2, offense = base + 2
    p = parse_dna('AEFAEF')
    assert p.body_parts['spike'] == 2
    assert p.stats['offense'] == pytest.approx(3.0)  # base 1 + 2
