import re
from dataclasses import dataclass


@dataclass
class Token:
    kind: str
    lexeme: str
    line: int
    column: int


@dataclass
class LexResult:
    tokens: list
    errors: list


class Lexer:
    KEYWORDS = {
        "int", "float", "bool", "string",
        "if", "else", "while", "for",
        "return", "void", "true", "false", "print"
    }

    PATTERN = re.compile(
        r"(?P<SPACE>[ \t\r]+)|"
        r"(?P<NEWLINE>\n)|"
        r"(?P<COMMENT>//[^\n]*|/\*[\s\S]*?\*/)|"
        r'(?P<STRING>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|'
        r"(?P<FLOAT>(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)|"
        r"(?P<INTEGER>\d+)|"
        r"(?P<IDENTIFIER>[A-Za-z_][A-Za-z_0-9]*)|"
        r"(?P<OPERATOR>==|!=|<=|>=|&&|\|\||\+\+|--|[+\-*/%=<>!])|"
        r"(?P<PUNCT>[(){}\[\],;:.])"
    )

    def tokenize(self, source):
        tokens = []
        errors = []

        position = 0
        line = 1
        column = 1

        while position < len(source):
            match = self.PATTERN.match(source, position)

            if not match:
                character = source[position]

                errors.append(
                    f"Line {line}, column {column}: "
                    f"unexpected character {character!r}"
                )

                position += 1
                column += 1
                continue

            kind = match.lastgroup
            lexeme = match.group()

            start_line = line
            start_column = column

            position = match.end()

            if kind == "NEWLINE":
                line += 1
                column = 1
                continue

            if kind == "SPACE":
                column += len(lexeme)
                continue

            if kind == "COMMENT":
                newlines = lexeme.count("\n")

                if newlines:
                    line += newlines
                    column = len(lexeme.rsplit("\n", 1)[-1]) + 1
                else:
                    column += len(lexeme)

                continue

            if kind == "IDENTIFIER" and lexeme in self.KEYWORDS:
                kind = "KEYWORD"

            tokens.append(
                Token(kind, lexeme, start_line, start_column)
            )

            column += len(lexeme)

        tokens.append(Token("EOF", "$", line, column))

        return LexResult(tokens, errors)
