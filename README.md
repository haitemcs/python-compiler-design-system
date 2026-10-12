# Compiler Front-End Simulator

Educational compiler-design project implemented in Python.

## Features
- Lexical analysis and token positions
- Lexical error reporting
- Identifier symbol table
- Context-free grammar representation
- Nullable, FIRST and FOLLOW
- Direct left-recursion elimination
- Basic left factoring
- LL(1) parsing table and predictive parsing trace
- LR(0) item sets
- SLR(1) parsing
- Canonical LR(1) item sets and parsing
- LALR(1) state merging and parsing
- Conflict reporting
- Panic-mode recovery for LL(1)
- PySide6 graphical interface
- Automated tests

## Run on Ubuntu

    cd ~/complier_system
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    python main.py

## Run tests

    python -m pip install pytest
    pytest -q

## Grammar format

    E -> E + T | T
    T -> T * F | F
    F -> ( E ) | id

Separate symbols with spaces. Use `ε` or `epsilon` for an empty production.

This is an educational implementation. Indirect left-recursion elimination,
complete normal-form conversion, and a full recursive-descent generator
remain possible extensions.
# python-compiler-design-system
