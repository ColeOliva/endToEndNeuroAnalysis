# Data Manifest

Purpose: record exactly which dataset version was used so analyses are reproducible.

## Locked Dataset Record
- Dataset source: OpenNeuro
- Dataset accession/identifier: ds007056
- Dataset title: PURSUE P300 Visual Oddball
- Download URL: https://s3.amazonaws.com/openneuro.org/ds007056/
- Dataset page: https://openneuro.org/datasets/ds007056/versions/1.1.1
- Date downloaded: 2026-02-19
- Local BIDS root: data/raw/openneuro_candidate_1
- Version/tag/release: 1.1.1
- DOI: 10.18112/openneuro.ds007056.v1.1.1
- Subject inclusion criteria (current slice): 17 subjects (sub-1001, sub-1002, sub-1004, sub-1005, sub-1006, sub-1007, sub-1008, sub-1009, sub-1010, sub-1011, sub-1013, sub-1014, sub-1015, sub-1016, sub-1017, sub-1018, sub-1020)
- Subject exclusions and reasons: remaining dataset subjects not yet ingested to keep compute/storage moderate during baseline development
- Run/session exclusions and reasons: none within the ingested slice
- Label column used for decoding: value
- Label mapping source: task-VisualOddball_events.json -> value.Levels
- Final classes included (current slice): Frequent_NonTarget, Rare_Target
- Aggregate class counts (17 subjects): Frequent_NonTarget=2432, Rare_Target=609
- Minimum per-subject class counts: Frequent_NonTarget=82, Rare_Target=19
- Notes on known issues: events.tsv uses coded numeric values; semantic labels require mapping from task-VisualOddball_events.json

## Integrity Checks
- dataset_description.json present: yes
- participants.tsv present: yes
- events.tsv present for all included runs: yes
- channels.tsv/electrodes.tsv present where expected: channels.tsv yes for all included runs

## Provenance Log
- 2026-02-19: Initialized manifest template.
- 2026-02-19: Locked dataset to ds007056 v1.1.1 and ingested initial BIDS slice (metadata + sub-1001 EEG).
- 2026-02-19: Expanded ingestion to a 17-subject EEG slice and recomputed aggregate class-balance statistics.
