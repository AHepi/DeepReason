#!/bin/sh
# RED-then-GREEN for every differential this tranche added, as commands rather
# than claims. A containment test you cannot make fail proves nothing.
#
# The mutation is applied to a COPY of src/ in a temporary directory and
# reached through PYTHONPATH; the repository's own src/ is never written to.
# That matters here beyond tidiness: every module these mutations touch except
# sandbox_os.py is inside frozen surface 3 (`verification/`), and this lane
# holds no grant to edit one even transiently.
#
# Each mutation prints three things:
#   RED     the differential failing against the weakened subject,
#   STILL   the CONFESSION the differential replaced, still true under the same
#           mutation -- which is the whole argument for the conversion,
#   GREEN   the same differential passing against the real subject.
set -e

REPO=$(cd "$(dirname "$0")/../../.." && pwd)
cd "$REPO"

mutate() {  # mutate <python-fragment-on-stdin>; echoes the mutated PYTHONPATH root
    MUT=$(mktemp -d)
    cp -r "$REPO/src" "$MUT/src"
    python - "$MUT" || { rm -rf "$MUT"; exit 1; }
    echo "$MUT"
}

run_red() {  # run_red <pythonpath-root> <pytest args...>
    root=$1; shift
    PYTHONPATH="$root/src" python -m pytest "$@" -q 2>&1 | tail -6 || true
}

echo "== BASELINE: the real subject, all three ring files =========================="
PYTHONPATH="$REPO/src" python -m pytest tests/test_sandbox_guard.py \
    tests/test_contained_simulation_runner.py \
    tests/test_simulation_runner_default.py -q 2>&1 | tail -3

########################################################################
echo
echo "== M1: the contained backend's probe drops --net ============================="
echo "   (containment_prefix() still returns a prefix, so the backend still"
echo "    believes it is contained and still reports so.)"
MUT=$(mktemp -d); cp -r "$REPO/src" "$MUT/src"
python - "$MUT" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]) / "src/deepreason/verification/contained.py"
t = p.read_text()
old = 'for flags in (("--map-root-user", "--net"), ("--net",)):'
assert t.count(old) == 1
p.write_text(t.replace(old, 'for flags in (("--map-root-user",),):'))
PY
echo "--- RED expected ---"
run_red "$MUT" tests/test_sandbox_guard.py -k "contained_backend_prefix_actually_denies"
echo "--- STILL TRUE under the same mutation: the confessions this replaced ---"
PYTHONPATH="$MUT/src" python -c "
from deepreason.verification.contained import ContainedSimulationBackend as B
b = B(toolchain_id='t', maximum_wall_ms=20000, maximum_memory_bytes=512*1024*1024)
print('  containment_prefix()          ->', B.containment_prefix())
print('  resource_limits()[\"network\"]   ->', b.resource_limits()['network'])
print('  fingerprint()[\"network_denial\"]->', b.fingerprint()['network_denial'])
assert b.resource_limits()['network'] is False
assert b.fingerprint()['network_denial'] == 'namespace_unshared'
print('  both self-reports UNCHANGED while the network is reachable')
"
echo "--- and the code-testing differential stays GREEN: separate probe ---"
run_red "$MUT" tests/test_sandbox_guard.py -k "network_namespace_actually_denies"
rm -rf "$MUT"
echo "--- GREEN restored ---"
PYTHONPATH="$REPO/src" python -m pytest tests/test_sandbox_guard.py -q \
    -k "contained_backend_prefix_actually_denies" 2>&1 | tail -2

