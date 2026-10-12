from dataclasses import dataclass

EPSILON = "ε"
END = "$"


@dataclass
class Grammar:
    productions: dict
    start: str

    @classmethod
    def from_text(cls, text):
        productions = {}

        for line_number, raw_line in enumerate(text.splitlines(), 1):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            if "->" not in line:
                raise ValueError(
                    f"Line {line_number}: expected '->'"
                )

            lhs, rhs = map(str.strip, line.split("->", 1))

            if not lhs:
                raise ValueError(
                    f"Line {line_number}: missing left-hand side"
                )

            productions.setdefault(lhs, [])

            for alternative in rhs.split("|"):
                alternative = alternative.strip()

                if alternative.lower() in {"", "ε", "epsilon"}:
                    production = ()
                else:
                    production = tuple(alternative.split())

                productions[lhs].append(production)

        if not productions:
            raise ValueError("No grammar productions were entered.")

        return cls(productions, next(iter(productions)))

    @property
    def nonterminals(self):
        return set(self.productions)

    @property
    def terminals(self):
        result = set()

        for alternatives in self.productions.values():
            for production in alternatives:
                for symbol in production:
                    if symbol not in self.productions:
                        result.add(symbol)

        return result

    def __str__(self):
        lines = []

        for lhs, alternatives in self.productions.items():
            rhs = [
                " ".join(p) if p else EPSILON
                for p in alternatives
            ]

            lines.append(f"{lhs} -> " + " | ".join(rhs))

        return "\n".join(lines)

    def nullable(self):
        result = set()
        changed = True

        while changed:
            changed = False

            for lhs, alternatives in self.productions.items():
                for production in alternatives:
                    if not production or all(
                        symbol in result for symbol in production
                    ):
                        if lhs not in result:
                            result.add(lhs)
                            changed = True
                        break

        return result

    def first_sets(self):
        first = {
            nonterminal: set()
            for nonterminal in self.nonterminals
        }

        changed = True

        while changed:
            changed = False

            for lhs, alternatives in self.productions.items():
                for production in alternatives:
                    before = len(first[lhs])

                    if not production:
                        first[lhs].add(EPSILON)
                    else:
                        all_nullable = True

                        for symbol in production:
                            if symbol in self.nonterminals:
                                first[lhs] |= first[symbol] - {EPSILON}

                                if EPSILON not in first[symbol]:
                                    all_nullable = False
                                    break
                            else:
                                first[lhs].add(symbol)
                                all_nullable = False
                                break

                        if all_nullable:
                            first[lhs].add(EPSILON)

                    if len(first[lhs]) != before:
                        changed = True

        return first

    def first_of_sequence(self, sequence, first=None):
        first = first or self.first_sets()

        if not sequence:
            return {EPSILON}

        result = set()

        for symbol in sequence:
            if symbol in self.nonterminals:
                result |= first[symbol] - {EPSILON}

                if EPSILON not in first[symbol]:
                    return result
            else:
                result.add(symbol)
                return result

        result.add(EPSILON)
        return result

    def follow_sets(self):
        first = self.first_sets()

        follow = {
            nonterminal: set()
            for nonterminal in self.nonterminals
        }

        follow[self.start].add(END)

        changed = True

        while changed:
            changed = False

            for lhs, alternatives in self.productions.items():
                for production in alternatives:
                    for index, symbol in enumerate(production):
                        if symbol not in self.nonterminals:
                            continue

                        suffix = production[index + 1:]

                        suffix_first = self.first_of_sequence(
                            suffix, first
                        )

                        before = len(follow[symbol])

                        follow[symbol] |= suffix_first - {EPSILON}

                        if EPSILON in suffix_first:
                            follow[symbol] |= follow[lhs]

                        if len(follow[symbol]) != before:
                            changed = True

        return follow

    def eliminate_direct_left_recursion(self):
        result = {}

        for lhs, alternatives in self.productions.items():
            recursive = [
                p[1:] for p in alternatives
                if p and p[0] == lhs
            ]

            ordinary = [
                p for p in alternatives
                if not (p and p[0] == lhs)
            ]

            if not recursive:
                result[lhs] = list(alternatives)
                continue

            if not ordinary:
                raise ValueError(
                    f"{lhs} has left recursion but no "
                    "non-recursive alternative."
                )

            helper = lhs + "'"

            while helper in self.productions or helper in result:
                helper += "'"

            result[lhs] = [
                production + (helper,)
                for production in ordinary
            ]

            result[helper] = [
                production + (helper,)
                for production in recursive
            ] + [()]

        return Grammar(result, self.start)

    def left_factor(self):
        result = {
            lhs: list(alternatives)
            for lhs, alternatives in self.productions.items()
        }

        for lhs in list(result):
            groups = {}

            for production in result[lhs]:
                if production:
                    groups.setdefault(production[0], []).append(production)

            group = next(
                (g for g in groups.values() if len(g) > 1),
                None
            )

            if not group:
                continue

            prefix_length = 0
            shortest = min(map(len, group))

            while (
                prefix_length < shortest
                and len({
                    p[prefix_length] for p in group
                }) == 1
            ):
                prefix_length += 1

            prefix = group[0][:prefix_length]

            helper = lhs + "_fact"

            while helper in result:
                helper += "_"

            remaining = [
                p for p in result[lhs] if p not in group
            ]

            remaining.append(prefix + (helper,))
            result[lhs] = remaining

            result[helper] = [
                p[prefix_length:] for p in group
            ]

        return Grammar(result, self.start)
