"""Storage (spec §14): flat content-addressed JSON files + JSONL log, git-native.

Save = git commit. Sealed holdout blobs live in a ``holdout/`` namespace
excluded from pack rendering until their Reveal event (§10.5). The
refuted-index (embedding NN over refuted artifacts, §11.5) is rebuilt
deterministically from the log.
"""
