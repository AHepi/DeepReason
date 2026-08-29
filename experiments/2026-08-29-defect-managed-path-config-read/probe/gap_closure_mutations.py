"""Plant one of the two gap-closure mutations, or restore with git checkout.

Usage: python probe/gap_closure_mutations.py {M8|M9}
  M8  `return None` as the first statement of
      preparation._load_operator_config -- reinstates P14 exactly.
  M9  delete change site 7, the config=load_config(...) line in
      cli.main._qualify_one_profile -- the operations-parity limb.
Restore: git checkout -- src/deepreason/preparation.py src/deepreason/cli/main.py
Deliberately OUTSIDE the cone it judges: it mutates src/, never tests/.
"""
import pathlib, sys

REPO = pathlib.Path(__file__).resolve().parents[3]

PREP = REPO / "src/deepreason/preparation.py"
MAIN = REPO / "src/deepreason/cli/main.py"

M8_OLD = '''    than a traceback out of yaml.
    """

    if config_path is None:'''
M8_NEW = '''    than a traceback out of yaml.
    """

    return None
    if config_path is None:'''
M9_LINE = '        config=load_config(Path(args.config)) if getattr(args, "config", None) else None,\n'

which = sys.argv[1]
if which == "M8":
    s = PREP.read_text()
    assert s.count(M8_OLD) == 1
    PREP.write_text(s.replace(M8_OLD, M8_NEW))
elif which == "M9":
    lines = MAIN.read_text().splitlines(keepends=True)
    assert lines.count(M9_LINE) == 1
    lines.remove(M9_LINE)
    MAIN.write_text("".join(lines))
else:
    raise SystemExit("unknown mutation")
print(f"{which} applied")
