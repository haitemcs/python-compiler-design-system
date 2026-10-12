from dataclasses import dataclass


@dataclass
class Symbol:
    name: str
    category: str = "identifier"
    data_type: str = "unknown"
    scope: str = "global"
    line: int = 0
    column: int = 0


class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def add(self, symbol):
        key = (symbol.scope, symbol.name)

        if key in self.symbols:
            return False

        self.symbols[key] = symbol
        return True

    def lookup(self, name, scope="global"):
        return (
            self.symbols.get((scope, name))
            or self.symbols.get(("global", name))
        )

    def all_symbols(self):
        return list(self.symbols.values())

    def clear(self):
        self.symbols.clear()
