"""
Test Suite for TAC Generator
Week 8 Implementation Tests
"""

import pytest
from src.compiler.lexer import Lexer
from src.compiler.parser import Parser
from src.compiler.semantic_analyzer import SemanticAnalyzer
from src.compiler.tac_generator import TACGenerator, TACOp, TACInstruction


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def generate_tac(code: str) -> TACGenerator:
    """Full pipeline: source → Lexer → Parser → SemanticAnalyzer → TACGenerator"""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    gen = TACGenerator()
    gen.generate(ast)
    return gen


def ops(gen: TACGenerator):
    """Extract just the list of TACOp values from a generator"""
    return [i.op for i in gen.instructions]


# ---------------------------------------------------------------------------
# Simple Assignment
# ---------------------------------------------------------------------------

class TestAssignment:

    def test_integer_literal_assignment(self):
        """x = 5  →  ASSIGN x 5"""
        gen = generate_tac("x = 5\n")
        assert TACOp.ASSIGN in ops(gen)
        assign = [i for i in gen.instructions if i.op == TACOp.ASSIGN][0]
        assert assign.result == "x"
        assert assign.arg1 == "5"

    def test_string_literal_assignment(self):
        """message = "hello"  →  ASSIGN with quoted string"""
        gen = generate_tac('message = "hello"\n')
        assign = [i for i in gen.instructions if i.op == TACOp.ASSIGN][0]
        assert assign.result == "message"
        assert '"hello"' in assign.arg1

    def test_variable_copy(self):
        """y = x  →  ASSIGN y x"""
        code = "x = 10\ny = x\n"
        gen = generate_tac(code)
        assigns = [i for i in gen.instructions if i.op == TACOp.ASSIGN]
        results = [a.result for a in assigns]
        assert "x" in results
        assert "y" in results


# ---------------------------------------------------------------------------
# Arithmetic Expressions
# ---------------------------------------------------------------------------

class TestArithmetic:

    def test_addition(self):
        """z = x + y  →  t0 = x + y ; z = t0"""
        code = "x = 3\ny = 4\nz = x + y\n"
        gen = generate_tac(code)
        assert TACOp.ADD in ops(gen)
        add_instr = [i for i in gen.instructions if i.op == TACOp.ADD][0]
        assert add_instr.arg1 == "x"
        assert add_instr.arg2 == "y"
        assert add_instr.result.startswith("t")

    def test_subtraction(self):
        code = "x = 10\ny = 3\nz = x - y\n"
        gen = generate_tac(code)
        assert TACOp.SUB in ops(gen)

    def test_multiplication(self):
        code = "x = 3\ny = 4\nz = x * y\n"
        gen = generate_tac(code)
        assert TACOp.MUL in ops(gen)

    def test_division(self):
        code = "x = 10\ny = 2\nz = x / y\n"
        gen = generate_tac(code)
        assert TACOp.DIV in ops(gen)

    def test_negation(self):
        """return -x  →  NEG instruction (parser supports unary minus in expressions)"""
        code = """\
def negate(x):
    return -x
"""
        gen = generate_tac(code)
        assert TACOp.NEG in ops(gen)
        neg_instr = [i for i in gen.instructions if i.op == TACOp.NEG][0]
        assert neg_instr.arg1 == "x"

    def test_nested_expression(self):
        """a + b * c  should produce multiple temporaries"""
        code = "a = 1\nb = 2\nc = 3\nresult = a + b * c\n"
        gen = generate_tac(code)
        # Should have at least one ADD and one MUL
        assert TACOp.ADD in ops(gen)
        assert TACOp.MUL in ops(gen)
        # Should have at least two temp vars
        temps = {i.result for i in gen.instructions if i.result and i.result.startswith("t")}
        assert len(temps) >= 2

    def test_temp_variable_naming(self):
        """Temporary variables should start with 't' and increment"""
        code = "x = 1\ny = 2\nz = 3\nr = x + y + z\n"
        gen = generate_tac(code)
        temps = sorted([i.result for i in gen.instructions
                        if i.result and i.result.startswith("t")])
        assert "t0" in temps


# ---------------------------------------------------------------------------
# Comparison Operators
# ---------------------------------------------------------------------------

class TestComparisons:
    """Comparisons are parsed only inside if/while conditions (parser limitation).
    We verify each comparison TACOp is generated via those constructs."""

    def test_equality(self):
        """EQ generated from if-condition  n == 0"""
        code = """\
x = 5
if x == 0:
    x = 1
"""
        gen = generate_tac(code)
        assert TACOp.EQ in ops(gen)

    def test_less_than(self):
        """LT generated from while-condition  i < 10"""
        code = """\
i = 0
while i < 10:
    i = i + 1
"""
        gen = generate_tac(code)
        assert TACOp.LT in ops(gen)

    def test_greater_than(self):
        """GT generated from if-condition  x > 0"""
        code = """\
x = 5
if x > 0:
    x = 0
"""
        gen = generate_tac(code)
        assert TACOp.GT in ops(gen)


