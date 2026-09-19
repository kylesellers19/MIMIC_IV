"""pytest wrapper over the frozen rule's synthetic test cases (scripts/test_note_phenotype.py).

The frozen file is a plain script and is NOT modified; its CASES list is imported
by parsing, so each case becomes one pytest test. Synthetic strings only.
"""
import ast, os
import pytest
from scripts.note_phenotype import classify_note

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "scripts", "test_note_phenotype.py")

def _cases():
    tree = ast.parse(open(_SRC).read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "CASES":
            return ast.literal_eval(node.value)
    raise RuntimeError("CASES not found")

@pytest.mark.parametrize("label,text,exp_a,exp_c", _cases(), ids=lambda v: v if isinstance(v, str) and len(v) < 60 else None)
def test_frozen_rule_case(label, text, exp_a, exp_c):
    r = classify_note(text)
    assert r["a_pos"] == exp_a, label
    assert r["c_hedged"] == exp_c, label
