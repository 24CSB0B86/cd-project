from enum import Enum, auto

class TokenType(Enum):
    # Special
    EOF = auto()
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    
    # Identifiers & Literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    
    # Keywords
    DEF = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    RETURN = auto()
    PRINT = auto()
    
    # Operators & Delimiters
    PLUS = auto()          # +
    MINUS = auto()         # -
    MULTIPLY = auto()      # *
    DIVIDE = auto()        # /
    ASSIGN = auto()        # =
    EQ = auto()            # ==
    NEQ = auto()           # !=
    LT = auto()            # <
    GT = auto()            # >
    LTE = auto()           # <=
    GTE = auto()           # >=
    LPAREN = auto()        # (
    RPAREN = auto()        # )
    COLON = auto()         # :
    COMMA = auto()         # ,

class Token:
    def __init__(self, type: TokenType, value: str, line: int, column: int):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', Line:{self.line}, Col:{self.column})"
