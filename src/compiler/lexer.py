import re
from typing import List, Optional
from .tokens import TokenType, Token

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.current_pos = 0
        self.line = 1
        self.column = 1
        self.indent_stack = [0]  # Stack to track indentation levels
        
        # Regex patterns
        self.token_specs = [
            ('NUMBER',     r'\d+'),
            ('ID',         r'[A-Za-z_]\w*'),
            ('STRING',     r'"[^"]*"'),
            ('OP',         r'==|!=|<=|>=|[+\-*/=<>()\:,]'),
            ('NEWLINE',    r'\n'),
            ('SKIP',       r'[ \t]+'),
            ('MISMATCH',   r'.'),
        ]
        self.token_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in self.token_specs)
        self.get_token = re.compile(self.token_regex).match

    def tokenize(self) -> List[Token]:
        lines = self.source.split('\n')
        
        for line_num, line_content in enumerate(lines, 1):
            stripped_line = line_content.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue  # Skip empty lines and comments
            
            # Handle Indentation
            indent_level = len(line_content) - len(line_content.lstrip())
            
            if indent_level > self.indent_stack[-1]:
                self.indent_stack.append(indent_level)
                self.tokens.append(Token(TokenType.INDENT, indent_level, line_num, 1))
            
            while indent_level < self.indent_stack[-1]:
                self.indent_stack.pop()
                self.tokens.append(Token(TokenType.DEDENT, indent_level, line_num, 1))
            
            if indent_level != self.indent_stack[-1]:
                raise SyntaxError(f"Indentation Error on line {line_num}")

            # Tokenize the line content
            pos = indent_level
            while pos < len(line_content):
                match = self.get_token(line_content, pos)
                if not match:
                     raise SyntaxError(f"Unexpected character '{line_content[pos]}' on line {line_num}")
                
                kind = match.lastgroup
                value = match.group(kind)
                
                if kind == 'NUMBER':
                    self.tokens.append(Token(TokenType.NUMBER, int(value), line_num, pos + 1))
                elif kind == 'ID':
                    # Check for keywords
                    keywords = {
                        'def': TokenType.DEF, 'if': TokenType.IF, 'else': TokenType.ELSE,
                        'while': TokenType.WHILE, 'return': TokenType.RETURN, 'print': TokenType.PRINT
                    }
                    token_type = keywords.get(value, TokenType.IDENTIFIER)
                    self.tokens.append(Token(token_type, value, line_num, pos + 1))
                elif kind == 'STRING':
                    self.tokens.append(Token(TokenType.STRING, value.strip('"'), line_num, pos + 1))
                elif kind == 'OP':
                    op_map = {
                        '+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.MULTIPLY, '/': TokenType.DIVIDE,
                        '=': TokenType.ASSIGN, '==': TokenType.EQ, '!=': TokenType.NEQ,
                        '<': TokenType.LT, '>': TokenType.GT, '<=': TokenType.LTE, '>=': TokenType.GTE,
                        '(': TokenType.LPAREN, ')': TokenType.RPAREN, ':': TokenType.COLON, ',': TokenType.COMMA
                    }
                    self.tokens.append(Token(op_map[value], value, line_num, pos + 1))
                elif kind == 'NEWLINE':
                    pass # Should not match here as we process line by line, but good for safety
                elif kind == 'SKIP':
                    pass
                elif kind == 'MISMATCH':
                    raise SyntaxError(f"Unexpected character '{value}' on line {line_num}")
                
                pos = match.end()
            
            self.tokens.append(Token(TokenType.NEWLINE, '\\n', line_num, pos + 1))

        # End of file dedentation
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, 0, line_num + 1 if lines else 1, 1))
            
        self.tokens.append(Token(TokenType.EOF, '', line_num + 1 if lines else 1, 1))
        
        return self.tokens