########################################################################
echo
echo "== M2: the launch drops the probed prefix from the worker argv =============="
MUT=$(mktemp -d); cp -r "$REPO/src" "$MUT/src"
python - "$MUT" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]) / "src/deepreason/verification/contained.py"
t = p.read_text()
old = '[*prefix, sys.executable, "worker.py"],'
assert t.count(old) == 1
p.write_text(t.replace(old, '[sys.executable, "worker.py"],'))
PY
echo "--- RED expected ---"
run_red "$MUT" tests/test_sandbox_guard.py -k "argv_really_carries"
echo "--- STILL TRUE: the label the launch no longer earns ---"
PYTHONPATH="$MUT/src" python -c "
from deepreason.verification.contained import ContainedSimulationBackend as B
b = B(toolchain_id='t', maximum_wall_ms=20000, maximum_memory_bytes=512*1024*1024)
print('  fingerprint()[\"network_denial\"]->', b.fingerprint()['network_denial'])
print('  resource_limits()[\"network\"]   ->', b.resource_limits()['network'])
"
echo "--- and M1's network differential stays GREEN: it probes the prefix, not the launch ---"
run_red "$MUT" tests/test_sandbox_guard.py -k "contained_backend_prefix_actually_denies"
rm -rf "$MUT"
echo "--- GREEN restored ---"
PYTHONPATH="$REPO/src" python -m pytest tests/test_sandbox_guard.py -q \
    -k "argv_really_carries" 2>&1 | tail -2

########################################################################
echo
echo "== M3: _apply_containment_limits stops applying RLIMIT_NOFILE ==============="
MUT=$(mktemp -d); cp -r "$REPO/src" "$MUT/src"
python - "$MUT" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]) / "src/deepreason/verification/contained.py"
t = p.read_text()
old = '    resource.setrlimit(resource.RLIMIT_NOFILE, (limits["nofile"], limits["nofile"]))\n'
assert t.count(old) == 1
p.write_text(t.replace(old, ""))
PY
echo "--- RED expected ---"
run_red "$MUT" tests/test_sandbox_guard.py -k "every_declared_rlimit"
echo "--- STILL TRUE: the retired self-to-self comparison ---"
PYTHONPATH="$MUT/src" python -c "
from deepreason.verification.contained import ContainedSimulationBackend as B, _containment_limits
b = B(toolchain_id='t', maximum_wall_ms=20000, maximum_memory_bytes=512*1024*1024)
rep = b.resource_limits()
lim = _containment_limits(maximum_wall_ms=20000, maximum_memory_bytes=512*1024*1024)
same = [k for k in ('cpu_seconds','memory_bytes','fsize_bytes','nofile','nproc') if rep[k] == lim[k]]
print('  resource_limits()[k] == _containment_limits()[k] for', same)
print('  -- the old assertion, unmoved, while the child no longer gets NOFILE')
"
rm -rf "$MUT"
echo "--- GREEN restored ---"
PYTHONPATH="$REPO/src" python -m pytest tests/test_sandbox_guard.py -q \
    -k "every_declared_rlimit" 2>&1 | tail -2

########################################################################
echo
echo "== M4: the ephemeral scratch directory stops being removed =================="
MUT=$(mktemp -d); cp -r "$REPO/src" "$MUT/src"
python - "$MUT" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]) / "src/deepreason/verification/contained.py"
t = p.read_text()
old = "            shutil.rmtree(scratch, ignore_errors=True)"
assert t.count(old) == 1
p.write_text(t.replace(old, "            pass  # mutation: the scratch dir survives"))
PY
echo "--- RED expected ---"
run_red "$MUT" tests/test_sandbox_guard.py -k "scratch_directory_is_the_cwd"
echo "--- STILL TRUE: the string that claims the confinement ---"
PYTHONPATH="$MUT/src" python -c "
from deepreason.verification.contained import ContainedSimulationBackend as B
b = B(toolchain_id='t', maximum_wall_ms=20000, maximum_memory_bytes=512*1024*1024)
print('  resource_limits()[\"filesystem\"] ->', repr(b.resource_limits()['filesystem']))
"
rm -rf "$MUT"
echo "--- GREEN restored ---"
PYTHONPATH="$REPO/src" python -m pytest tests/test_sandbox_guard.py -q \
    -k "scratch_directory_is_the_cwd" 2>&1 | tail -2

