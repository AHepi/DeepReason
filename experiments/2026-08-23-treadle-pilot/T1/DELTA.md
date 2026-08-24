# Docs Verify Delta

| Document:Line | Subject | Disposition |
|---|---|---|
| CON-run-identity.md:200 | `git log -M --diff-filter=R --name-status --format= -- experiments/live_research_2026-07-29/selfstudy/runs/ | grep -o 'runs/[a-z0-9-]*run-9175f0ecb055e57455af3c50df153c5a/run-manifest.json' | sort -u | tr '\n' ' ' | grep -qx 'runs/failed-epoch1-run-9175f0ecb055e57455af3c50df153c5a/run-manifest.json runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a/run-manifest.json runs/run-9175f0ecb055e57455af3c50df153c5a/run-manifest.json '` | baseline |
| CON-run-identity.md:202 | `git log -1 --format=%s 1637e808 | grep -qi retire` | baseline |
| CON-run-identity.md:204 | `test -z "$(git show -M --diff-filter=R --name-status --format= f304fec1)" && git log -1 --format=%s f304fec1 | grep -qi "retire.*epoch3" && git show --name-status --format= 6a8758a5 -- experiments/live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a/run-manifest.json | grep -q "^A"` | baseline |

**Total:** 3 failed

The baseline already records these three as pre‑existing `CON-run-identity.md` git‑history failures, so they are accounted for as “baseline”.
