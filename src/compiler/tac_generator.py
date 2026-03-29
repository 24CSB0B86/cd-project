"""
Three Address Code (TAC) Generator for Mini-Python Compiler
Translates the AST (after semantic analysis) into intermediate representation.
Week 8 Implementation

Three Address Code format:
    result = arg1 op arg2    (binary operations)
    result = op arg1         (unary operations)
    result = arg1            (copy / assignment)
    LABEL label_name:        (branch targets)
    GOTO label_name          (unconditional jump)
    IF_FALSE result GOTO label_name   (conditional jump)
    PARAM arg                (push function argument)
    result = CALL func, n    (call function with n args)
    RETURN result            (return from function)
    PRINT arg                (output)
"""

from typing import List, Optional, Tuple
from enum import Enum, auto
from dataclasses import dataclass, field
from .ast_nodes import (
    Program, Statement, Expression, Block,
    Assignment, IfStatement, WhileStatement, FunctionDef,
    ReturnStatement, PrintStatement,
    BinaryOp, UnaryOp, Identifier, Literal, FunctionCall
)


# ============================================================================
# TAC Operation Codes
# ============================================================================

class TACOp(Enum):
    """Enumeration of all Three Address Code operation codes"""
    # Data movement
    ASSIGN   = "ASSIGN"    # t = a

    # Arithmetic
    ADD      = "ADD"       # t = a + b
    SUB      = "SUB"       # t = a - b
    MUL      = "MUL"       # t = a * b
    DIV      = "DIV"       # t = a / b
    NEG      = "NEG"       # t = -a

    # Comparison
    EQ       = "EQ"        # t = a == b
    NEQ      = "NEQ"       # t = a != b
    LT       = "LT"        # t = a < b
    GT       = "GT"        # t = a > b
    LTE      = "LTE"       # t = a <= b
    GTE      = "GTE"       # t = a >= b

    # Control flow
    LABEL    = "LABEL"     # LABEL name:
    GOTO     = "GOTO"      # GOTO label
    IF_FALSE = "IF_FALSE"  # IF_FALSE cond GOTO label

    # Functions
    FUNC_BEGIN = "FUNC_BEGIN"  # FUNC_BEGIN name
    FUNC_END   = "FUNC_END"    # FUNC_END name
    PARAM    = "PARAM"     # PARAM arg  (push argument before CALL)
    CALL     = "CALL"      # result = CALL func n_args
    RETURN   = "RETURN"    # RETURN value

    # I/O
    PRINT    = "PRINT"     # PRINT arg


# ============================================================================
# TAC Instruction
# ============================================================================

@dataclass
class TACInstruction:
    """
    A single Three Address Code instruction.

    Formats:
        - Binary op:   op=ADD, result='t1', arg1='a', arg2='b'  → t1 = a + b
        - Unary op:    op=NEG, result='t1', arg1='x'            → t1 = -x
        - Assign:      op=ASSIGN, result='x', arg1='5'          → x = 5
        - Label:       op=LABEL, result='L1'                    → L1:
        - Goto:        op=GOTO, arg1='L2'                       → goto L2
        - If_false:    op=IF_FALSE, arg1='cond', arg2='L3'      → if_false cond goto L3
        - Param:       op=PARAM, arg1='a'                       → param a
        - Call:        op=CALL, result='t2', arg1='foo', arg2=3 → t2 = call foo, 3
        - Return:      op=RETURN, arg1='t3'                     → return t3
        - Print:       op=PRINT, arg1='x'                       → print x
        - FuncBegin:   op=FUNC_BEGIN, result='name'             → func_begin name
        - FuncEnd:     op=FUNC_END, result='name'               → func_end name
    """
    op: TACOp
    result: Optional[str] = None
    arg1: Optional[str] = None
    arg2: Optional[str] = None

    def __str__(self) -> str:
        """Human-readable TAC instruction"""
        op = self.op

        if op == TACOp.LABEL:
            return f"{self.result}:"
        elif op == TACOp.FUNC_BEGIN:
            return f"func_begin {self.result}"
        elif op == TACOp.FUNC_END:
            return f"func_end {self.result}"
        elif op == TACOp.GOTO:
            return f"    goto {self.arg1}"
        elif op == TACOp.IF_FALSE:
            return f"    if_false {self.arg1} goto {self.arg2}"
        elif op == TACOp.RETURN:
            if self.arg1:
                return f"    return {self.arg1}"
            return f"    return"
        elif op == TACOp.PRINT:
            return f"    print {self.arg1}"
        elif op == TACOp.PARAM:
            return f"    param {self.arg1}"
        elif op == TACOp.CALL:
            if self.result:
                return f"    {self.result} = call {self.arg1}, {self.arg2}"
            return f"    call {self.arg1}, {self.arg2}"
        elif op == TACOp.ASSIGN:
            return f"    {self.result} = {self.arg1}"
        elif op == TACOp.NEG:
            return f"    {self.result} = -{self.arg1}"
        else:
            # Binary arithmetic / comparison
            symbol_map = {
                TACOp.ADD: "+",  TACOp.SUB: "-",
                TACOp.MUL: "*",  TACOp.DIV: "/",
                TACOp.EQ:  "==", TACOp.NEQ: "!=",
                TACOp.LT:  "<",  TACOp.GT:  ">",
                TACOp.LTE: "<=", TACOp.GTE: ">=",
            }
            sym = symbol_map.get(op, op.value)
            return f"    {self.result} = {self.arg1} {sym} {self.arg2}"