########################################################################
echo
echo "== M5: the launch stops passing env=, so the worker inherits ours ==========="
MUT=$(mktemp -d); cp -r "$REPO/src" "$MUT/src"
python - "$MUT" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]) / "src/deepreason/verification/contained.py"
t = p.read_text()
old = "                    env=_contained_environment(scratch),\n"
assert t.count(old) == 1
p.write_text(t.replace(old, ""))
PY
echo "--- RED expected ---"
run_red "$MUT" tests/test_sandbox_guard.py -k "contained_worker_environment_reaches"
echo "--- STILL GREEN: the allowlist test, which asserts the dict, not the child ---"
run_red "$MUT" tests/test_contained_simulation_runner.py -k "worker_environment_is_a_fixed_allowlist"
rm -rf "$MUT"
echo "--- GREEN restored ---"
PYTHONPATH="$REPO/src" python -m pytest tests/test_sandbox_guard.py -q \
    -k "contained_worker_environment_reaches" 2>&1 | tail -2

########################################################################
echo
echo "== M6: the code-testing worker environment keeps OLLAMA_API_KEY ============="
MUT=$(mktemp -d); cp -r "$REPO/src" "$MUT/src"
python - "$MUT" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]) / "src/deepreason/oracle_sandbox.py"
t = p.read_text()
old = '        "VIRTUAL_ENV",\n    )'
assert t.count(old) == 1
p.write_text(t.replace(old, '        "VIRTUAL_ENV",\n        "OLLAMA_API_KEY",\n    )'))
PY
echo "--- RED expected ---"
run_red "$MUT" tests/test_sandbox_guard.py -k "code_testing_worker_environment_reaches"
rm -rf "$MUT"
echo "--- GREEN restored ---"
PYTHONPATH="$REPO/src" python -m pytest tests/test_sandbox_guard.py -q \
    -k "code_testing_worker_environment_reaches" 2>&1 | tail -2

########################################################################
echo
echo "== M7: the code-testing channel's own probe drops --net ====================="
MUT=$(mktemp -d); cp -r "$REPO/src" "$MUT/src"
python - "$MUT" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]) / "src/deepreason/sandbox_os.py"
t = p.read_text()
old = '''_CANDIDATE_FLAGS: tuple[tuple[str, ...], ...] = (
    ("--map-root-user", "--net"),
    ("--net",),
)'''
assert t.count(old) == 1
p.write_text(t.replace(old, '''_CANDIDATE_FLAGS: tuple[tuple[str, ...], ...] = (
    ("--map-root-user",),
)'''))
PY
echo "--- RED expected ---"
run_red "$MUT" tests/test_sandbox_guard.py -k "network_namespace_actually_denies"
rm -rf "$MUT"
echo "--- GREEN restored ---"
PYTHONPATH="$REPO/src" python -m pytest tests/test_sandbox_guard.py -q \
    -k "network_namespace_actually_denies" 2>&1 | tail -2

########################################################################
echo
echo "== V: the vacuity guard, on a host that really has only loopback ============"
echo "   The whole pytest process runs inside an unshared network namespace, so"
echo "   the OUTSIDE arm sees ['lo'] and there is nothing to deny. A two-armed"
echo "   differential must SKIP there. The one-armed form the tree carried until"
echo "   this tranche PASSES there, measuring nothing."
echo "--- the two differentials, inside a lo-only namespace ---"
/usr/bin/unshare --map-root-user --net -- env PYTHONPATH="$REPO/src" \
    python -m pytest tests/test_sandbox_guard.py -q -rs \
    -k "denies_network" 2>&1 | tail -6 || true
echo "--- the retired one-armed assertion, in the same namespace ---"
/usr/bin/unshare --map-root-user --net -- env PYTHONPATH="$REPO/src" python -c "
import json, socket, subprocess, sys
from deepreason.sandbox_os import network_denial_prefix
probe = ('import json, socket\n'
         \"print(json.dumps({'interfaces': sorted(n for _i, n in socket.if_nameindex())}))\n\")
inside = json.loads(subprocess.run([*network_denial_prefix(), sys.executable, '-c', probe],
                                   capture_output=True, text=True, check=True).stdout)
assert inside['interfaces'] == ['lo']
print('  one-armed assertion inside[\"interfaces\"] == [\"lo\"]: PASSED, vacuously')
" || true
