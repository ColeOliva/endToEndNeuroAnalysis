from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

root = Path("data/raw/openneuro_candidate_1")
levels = json.load((root / "task-VisualOddball_events.json").open("r", encoding="utf-8"))["value"]["Levels"]

aggregate = Counter()
per_subject: dict[str, Counter] = {}

for events_path in sorted(root.glob("sub-*/eeg/*_events.tsv")):
    subject = events_path.parts[-3]
    reader = csv.DictReader(events_path.open("r", encoding="utf-8"), delimiter="\t")
    mapped = Counter(levels.get(row["value"], row["value"]) for row in reader)
    filtered = Counter({
        "Frequent_NonTarget": mapped.get("Frequent_NonTarget", 0),
        "Rare_Target": mapped.get("Rare_Target", 0),
    })
    per_subject[subject] = filtered
    aggregate.update(filtered)

summary = {
    "subjects_with_events": len(per_subject),
    "aggregate": dict(aggregate),
    "min_target": min((c["Rare_Target"] for c in per_subject.values()), default=0),
    "min_nontarget": min((c["Frequent_NonTarget"] for c in per_subject.values()), default=0),
    "subjects": sorted(per_subject.keys()),
}

print(json.dumps(summary, indent=2))