# ---------------------------------------------------------------------------
# If / If-Else Statements
# ---------------------------------------------------------------------------

class TestIfStatements:

    def test_if_without_else(self):
        """if x == 0: ...  →  IF_FALSE + LABEL"""
        code = """\
x = 5
if x == 0:
    x = 1
"""
        gen = generate_tac(code)
        assert TACOp.IF_FALSE in ops(gen)
        assert TACOp.LABEL in ops(gen)
        # Should NOT have a GOTO (no else branch)
        if_instr = [i for i in gen.instructions if i.op == TACOp.IF_FALSE][0]
        assert if_instr.arg2.startswith("L")

    def test_if_with_else(self):
        """if-else  →  IF_FALSE + GOTO + two LABELs"""
        code = """\
x = 5
if x == 0:
    y = 1
else:
    y = 2
"""
        gen = generate_tac(code)
        assert TACOp.IF_FALSE in ops(gen)
        assert TACOp.GOTO in ops(gen)
        labels = [i for i in gen.instructions if i.op == TACOp.LABEL]
        assert len(labels) == 2

    def test_if_labels_are_unique(self):
        """Multiple if statements should use distinct labels"""
        code = """\
x = 1
if x == 1:
    y = 10
if x == 2:
    y = 20
"""
        gen = generate_tac(code)
        labels = [i.result for i in gen.instructions if i.op == TACOp.LABEL]
        assert len(labels) == len(set(labels)), "Labels must be unique"


# ---------------------------------------------------------------------------
# While Loops
# ---------------------------------------------------------------------------

class TestWhileLoops:

    def test_while_basic(self):
        """while loop  →  L_loop: ... IF_FALSE ... GOTO L_loop  L_end:"""
        code = """\
x = 10
while x > 0:
    x = x - 1
"""
        gen = generate_tac(code)
        assert TACOp.LABEL in ops(gen)
        assert TACOp.IF_FALSE in ops(gen)
        assert TACOp.GOTO in ops(gen)

    def test_while_produces_two_labels(self):
        """While loop needs a loop-start label and a loop-end label"""
        code = """\
i = 0
while i < 5:
    i = i + 1
"""
        gen = generate_tac(code)
        labels = [i for i in gen.instructions if i.op == TACOp.LABEL]
        assert len(labels) == 2

    def test_while_loop_structure_order(self):
        """Instruction order: LABEL → IF_FALSE → body → GOTO → LABEL"""
        code = """\
x = 3
while x > 0:
    x = x - 1
"""
        gen = generate_tac(code)
        label_idxs = [idx for idx, i in enumerate(gen.instructions) if i.op == TACOp.LABEL]
        goto_idx = next(idx for idx, i in enumerate(gen.instructions) if i.op == TACOp.GOTO)

        # First label (loop start) must come before GOTO
        assert label_idxs[0] < goto_idx
        # Second label (loop end) must come after GOTO
        assert label_idxs[1] > goto_idx


# ---------------------------------------------------------------------------
# Function Definitions
# ---------------------------------------------------------------------------

class TestFunctionDef:

    def test_function_boundaries(self):
        """Function should be wrapped in FUNC_BEGIN / FUNC_END"""
        code = """\
def add(a, b):
    return a + b
"""
        gen = generate_tac(code)
        assert TACOp.FUNC_BEGIN in ops(gen)
        assert TACOp.FUNC_END in ops(gen)

        begin = [i for i in gen.instructions if i.op == TACOp.FUNC_BEGIN][0]
        end   = [i for i in gen.instructions if i.op == TACOp.FUNC_END][0]
        assert begin.result == "add"
        assert end.result == "add"

    def test_function_return(self):
        """return statement  →  RETURN instruction"""
        code = """\
def square(n):
    return n * n
"""
        gen = generate_tac(code)
        assert TACOp.RETURN in ops(gen)

    def test_function_return_value(self):
        """Return should reference the computed temp"""
        code = """\
def double(x):
    return x + x
"""
        gen = generate_tac(code)
        ret_instr = [i for i in gen.instructions if i.op == TACOp.RETURN][0]
        assert ret_instr.arg1 is not None

    def test_factorial_function(self):
        """Factorial (recursive) TAC generation"""
        code = """\
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
"""
        gen = generate_tac(code)
        assert TACOp.FUNC_BEGIN in ops(gen)
        assert TACOp.IF_FALSE in ops(gen)
        assert TACOp.RETURN in ops(gen)
        assert TACOp.CALL in ops(gen)


# ---------------------------------------------------------------------------
# Function Calls
# ---------------------------------------------------------------------------

