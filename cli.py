from compiler_frontend.lexer import Lexer
from compiler_frontend.grammar import Grammar
from compiler_frontend.lr import build_slr_table, parse_lr

source = """int age = 19;
age = age + 1;
"""

grammar_text = """E -> E + T | T
T -> T * F | F
F -> ( E ) | id
"""

print("\n=== LEXICAL ANALYSIS ===")

result = Lexer().tokenize(source)

for token in result.tokens:
    print(
        f"{token.line}:{token.column} "
        f"{token.kind:<12} {token.lexeme}"
    )

for error in result.errors:
    print("ERROR:", error)

print("\n=== GRAMMAR ===")

grammar = Grammar.from_text(grammar_text)
print(grammar)

print("\n=== FIRST ===")

for nt, values in grammar.first_sets().items():
    print(f"FIRST({nt}) = {values}")

print("\n=== FOLLOW ===")

for nt, values in grammar.follow_sets().items():
    print(f"FOLLOW({nt}) = {values}")

print("\n=== SLR(1) ===")

table = build_slr_table(grammar)

print("States:", len(table.states))
print("Conflicts:", table.conflicts or "None")

if not table.conflicts:
    trace = parse_lr(table, ["id", "+", "id", "*", "id"])

    for row in trace:
        print(row)

    print("Result:", trace[-1]["action"])
