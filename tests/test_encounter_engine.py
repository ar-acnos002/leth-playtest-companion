from collections import Counter
import random

import pytest
from leth.encounter_engine import EncounterEngine


@pytest.fixture
def engine():
    return EncounterEngine()


def combinations(engine):
    return [(q, m, s, e) for q, modes in engine.scene_pools.items()
            for m, scenes in modes.items() for s in scenes
            for e in engine.environment_pools]


def test_rules_load_and_resolve(engine):
    assert len(engine.encounters) == 76
    assert "FIND" in engine.scene_pools
    assert len(engine.environment_pools) == 9
    for modes in engine.scene_pools.values():
        for scenes in modes.values():
            for pool in scenes.values():
                assert all(eid in engine.encounters for eid in pool)
    for pool in engine.environment_pools.values():
        assert all(eid in engine.encounters for eid in pool)
    for context in combinations(engine):
        for eid in engine.eligible_ids(*context):
            assert engine.encounters[eid]["name"]
            assert engine.encounters[eid]["description"]


def test_every_combination(engine):
    empty = set()
    for q, m, s, e in combinations(engine):
        result = engine.roll(q, m, s, e, rng=random.Random(4))
        if result is None:
            assert engine.eligible_ids(q, m, s, e) == []
            empty.add((q, m, s, e))
        else:
            assert result["id"] in engine.scene_pools[q][m][s]
            assert result["id"] in engine.environment_pools[e]
            assert result == engine.encounters[result["id"]]
    assert {(m, s, e) for q, m, s, e in empty if q == "FIND"} == {(m, s, e) for m, s in [("TRAVEL", "CULMINATION"),
                     ("EXPLORE", "SETUP"), ("EXPLORE", "CULMINATION")]
                     for e in ("SETTLEMENT", "VILLAGE")}


def test_duplicate_weight_preserved(engine):
    engine.scene_pools["FIND"]["TRAVEL"]["SETUP"] = [2, 2, 2, 8, 1]
    engine.environment_pools["ROAD"] = [2, 8, 8]
    assert engine.eligible_ids("FIND", "TRAVEL", "SETUP", "ROAD") == [2, 2, 2, 8]
    rng = random.Random(42)
    counts = Counter(engine.roll("FIND", "TRAVEL", "SETUP", "ROAD", rng)["id"]
                     for _ in range(10000))
    assert 0.72 < counts[2] / 10000 < 0.78
