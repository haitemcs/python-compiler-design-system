import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPlainTextEdit, QTabWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QMessageBox,
    QHeaderView
)

from compiler_frontend.lexer import Lexer
from compiler_frontend.grammar import Grammar
from compiler_frontend.symbol_table import Symbol, SymbolTable
from compiler_frontend.ll1 import build_ll1_table, parse_ll1
from compiler_frontend.lr import (
    build_lr0_table, build_slr_table,
    build_lr1_table, build_lalr_table, parse_lr
)


SOURCE = """int age = 19;
float price = 12.5;
age = age + 1;
"""

GRAMMAR = """E -> E + T | T
T -> T * F | F
F -> ( E ) | id
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Compiler Front-End Simulator")
        self.resize(1250, 850)

        self.symbols = SymbolTable()

        self.source = QPlainTextEdit(SOURCE)
        self.grammar = QPlainTextEdit(GRAMMAR)
        self.parser_input = QPlainTextEdit("id + id * id")

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)

        self.tabs = QTabWidget()

        overview = QWidget()
        layout = QVBoxLayout(overview)

        layout.addWidget(QLabel("SOURCE CODE"))
        layout.addWidget(self.source)

        lex_button = QPushButton("Run Lexical Analysis")
        lex_button.clicked.connect(self.run_lexer)
        layout.addWidget(lex_button)

        layout.addWidget(QLabel("CONTEXT-FREE GRAMMAR"))
        layout.addWidget(self.grammar)

        layout.addWidget(QLabel("Parser input (space-separated tokens)"))
        layout.addWidget(self.parser_input)

        button_layout = QHBoxLayout()

        buttons = [
            ("FIRST / FOLLOW", self.run_first_follow),
            ("LL(1)", self.run_ll1),
            ("LR(0)", self.run_lr0),
            ("SLR(1)", self.run_slr),
            ("LR(1)", self.run_lr1),
            ("LALR(1)", self.run_lalr),
            ("Grammar Tools", self.run_transforms),
        ]

        for text, callback in buttons:
            button = QPushButton(text)
            button.clicked.connect(callback)
            button_layout.addWidget(button)

        layout.addLayout(button_layout)
        layout.addWidget(QLabel("ANALYSIS OUTPUT"))
        layout.addWidget(self.output)

        self.tabs.addTab(overview, "Compiler Workbench")

        self.token_table = QTableWidget(0, 4)
        self.token_table.setHorizontalHeaderLabels(
            ["Lexeme", "Token", "Line", "Column"]
        )
        self.token_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabs.addTab(self.token_table, "Tokens")

        self.symbol_widget = QTableWidget(0, 5)
        self.symbol_widget.setHorizontalHeaderLabels(
            ["Name", "Category", "Type", "Scope", "Line"]
        )
        self.symbol_widget.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabs.addTab(self.symbol_widget, "Symbol Table")

        self.setCentralWidget(self.tabs)
        self.statusBar().showMessage("Ready")

        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #20242b;
                color: #e6eaf0;
                font-size: 13px;
            }
            QPlainTextEdit, QTableWidget {
                background-color: #15191f;
                color: #e6eaf0;
                border: 1px solid #414957;
                selection-background-color: #315f91;
            }
            QPushButton {
                background-color: #315f91;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4079b5;
            }
            QTabBar::tab {
                background-color: #303640;
                padding: 9px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background-color: #315f91;
            }
        """)

    def get_grammar(self):
        return Grammar.from_text(self.grammar.toPlainText())

    def show_output(self, title, lines):
        self.output.setPlainText(
            title + "\n" + "=" * len(title) + "\n" +
            "\n".join(map(str, lines))
        )
        self.tabs.setCurrentIndex(0)

    def run_lexer(self):
        result = Lexer().tokenize(self.source.toPlainText())

        self.symbols.clear()

        self.token_table.setRowCount(0)
        self.symbol_widget.setRowCount(0)

        for token in result.tokens:
            row = self.token_table.rowCount()
            self.token_table.insertRow(row)

            values = [
                token.lexeme, token.kind,
                str(token.line), str(token.column)
            ]

            for col, value in enumerate(values):
                self.token_table.setItem(
                    row, col, QTableWidgetItem(value)
                )

            if token.kind == "IDENTIFIER":
                self.symbols.add(
                    Symbol(
                        token.lexeme,
                        line=token.line,
                        column=token.column
                    )
                )

        for symbol in self.symbols.all_symbols():
            row = self.symbol_widget.rowCount()
            self.symbol_widget.insertRow(row)

            values = [
                symbol.name, symbol.category, symbol.data_type,
                symbol.scope, str(symbol.line)
            ]

            for col, value in enumerate(values):
                self.symbol_widget.setItem(
                    row, col, QTableWidgetItem(value)
                )

        lines = [
            f"Tokens: {len(result.tokens) - 1}",
            f"Lexical errors: {len(result.errors)}",
            ""
        ]

        lines.extend(result.errors or ["No lexical errors."])

        self.show_output("Lexical Analysis", lines)

        self.tabs.setCurrentIndex(1)
        self.statusBar().showMessage(
            f"Lexical analysis completed: {len(result.errors)} error(s)"
        )

    def run_first_follow(self):
        try:
            grammar = self.get_grammar()

            lines = ["FIRST SETS"]

            for nt, values in sorted(grammar.first_sets().items()):
                lines.append(f"FIRST({nt}) = {{{', '.join(sorted(values))}}}")

            lines.append("")
            lines.append("FOLLOW SETS")

            for nt, values in sorted(grammar.follow_sets().items()):
                lines.append(f"FOLLOW({nt}) = {{{', '.join(sorted(values))}}}")

            self.show_output("FIRST and FOLLOW", lines)

        except Exception as error:
            self.show_error(error)

    def run_ll1(self):
        try:
            grammar = self.get_grammar()
            table = build_ll1_table(grammar)

            lines = [
                "CONFLICTS",
                *(table.conflicts or ["None"]),
                "",
                "PARSING TABLE"
            ]

            for (nt, terminal), production in sorted(table.entries.items()):
                rhs = " ".join(production) if production else "ε"
                lines.append(f"M[{nt}, {terminal}] = {nt} -> {rhs}")

            tokens = self.parser_input.toPlainText().split()

            trace, errors = parse_ll1(
                grammar, table, tokens, panic_mode=True
            )

            lines.extend(["", "PARSING TRACE"])

            for row in trace:
                lines.append(
                    f"{row['stack']:<25} | "
                    f"{row['input']:<25} | {row['action']}"
                )

            lines.extend(["", "ERRORS", *(errors or ["None"])])

            self.show_output("LL(1) Analysis", lines)

        except Exception as error:
            self.show_error(error)

    def run_lr_algorithm(self, builder, title):
        try:
            grammar = self.get_grammar()
            table = builder(grammar)

            lines = [
                f"Number of states: {len(table.states)}",
                "",
                "CONFLICTS",
                *(table.conflicts or ["None"]),
                "",
                "ITEM SETS"
            ]

            for index, state in enumerate(table.states):
                lines.append(f"\nI{index}:")

                for item in sorted(state, key=str):
                    if len(item) == 3:
                        pi, dot, lookahead = item
                    else:
                        pi, dot = item
                        lookahead = None

                    lhs, rhs = table.productions[pi]
                    body = list(rhs)
                    body.insert(dot, "·")

                    text = f"  {lhs} -> {' '.join(body)}"

                    if lookahead is not None:
                        text += f" , {lookahead}"

                    lines.append(text)

            lines.extend(["", "ACTION TABLE"])

            for key, value in sorted(table.action.items()):
                lines.append(f"ACTION[{key[0]}, {key[1]}] = {value}")

            lines.extend(["", "GOTO TABLE"])

            for key, value in sorted(table.goto.items()):
                lines.append(f"GOTO[{key[0]}, {key[1]}] = {value}")

            trace = parse_lr(
                table, self.parser_input.toPlainText().split()
            )

            lines.extend(["", "PARSING TRACE"])

            for row in trace:
                lines.append(
                    f"States: {row['states']} | "
                    f"Symbols: {row['symbols']} | "
                    f"Input: {row['input']} | "
                    f"{row['action']}"
                )

            self.show_output(title, lines)

        except Exception as error:
            self.show_error(error)

    def run_lr0(self):
        self.run_lr_algorithm(build_lr0_table, "LR(0) Analysis")

    def run_slr(self):
        self.run_lr_algorithm(build_slr_table, "SLR(1) Analysis")

    def run_lr1(self):
        self.run_lr_algorithm(build_lr1_table, "Canonical LR(1) Analysis")

    def run_lalr(self):
        self.run_lr_algorithm(build_lalr_table, "LALR(1) Analysis")

    def run_transforms(self):
        try:
            grammar = self.get_grammar()

            direct = grammar.eliminate_direct_left_recursion()
            factored = grammar.left_factor()

            self.show_output(
                "Grammar Transformations",
                [
                    "ORIGINAL GRAMMAR",
                    str(grammar),
                    "",
                    "DIRECT LEFT RECURSION ELIMINATION",
                    str(direct),
                    "",
                    "LEFT FACTORING",
                    str(factored)
                ]
            )

        except Exception as error:
            self.show_error(error)

    def show_error(self, error):
        QMessageBox.critical(
            self, "Analysis Error", str(error)
        )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

