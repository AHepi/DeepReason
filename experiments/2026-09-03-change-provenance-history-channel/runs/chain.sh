#!/bin/bash
# FULLY SERIAL chain: exactly ONE deepreason process at a time.
#
# The 429s that cost M3-C0 its full qualification (17 of 300 cases,
# ENDPOINT_HTTP_429, 11 of 15 pairs qualified -> shallow tier -> full reasoning
# refused) came from running five provider workloads at once. Serial removes
# the cause rather than hoping a lower number is low enough, and it is what the
# operator's "prefer a run complete" asks for: if the budget ends mid-chain,
# the measurements already finished are whole.
#
# Order is by what gates the SPEC: M1 first (H0 then H1), then M3.
set -u
cd /home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel/runs
A=/home/user/DeepReason/experiments/2026-09-03-change-provenance-history-channel/runs
P=experiments/2026-09-03-change-provenance-history-channel/runs

wait_idle () {
  while [ "$(ps -eo args 2>/dev/null | grep -cE '[d]eepreason (reason|qualify)')" -gt 0 ]; do sleep 30; done
}

echo "### chain start $(date -u +%FT%TZ)"
wait_idle
echo "### H0 already running or done; waiting for its log to say finished"
until grep -q "arm M1-H0 finished" m1_h0.log 2>/dev/null; do sleep 30; done
H0ROOT=$(ls -dt home-default/runs/run-* 2>/dev/null | head -1)
echo "### H0 FINISHED root=$H0ROOT $(date -u +%FT%TZ)"

if [ -n "$H0ROOT" ]; then
  wait_idle
  echo "### launching H1 $(date -u +%FT%TZ)"
  ./arm.sh $P/home-h1 M1-H1 conjecturer "$A/$H0ROOT" > m1_h1.log 2>&1
  echo "### H1 done rc=$? -- M1 COMPLETE $(date -u +%FT%TZ)"
else
  echo "### H0 produced no root; M1 cannot complete. Not starting H1 with nothing to inject."
fi

wait_idle
echo "### relaunching C0 (its first attempt died on 429-induced shallow tier) $(date -u +%FT%TZ)"
./arm.sh $P/home-c0 M3-C0 none > m3_c0.log 2>&1
echo "### C0 done rc=$? $(date -u +%FT%TZ)"
C0ROOT=$(ls -dt home-c0/runs/run-* 2>/dev/null | head -1)
if [ -n "$C0ROOT" ]; then
  wait_idle
  echo "### launching C1 root=$C0ROOT $(date -u +%FT%TZ)"
  ./arm.sh $P/home-c1 M3-C1 critic "$A/$C0ROOT" > m3_c1.log 2>&1
  echo "### C1 done rc=$? -- M3 COMPLETE $(date -u +%FT%TZ)"
else
  echo "### C0 produced no root; M3 cannot complete."
fi
echo "### chain finished $(date -u +%FT%TZ)"