class TestFunctionCalls:

    def test_function_call_produces_param_and_call(self):
        """f(a, b)  →  param a ; param b ; t0 = call f, 2"""
        code = """\
def add(a, b):
    return a + b

x = 3
y = 4
result = add(x, y)
"""
        gen = generate_tac(code)
        assert TACOp.PARAM in ops(gen)
        assert TACOp.CALL in ops(gen)

        call_instr = [i for i in gen.instructions if i.op == TACOp.CALL][-1]
        assert call_instr.arg1 == "add"
        assert call_instr.arg2 == "2"

    def test_call_result_used_in_assign(self):
        """Result of function call stored in temp, then assigned to variable"""
        code = """\
def id(x):
    return x

r = id(42)
"""
        gen = generate_tac(code)
        call_instr = [i for i in gen.instructions if i.op == TACOp.CALL][-1]
        # call result (temp) must be used in a subsequent ASSIGN
        call_temp = call_instr.result
        assigns = [i for i in gen.instructions if i.op == TACOp.ASSIGN and i.arg1 == call_temp]
        assert len(assigns) >= 1

    def test_no_arg_call(self):
        """f()  →  t0 = call f, 0"""
        code = """\
def greet():
    return 1

r = greet()
"""
        gen = generate_tac(code)
        call_instr = [i for i in gen.instructions if i.op == TACOp.CALL][-1]
        assert call_instr.arg2 == "0"


# ---------------------------------------------------------------------------
# Print Statement
# ---------------------------------------------------------------------------

class TestPrint:

    def test_print_literal(self):
        code = 'print("hello")\n'
        gen = generate_tac(code)
        assert TACOp.PRINT in ops(gen)

    def test_print_variable(self):
        code = "x = 5\nprint(x)\n"
        gen = generate_tac(code)
        assert TACOp.PRINT in ops(gen)
        print_instr = [i for i in gen.instructions if i.op == TACOp.PRINT][0]
        assert print_instr.arg1 == "x"

    def test_print_expression(self):
        code = "x = 5\ny = 3\nprint(x + y)\n"
        gen = generate_tac(code)
        assert TACOp.ADD in ops(gen)
        assert TACOp.PRINT in ops(gen)


# ---------------------------------------------------------------------------
# Code Output / Formatting
# ---------------------------------------------------------------------------

class TestCodeOutput:

    def test_get_code_returns_string(self):
        gen = generate_tac("x = 42\n")
        code_str = gen.get_code()
        assert isinstance(code_str, str)
        assert len(code_str) > 0

    def test_get_instruction_count(self):
        gen = generate_tac("x = 1\ny = 2\nz = x + y\n")
        assert gen.get_instruction_count() > 0

    def test_instruction_str_format_assign(self):
        instr = TACInstruction(op=TACOp.ASSIGN, result="x", arg1="5")
        assert "x" in str(instr) and "5" in str(instr)

    def test_instruction_str_format_label(self):
        instr = TACInstruction(op=TACOp.LABEL, result="L0")
        assert "L0:" in str(instr)

    def test_instruction_str_format_goto(self):
        instr = TACInstruction(op=TACOp.GOTO, arg1="L1")
        assert "goto" in str(instr) and "L1" in str(instr)

    def test_instruction_str_format_if_false(self):
        instr = TACInstruction(op=TACOp.IF_FALSE, arg1="cond", arg2="L2")
        s = str(instr)
        assert "if_false" in s and "cond" in s and "L2" in s


# ---------------------------------------------------------------------------
# Full Pipeline Integration
# ---------------------------------------------------------------------------

class TestFullPipeline:

    def test_pipeline_simple(self):
        """Source → Lexer → Parser → Semantic → TAC (no exceptions)"""
        code = "x = 10\ny = x + 5\n"
        gen = generate_tac(code)
        assert gen.get_instruction_count() > 0

    def test_pipeline_factorial_full(self):
        """Full factorial pipeline"""
        code = """\
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

result = factorial(5)
"""
        gen = generate_tac(code)
        # Must contain all expected op types
        op_set = set(ops(gen))
        assert TACOp.FUNC_BEGIN in op_set
        assert TACOp.IF_FALSE  in op_set
        assert TACOp.RETURN    in op_set
        assert TACOp.CALL      in op_set
        assert TACOp.PARAM     in op_set
        assert TACOp.ASSIGN    in op_set

    def test_pipeline_while_program(self):
        """While loop integration"""
        code = """\
total = 0
i = 1
while i < 6:
    total = total + i
    i = i + 1
"""
        gen = generate_tac(code)
        op_set = set(ops(gen))
        assert TACOp.LABEL    in op_set
        assert TACOp.IF_FALSE in op_set
        assert TACOp.GOTO     in op_set
        assert TACOp.ADD      in op_set

    def test_unique_labels_across_program(self):
        """All labels in a program must be unique"""
        code = """\
x = 1
if x == 1:
    y = 2
while x < 5:
    x = x + 1
if x == 5:
    y = 3
"""
        gen = generate_tac(code)
        labels = [i.result for i in gen.instructions if i.op == TACOp.LABEL]
        assert len(labels) == len(set(labels))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
