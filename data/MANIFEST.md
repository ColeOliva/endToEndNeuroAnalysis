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
- Subject inclusion criteria (current slice): sub-1001 only (initial ingestion for pipeline validation)
- Subject exclusions and reasons: all other subjects temporarily excluded to keep first ingestion lightweight
- Run/session exclusions and reasons: none within sub-1001 initial slice
- Label column used for decoding: value
- Label mapping source: task-VisualOddball_events.json -> value.Levels
- Final classes included (current slice): Frequent_NonTarget, Rare_Target
- Observed class counts (sub-1001): Frequent_NonTarget=168, Rare_Target=42
- Notes on known issues: events.tsv uses coded numeric values; semantic labels require mapping from task-VisualOddball_events.json

## Integrity Checks
- dataset_description.json present: yes
- participants.tsv present: yes
- events.tsv present for included run: yes
- channels.tsv/electrodes.tsv present where expected: channels.tsv yes for included run

## Provenance Log
- 2026-02-19: Initialized manifest template.
- 2026-02-19: Locked dataset to ds007056 v1.1.1 and ingested initial BIDS slice (metadata + sub-1001 EEG).
