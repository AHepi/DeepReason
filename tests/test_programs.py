"""programs.py's shared, content-evaluation-adjacent utilities."""

from deepreason.programs import is_pure_code


def test_is_pure_code_rejects_a_bare_function_definition():
    assert is_pure_code("def solve(x):\n    return x * 2") is True


def test_is_pure_code_rejects_a_bare_class_definition():
    assert is_pure_code("class Solver:\n    def solve(self, x):\n        return x * 2") is True


def test_is_pure_code_rejects_import_plus_def_with_nothing_else():
    assert is_pure_code("import math\ndef solve(x):\n    return math.floor(x)") is True


def test_is_pure_code_passes_real_prose():
    assert is_pure_code(
        "Doubling composes with addition the way multiplication by two does."
    ) is False


def test_is_pure_code_passes_a_bare_docstring():
    """A lone string literal is prose-as-a-string, not code (R57(a))."""
    assert is_pure_code('"""Doubling composes with addition."""') is False


def test_is_pure_code_passes_prose_quoting_code_inline():
    """Mixed prose and code is not valid Python syntax as a whole, so it
    never reaches the code-only-nodes branch at all (R57(a)'s protected
    case: an explanation that happens to mention/quote code)."""
    assert is_pure_code(
        "The mechanism is: def solve(x): return x*2. This shows doubling."
    ) is False


def test_is_pure_code_does_not_trip_on_bare_assignments():
    """Deliberately narrow (A6, SPEC.md Revision 3): a worked-example-style
    sequence of assignments with no def/class/import is NOT treated as
    pure code, to avoid a false positive on legitimate explanatory
    content that happens to parse as valid Python."""
    assert is_pure_code("x = 5\ny = 10\nz = x + y") is False


def test_is_pure_code_passes_empty_content():
    """Empty content is a different, already-enforced failure (the
    non-empty field requirement); is_pure_code itself is not the gate
    for emptiness."""
    assert is_pure_code("") is False
