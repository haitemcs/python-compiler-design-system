from compiler_frontend.lexer import Lexer


def test_basic_tokens():
    result = Lexer().tokenize("int age = 12;")

    assert not result.errors
    assert result.tokens[0].kind == "KEYWORD"
    assert result.tokens[1].lexeme == "age"
    assert result.tokens[-1].kind == "EOF"


def test_invalid_character():
    result = Lexer().tokenize("int x = @;")

    assert result.errors
