from dataclasses import dataclass
from collections import deque


@dataclass
class LRTable:
    states: list
    action: dict
    goto: dict
    conflicts: list
    productions: list
    start_augmented: str
    mode: str


def production_list(grammar):
    return [
        (lhs, tuple(rhs))
        for lhs, alternatives in grammar.productions.items()
        for rhs in alternatives
    ]


def closure_lr0(items, productions, nonterminals):
    items = set(items)
    changed = True

    while changed:
        changed = False

        for production_index, dot in list(items):
            lhs, rhs = productions[production_index]

            if dot < len(rhs) and rhs[dot] in nonterminals:
                next_nonterminal = rhs[dot]

                for index, (candidate_lhs, _) in enumerate(productions):
                    item = (index, 0)

                    if candidate_lhs == next_nonterminal and item not in items:
                        items.add(item)
                        changed = True

    return frozenset(items)


def goto_lr0(items, symbol, productions, nonterminals):
    moved = {
        (index, dot + 1)
        for index, dot in items
        if dot < len(productions[index][1])
        and productions[index][1][dot] == symbol
    }

    if not moved:
        return frozenset()

    return closure_lr0(moved, productions, nonterminals)


def closure_lr1(items, productions, nonterminals, grammar):
    first = grammar.first_sets()
    items = set(items)
    changed = True

    while changed:
        changed = False

        for index, dot, lookahead in list(items):
            lhs, rhs = productions[index]

            if dot >= len(rhs) or rhs[dot] not in nonterminals:
                continue

            next_nonterminal = rhs[dot]
            beta = rhs[dot + 1:] + (lookahead,)

            lookaheads = grammar.first_of_sequence(beta, first) - {"ε"}

            for candidate_index, (candidate_lhs, _) in enumerate(productions):
                if candidate_lhs != next_nonterminal:
                    continue

                for new_lookahead in lookaheads:
                    item = (candidate_index, 0, new_lookahead)

                    if item not in items:
                        items.add(item)
                        changed = True

    return frozenset(items)


def goto_lr1(items, symbol, productions, nonterminals, grammar):
    moved = {
        (index, dot + 1, lookahead)
        for index, dot, lookahead in items
        if dot < len(productions[index][1])
        and productions[index][1][dot] == symbol
    }

    if not moved:
        return frozenset()

    return closure_lr1(moved, productions, nonterminals, grammar)


