from dataclasses import dataclass
from .grammar import EPSILON, END


@dataclass
class LL1Table:
    entries: dict
    conflicts: list
    first: dict
    follow: dict


def build_ll1_table(grammar):
    first = grammar.first_sets()
    follow = grammar.follow_sets()

    entries = {}
    conflicts = []

    for lhs, alternatives in grammar.productions.items():
        for production in alternatives:
            selection = grammar.first_of_sequence(
                production, first
            )

            lookaheads = selection - {EPSILON}

            if EPSILON in selection:
                lookaheads |= follow[lhs]

            for terminal in lookaheads:
                key = (lhs, terminal)

                if key in entries and entries[key] != production:
                    conflicts.append(
                        f"Conflict at M[{lhs}, {terminal}]: "
                        f"{entries[key]} / {production}"
                    )
                else:
                    entries[key] = production

    return LL1Table(entries, conflicts, first, follow)


def parse_ll1(grammar, table, tokens, panic_mode=True):
    input_tokens = list(tokens) + [END]
    stack = [END, grammar.start]

    index = 0
    trace = []
    errors = []

    for _ in range(10000):
        if not stack:
            break

        top = stack[-1]
        lookahead = (
            input_tokens[index]
            if index < len(input_tokens)
            else END
        )

        row = {
            "stack": " ".join(stack),
            "input": " ".join(input_tokens[index:]),
            "action": ""
        }

        trace.append(row)

        if top == END and lookahead == END:
            row["action"] = "accept"
            break

        if top not in grammar.nonterminals:
            if top == lookahead:
                stack.pop()
                index += 1
                row["action"] = f"match {top}"
            else:
                errors.append(
                    f"Expected {top}, found {lookahead}"
                )

                if not panic_mode:
                    break

                if lookahead != END:
                    index += 1
                else:
                    stack.pop()

                row["action"] = "panic-mode recovery"

            continue

        production = table.entries.get((top, lookahead))

        if production is None:
            errors.append(
                f"No rule for {top} with lookahead {lookahead}"
            )

            if not panic_mode:
                break

            if lookahead in table.follow.get(top, {END}) or lookahead == END:
                stack.pop()
            else:
                index += 1

            row["action"] = "panic-mode recovery"
            continue

        stack.pop()

        for symbol in reversed(production):
            if symbol != EPSILON:
                stack.append(symbol)

        row["action"] = (
            f"{top} -> {' '.join(production) if production else EPSILON}"
        )

    else:
        errors.append("Stopped at the parser step limit.")

    return trace, errors
