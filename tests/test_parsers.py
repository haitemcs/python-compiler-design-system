from compiler_frontend.grammar import Grammar
from compiler_frontend.ll1 import build_ll1_table, parse_ll1
from compiler_frontend.lr import (
    build_slr_table, build_lr1_table,
    build_lalr_table, parse_lr
)


TEXT = """E -> E + T | T
T -> T * F | F
F -> ( E ) | id
"""


def test_first_follow():
    grammar = Grammar.from_text(TEXT)

    assert grammar.first_sets()["E"] == {"(", "id"}
    assert "$" in grammar.follow_sets()["E"]


def test_lr_parsers():
    grammar = Grammar.from_text(TEXT)

    for builder in (
        build_slr_table,
        build_lr1_table,
        build_lalr_table
    ):
        table = builder(grammar)

        assert not table.conflicts

        trace = parse_lr(
            table, ["id", "+", "id", "*", "id"]
        )

        assert trace[-1]["action"] == "accept"


def test_ll1_after_left_recursion_elimination():
    grammar = Grammar.from_text(TEXT)
    grammar = grammar.eliminate_direct_left_recursion()

    table = build_ll1_table(grammar)

    trace, errors = parse_ll1(
        grammar,
        table,
        ["id", "+", "id", "*", "id"],
        panic_mode=False
    )

    assert not errors
    assert trace[-1]["action"] == "accept"