def build_table(grammar, mode):
    augmented = grammar.start + "__START__"

    while augmented in grammar.nonterminals:
        augmented += "_"

    productions = [
        (augmented, (grammar.start,))
    ] + production_list(grammar)

    nonterminals = grammar.nonterminals | {augmented}
    symbols = grammar.terminals | grammar.nonterminals

    if mode in {"LR(0)", "SLR(1)"}:
        initial = closure_lr0(
            {(0, 0)}, productions, nonterminals
        )

        closure = closure_lr0
        transition_function = lambda state, symbol: goto_lr0(
            state, symbol, productions, nonterminals
        )

    else:
        initial = closure_lr1(
            {(0, 0, "$")}, productions, nonterminals, grammar
        )

        transition_function = lambda state, symbol: goto_lr1(
            state, symbol, productions, nonterminals, grammar
        )

    states = [initial]
    indexes = {initial: 0}
    queue = deque([initial])
    transitions = {}

    while queue:
        state = queue.popleft()
        state_index = indexes[state]

        for symbol in symbols:
            target = transition_function(state, symbol)

            if not target:
                continue

            if target not in indexes:
                indexes[target] = len(states)
                states.append(target)
                queue.append(target)

            transitions[(state_index, symbol)] = indexes[target]

    if mode == "LALR(1)":
        core_indexes = {}
        merged_states = []
        old_to_new = {}

        for old_index, state in enumerate(states):
            core = frozenset(
                (item[0], item[1]) for item in state
            )

            if core not in core_indexes:
                core_indexes[core] = len(merged_states)
                merged_states.append(set())

            new_index = core_indexes[core]
            old_to_new[old_index] = new_index
            merged_states[new_index].update(state)

        states = [
            frozenset(state)
            for state in merged_states
        ]

        transitions = {
            (old_to_new[source], symbol): old_to_new[target]
            for (source, symbol), target in transitions.items()
        }

    action = {}
    goto = {}
    conflicts = []

    def add_action(key, value):
        if key in action and action[key] != value:
            message = (
                f"{mode} conflict at state {key[0]}, "
                f"symbol {key[1]}: {action[key]} / {value}"
            )

            if message not in conflicts:
                conflicts.append(message)
        else:
            action[key] = value

    follow = grammar.follow_sets()

    for state_index, state in enumerate(states):
        for item in state:
            if len(item) == 3:
                production_index, dot, lookahead = item
            else:
                production_index, dot = item
                lookahead = None

            lhs, rhs = productions[production_index]

            if dot < len(rhs):
                symbol = rhs[dot]

                if symbol not in nonterminals:
                    target = transitions.get((state_index, symbol))

                    if target is not None:
                        add_action(
                            (state_index, symbol),
                            ("shift", target)
                        )

            elif production_index == 0:
                add_action(
                    (state_index, "$"),
                    ("accept",)
                )

            else:
                if lookahead is not None:
                    lookaheads = {lookahead}
                elif mode == "SLR(1)":
                    lookaheads = follow[lhs]
                else:
                    lookaheads = grammar.terminals | {"$"}

                for terminal in lookaheads:
                    add_action(
                        (state_index, terminal),
                        ("reduce", production_index)
                    )

        for nonterminal in grammar.nonterminals:
            target = transitions.get((state_index, nonterminal))

            if target is not None:
                goto[(state_index, nonterminal)] = target

    return LRTable(
        states, action, goto, conflicts,
        productions, augmented, mode
    )


def build_lr0_table(grammar):
    return build_table(grammar, "LR(0)")


def build_slr_table(grammar):
    return build_table(grammar, "SLR(1)")


def build_lr1_table(grammar):
    return build_table(grammar, "LR(1)")


def build_lalr_table(grammar):
    return build_table(grammar, "LALR(1)")


def parse_lr(table, tokens):
    input_tokens = list(tokens) + ["$"]

    states = [0]
    symbols = []
    index = 0
    trace = []

    for _ in range(10000):
        lookahead = (
            input_tokens[index]
            if index < len(input_tokens)
            else "$"
        )

        state = states[-1]
        action = table.action.get((state, lookahead))

        row = {
            "states": " ".join(map(str, states)),
            "symbols": " ".join(symbols),
            "input": " ".join(input_tokens[index:]),
            "action": ""
        }

        trace.append(row)

        if action is None:
            row["action"] = (
                f"ERROR: no action for state {state}, "
                f"lookahead {lookahead}"
            )
            break

        if action[0] == "accept":
            row["action"] = "accept"
            break

        if action[0] == "shift":
            row["action"] = f"shift {lookahead}, state {action[1]}"
            symbols.append(lookahead)
            states.append(action[1])
            index += 1
            continue

        if action[0] == "reduce":
            production_index = action[1]
            lhs, rhs = table.productions[production_index]

            row["action"] = (
                f"reduce {lhs} -> {' '.join(rhs) if rhs else 'ε'}"
            )

            if rhs:
                if len(rhs) > len(symbols):
                    row["action"] = "ERROR: invalid reduction length"
                    break

                del symbols[-len(rhs):]
                del states[-len(rhs):]

            symbols.append(lhs)

            destination = table.goto.get((states[-1], lhs))

            if destination is None:
                row["action"] += " (missing GOTO)"
                break

            states.append(destination)

    else:
        trace.append({
            "states": "",
            "symbols": "",
            "input": "",
            "action": "Stopped at parser step limit"
        })

    return trace