# ============================================================================
# TAC Generator
# ============================================================================

class TACGenerator:
    """
    Generates Three Address Code from an AST.

    Usage:
        generator = TACGenerator()
        instructions = generator.generate(ast)
        print(generator.get_code())
    """

    def __init__(self):
        self.instructions: List[TACInstruction] = []
        self._temp_counter: int = 0
        self._label_counter: int = 0
        self._current_function: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, ast: Program) -> List[TACInstruction]:
        """
        Generate TAC for a complete program.

        Args:
            ast: The root Program AST node (must already be semantically valid)

        Returns:
            List of TACInstruction objects
        """
        self.instructions = []
        self._temp_counter = 0
        self._label_counter = 0
        self._current_function = None

        self.visit_program(ast)
        return self.instructions

    def get_code(self) -> str:
        """Return the TAC as a formatted, human-readable string"""
        lines = []
        for instr in self.instructions:
            lines.append(str(instr))
        return "\n".join(lines)

    def get_instruction_count(self) -> int:
        """Return total number of TAC instructions generated"""
        return len(self.instructions)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _new_temp(self) -> str:
        """Allocate a new temporary variable (t0, t1, t2, …)"""
        name = f"t{self._temp_counter}"
        self._temp_counter += 1
        return name

    def _new_label(self, prefix: str = "L") -> str:
        """Allocate a new unique label"""
        name = f"{prefix}{self._label_counter}"
        self._label_counter += 1
        return name

    def _emit(self, op: TACOp, result=None, arg1=None, arg2=None) -> TACInstruction:
        """Create and record a TAC instruction"""
        instr = TACInstruction(op=op, result=result, arg1=arg1, arg2=arg2)
        self.instructions.append(instr)
        return instr

    # ------------------------------------------------------------------
    # AST Visitor Methods – Statements
    # ------------------------------------------------------------------

    def visit_program(self, node: Program):
        """Visit the root program node"""
        for statement in node.statements:
            self.visit_statement(statement)

    def visit_statement(self, node: Statement):
        """Dispatch to the appropriate statement visitor"""
        if isinstance(node, Assignment):
            self.visit_assignment(node)
        elif isinstance(node, IfStatement):
            self.visit_if_statement(node)
        elif isinstance(node, WhileStatement):
            self.visit_while_statement(node)
        elif isinstance(node, FunctionDef):
            self.visit_function_def(node)
        elif isinstance(node, ReturnStatement):
            self.visit_return_statement(node)
        elif isinstance(node, PrintStatement):
            self.visit_print_statement(node)
        else:
            raise NotImplementedError(f"Unknown statement type: {type(node).__name__}")

    def visit_block(self, node: Block):
        """Visit a block of statements"""
        for statement in node.statements:
            self.visit_statement(statement)

    def visit_assignment(self, node: Assignment):
        """
        Generate TAC for:  target = expression
        Example:  x = a + b  →  t0 = a + b
                                 x = t0
        """
        value_place = self.visit_expression(node.value)
        self._emit(TACOp.ASSIGN, result=node.target, arg1=value_place)

    def visit_if_statement(self, node: IfStatement):
        """
        Generate TAC for if / if-else:

            if condition:           →  cond = <condition>
                then_block             if_false cond goto L_else
            else:                      <then_block>
                else_block             goto L_end
                                   L_else:
                                       <else_block>
                                   L_end:
        """
        # Allocate labels
        label_else = self._new_label("L_else")
        label_end  = self._new_label("L_end")

        # Evaluate condition
        cond_place = self.visit_expression(node.condition)

        # Branch on false
        self._emit(TACOp.IF_FALSE, arg1=cond_place, arg2=label_else)

        # Then block
        self.visit_block(node.then_block)

        if node.else_block:
            self._emit(TACOp.GOTO, arg1=label_end)

        # Else label
        self._emit(TACOp.LABEL, result=label_else)

        # Else block (if present)
        if node.else_block:
            self.visit_block(node.else_block)
            self._emit(TACOp.LABEL, result=label_end)

    def visit_while_statement(self, node: WhileStatement):
        """
        Generate TAC for while loop:

            while condition:        →  L_loop:
                body                       cond = <condition>
                                           if_false cond goto L_end
                                           <body>
                                           goto L_loop
                                       L_end:
        """
        label_loop = self._new_label("L_loop")
        label_end  = self._new_label("L_end")

        # Loop header label
        self._emit(TACOp.LABEL, result=label_loop)

        # Evaluate condition
        cond_place = self.visit_expression(node.condition)

        # Exit loop if condition is false
        self._emit(TACOp.IF_FALSE, arg1=cond_place, arg2=label_end)

        # Loop body
        self.visit_block(node.body)

        # Back-edge
        self._emit(TACOp.GOTO, arg1=label_loop)

        # Post-loop label
        self._emit(TACOp.LABEL, result=label_end)

    def visit_function_def(self, node: FunctionDef):
        """
        Generate TAC for function definition:

            def foo(a, b):          →  func_begin foo
                body                       (parameters are named directly)
                                           <body>
                                       func_end foo
        """
        prev_function = self._current_function
        self._current_function = node.name

        self._emit(TACOp.FUNC_BEGIN, result=node.name)
        # Parameters are referenced by name in the body; no explicit PARAM needed here
        self.visit_block(node.body)
        self._emit(TACOp.FUNC_END, result=node.name)

        self._current_function = prev_function

    def visit_return_statement(self, node: ReturnStatement):
        """
        Generate TAC for return statement.
        """
        if node.value:
            val_place = self.visit_expression(node.value)
            self._emit(TACOp.RETURN, arg1=val_place)
        else:
            self._emit(TACOp.RETURN)

    def visit_print_statement(self, node: PrintStatement):
        """
        Generate TAC for print statement.
        """
        val_place = self.visit_expression(node.expression)
        self._emit(TACOp.PRINT, arg1=val_place)

    # ------------------------------------------------------------------
    # AST Visitor Methods – Expressions
    # ------------------------------------------------------------------

    def visit_expression(self, node: Expression) -> str:
        """
        Visit an expression and return the *place* (variable or literal string)
        where its value is stored / represented.
        """
        if isinstance(node, BinaryOp):
            return self.visit_binary_op(node)
        elif isinstance(node, UnaryOp):
            return self.visit_unary_op(node)
        elif isinstance(node, Identifier):
            return self.visit_identifier(node)
        elif isinstance(node, Literal):
            return self.visit_literal(node)
        elif isinstance(node, FunctionCall):
            return self.visit_function_call(node)
        else:
            raise NotImplementedError(f"Unknown expression type: {type(node).__name__}")

    def visit_binary_op(self, node: BinaryOp) -> str:
        """
        Generate TAC for binary operations.
        Example:  a + b  →  t0 = a + b   (returns 't0')
        """
        left_place  = self.visit_expression(node.left)
        right_place = self.visit_expression(node.right)
        temp        = self._new_temp()

        op_map = {
            '+':  TACOp.ADD, '-':  TACOp.SUB,
            '*':  TACOp.MUL, '/':  TACOp.DIV,
            '==': TACOp.EQ,  '!=': TACOp.NEQ,
            '<':  TACOp.LT,  '>':  TACOp.GT,
            '<=': TACOp.LTE, '>=': TACOp.GTE,
        }

        tac_op = op_map.get(node.operator)
        if tac_op is None:
            raise ValueError(f"Unknown binary operator: {node.operator}")

        self._emit(tac_op, result=temp, arg1=left_place, arg2=right_place)
        return temp

    def visit_unary_op(self, node: UnaryOp) -> str:
        """
        Generate TAC for unary operations.
        Example:  -x  →  t0 = -x   (returns 't0')
        """
        operand_place = self.visit_expression(node.operand)
        temp = self._new_temp()
        self._emit(TACOp.NEG, result=temp, arg1=operand_place)
        return temp

    def visit_identifier(self, node: Identifier) -> str:
        """
        Identifier: just return the variable name as the place.
        No TAC instruction needed – it's already a named location.
        """
        return node.name

    def visit_literal(self, node: Literal) -> str:
        """
        Literal value: represent as a string constant (e.g. '42', '"hello"').
        """
        if isinstance(node.value, str):
            return f'"{node.value}"'
        return str(node.value)

    def visit_function_call(self, node: FunctionCall) -> str:
        """
        Generate TAC for a function call.

        Example:
            foo(a, a+b)  →
                t0 = a + b
                param a
                param t0
                t1 = call foo, 2      (returns 't1')
        """
        # Evaluate each argument and emit PARAM
        arg_places = []
        for arg in node.arguments:
            place = self.visit_expression(arg)
            arg_places.append(place)

        for place in arg_places:
            self._emit(TACOp.PARAM, arg1=place)

        temp = self._new_temp()
        n_args = str(len(node.arguments))
        self._emit(TACOp.CALL, result=temp, arg1=node.function_name, arg2=n_args)
        return temp
