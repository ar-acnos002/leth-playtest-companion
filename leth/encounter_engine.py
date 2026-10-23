"""Rules loading and weighted encounter selection."""
import json
from pathlib import Path
import random

RULES_DIR = Path(__file__).resolve().parent.parent / "rules"
ALTERNATIVES = ("Quiet Beat", "Redirect", "Misdirect")


class EncounterEngine:
    def __init__(self, rules_dir=RULES_DIR):
        def read(name):
            return json.loads((Path(rules_dir) / name).read_text(encoding="utf-8"))
        glossary = read("encounters.json")["encounters"]
        self.encounters = {item["id"]: item for item in glossary}
        if len(self.encounters) != len(glossary):
            raise ValueError("Duplicate glossary IDs")
        self.scene_pools = read("scene_pools.json")["pools"]
        self.environment_pools = read("environment_pools.json")["pools"]
        pools = list(self.environment_pools.values())
        pools += [pool for modes in self.scene_pools.values()
                  for scenes in modes.values() for pool in scenes.values()]
        if any(item not in self.encounters for pool in pools for item in pool):
            raise ValueError("Pool references an unknown encounter ID")

    def eligible_ids(self, quest_type, mode, scene_type, environment):
        scene = self.scene_pools[quest_type][mode][scene_type]
        allowed = set(self.environment_pools[environment])
        # Filter the original sequence so repetitions retain their weight.
        return [item for item in scene if item in allowed]

    def roll(self, quest_type, mode, scene_type, environment, rng=None):
        eligible = self.eligible_ids(quest_type, mode, scene_type, environment)
        if not eligible:
            return None
        return dict(self.encounters[(rng or random).choice(eligible)])
