from __future__ import annotations

import argparse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

S3_BASE = "https://s3.amazonaws.com/openneuro.org"
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}


def list_s3_keys(prefix: str) -> list[str]:
    keys: list[str] = []
    marker = ""

    while True:
        marker_param = f"&marker={quote(marker)}" if marker else ""
        url = f"{S3_BASE}/?prefix={quote(prefix)}&max-keys=1000{marker_param}"
        root = ET.fromstring(urllib.request.urlopen(url, timeout=60).read())

        batch_keys = [k.find("s3:Key", NS).text for k in root.findall("s3:Contents", NS)]
        batch_keys = [k for k in batch_keys if k]
        keys.extend(batch_keys)

        truncated = root.find("s3:IsTruncated", NS)
        if truncated is None or truncated.text != "true" or not batch_keys:
            break
        marker = batch_keys[-1]

    return keys


def ensure_common_files(local_root: Path, dataset_prefix: str) -> None:
    common = [
        f"{dataset_prefix}/dataset_description.json",
        f"{dataset_prefix}/participants.tsv",
        f"{dataset_prefix}/participants.json",
        f"{dataset_prefix}/task-VisualOddball_events.json",
    ]

    for key in common:
        rel = Path("/".join(key.split("/")[1:]))
        out = local_root / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if not out.exists():
            urllib.request.urlretrieve(f"{S3_BASE}/{key}", out)


def discover_remote_subjects(dataset_prefix: str, task_name: str) -> list[str]:
    keys = list_s3_keys(f"{dataset_prefix}/sub-")
    subject_ids: set[str] = set()
    needle = f"_task-{task_name}_eeg.set"

    for key in keys:
        if "/eeg/" in key and key.endswith(needle):
            parts = key.split("/")
            for part in parts:
                if part.startswith("sub-"):
                    subject_ids.add(part)
                    break

    return sorted(subject_ids)


def local_subjects(local_root: Path) -> set[str]:
    return {p.name for p in local_root.glob("sub-*") if p.is_dir()}


def download_subject(local_root: Path, dataset_prefix: str, subject: str) -> int:
    keys = list_s3_keys(f"{dataset_prefix}/{subject}/eeg/")
    downloaded = 0
    for key in keys:
        rel = Path("/".join(key.split("/")[1:]))
        out = local_root / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            continue
        urllib.request.urlretrieve(f"{S3_BASE}/{key}", out)
        downloaded += 1
    return downloaded


def main() -> int:
    parser = argparse.ArgumentParser(description="Download a small OpenNeuro subject subset")
    parser.add_argument("--dataset-prefix", default="ds007056")
    parser.add_argument("--task-name", default="VisualOddball")
    parser.add_argument("--target-count", type=int, default=10)
    parser.add_argument("--local-root", default="data/raw/openneuro_candidate_1")
    args = parser.parse_args()

    local_root = Path(args.local_root)
    local_root.mkdir(parents=True, exist_ok=True)

    ensure_common_files(local_root, args.dataset_prefix)

    remote = discover_remote_subjects(args.dataset_prefix, args.task_name)
    existing = local_subjects(local_root)
    to_add = [sub for sub in remote if sub not in existing][: args.target_count]

    print(f"Remote subjects discovered: {len(remote)}")
    print(f"Existing local subjects: {len(existing)}")
    print(f"Subjects to download ({len(to_add)}): {to_add}")

    total_files = 0
    for subject in to_add:
        count = download_subject(local_root, args.dataset_prefix, subject)
        total_files += count
        print(f"Downloaded {count} files for {subject}")

    final_subjects = sorted(local_subjects(local_root))
    print(f"Final local subjects ({len(final_subjects)}): {final_subjects}")
    print(f"Total new files downloaded: {total_files}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
