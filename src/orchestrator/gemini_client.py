"""
Enhanced Gemini Compiler Agent
Integrates with the Context Provider for deep compiler state awareness.
Week 8 Implementation - Gemini API Integration & Context Injection
"""

import os
import logging
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Module-level logger (replaces debug prints)
logger = logging.getLogger(__name__)


# System prompt injected into every Gemini session
SYSTEM_PROMPT = """\
You are an Agentic AI Assistant integrated into a custom Mini-Python compiler.
Your role is to help users fix syntax, semantic, and security errors based on
the compiler's internal state.

RULES:
1. Analyze errors using the COMPILER CONTEXT provided (AST, Symbol Table, Diagnostics).
2. Explain WHY the error occurred, referencing the relevant grammar rule.
3. Suggest a concrete fix using a code block.
4. If the code uses dangerous patterns (eval, exec, __import__), flag it as a security risk.
5. Be conversational and encouraging, not robotic.

EBNF Grammar (Mini-Python subset):
  program     = { statement } ;
  statement   = assignment | if_stmt | while_stmt | func_def | print_stmt ;
  assignment  = identifier , "=" , expression , NEWLINE ;
  if_stmt     = "if" , condition , ":" , block , [ "else" , ":" , block ] ;
  while_stmt  = "while" , condition , ":" , block ;
  func_def    = "def" , identifier , "(" , [ params ] , ")" , ":" , block ;
  print_stmt  = "print" , "(" , expression , ")" , NEWLINE ;
  block       = NEWLINE , INDENT , { statement } , DEDENT ;
  expression  = term , { ( "+" | "-" ) , term } ;
  term        = factor , { ( "*" | "/" ) , factor } ;
  factor      = [ "-" ] , ( identifier | number | string | "(" , expression , ")" ) ;
  condition   = expression , comp_op , expression ;
  comp_op     = "==" | "!=" | "<" | ">" | "<=" | ">=" ;
"""


class GeminiCompilerAgent:
    """
    Enhanced Gemini AI agent with deep compiler context awareness.
    
    Capabilities:
    - Receives full compiler state (AST, Symbol Table, Errors) as context
    - Provides conversational error explanations
    - Suggests fixes grounded in the EBNF grammar
    - Handles API errors gracefully
    """

    def __init__(self):
        """Initialize the Gemini agent with secure API configuration."""
        self.model = None
        self.chat = None
        self._initialized = False

        key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("MODEL_NAME", "models/gemini-2.5-flash")

        if not key:
            logger.error("GEMINI_API_KEY is not set in .env")
            return

        key = key.strip()
        logger.info(f"API key loaded ({key[:5]}...{key[-4:]})")

        try:
            genai.configure(api_key=key)
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            return

        # Dynamic model selection with fallback
        target_model = model_name
        try:
            available = [
                m.name for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods
            ]
            if target_model not in available and available:
                logger.warning(
                    f"Model '{target_model}' unavailable, falling back to '{available[0]}'"
                )
                target_model = available[0]
        except Exception as e:
            logger.warning(f"Could not list models ({e}), using configured model")

        try:
            self.model = genai.GenerativeModel(
                model_name=target_model,
                system_instruction=SYSTEM_PROMPT,
            )
            self.chat = self.model.start_chat(history=[])
            self._initialized = True
            logger.info(f"Agent ready with model: {target_model}")
        except Exception as e:
            logger.error(f"Failed to create model: {e}")

    @property
    def is_ready(self) -> bool:
        """Check if the agent is initialized and ready to use."""
        return self._initialized and self.model is not None

    # ====================================================================
    # Context-Aware Methods (Week 8)
    # ====================================================================

    def analyze_with_context(self, compiler_context: str) -> str:
        """
        Send full compiler context to Gemini for analysis.
        
        Args:
            compiler_context: The natural language context string from
                              ContextProvider.build_context()
        
        Returns:
            Gemini's analysis and suggestions
        """
        if not self.is_ready:
            return "[Agent not initialized] Cannot reach Gemini API."

        prompt = f"""\
The compiler has processed the following Mini-Python code.
Please review the compiler state and provide feedback.

--- COMPILER CONTEXT ---
{compiler_context}
--- END CONTEXT ---

Instructions:
- If there are errors, explain each one and suggest fixes.
- If the code is valid, briefly confirm correctness and mention any improvements.
- Reference specific line numbers from the source code.
"""
        return self._safe_send(prompt)

    def explain_error(self,
                      source_code: str,
                      error_type: str,
                      error_message: str,
                      compiler_context: Optional[str] = None) -> str:
        """
        Ask Gemini to explain a specific compilation error.
        
        Args:
            source_code: The source code that caused the error
            error_type: e.g., "LexerError", "ParserError", "SemanticError"
            error_message: The error description
            compiler_context: Optional full compiler context for richer analysis
        
        Returns:
            Gemini's explanation and suggested fix
        """
        if not self.is_ready:
            return "[Agent not initialized] Cannot reach Gemini API."

        context_section = ""
        if compiler_context:
            context_section = f"""
--- COMPILER CONTEXT ---
{compiler_context}
--- END CONTEXT ---
"""

        prompt = f"""\
A user's Mini-Python code produced the following error:

ERROR TYPE: {error_type}
ERROR MESSAGE: {error_message}

SOURCE CODE:
{source_code}
{context_section}
Please:
1. Explain why this error occurred (reference the EBNF grammar rule that was violated).
2. Show the corrected code in a code block.
3. Explain what you changed and why.
"""
        return self._safe_send(prompt)

    # ====================================================================
    # Legacy Method (backward compatible)
    # ====================================================================

    def get_assistance(self, user_code: str, error_type: str,
                       error_msg: str, line_content: str) -> str:
        """
        Basic assistance request (Week 2 interface, kept for compatibility).
        
        Args:
            user_code: Full source code
            error_type: Error category
            error_msg: Error message
            line_content: The specific line with the error
        
        Returns:
            Gemini's response text
        """
        if not self.is_ready:
            return "[Agent not initialized] Cannot reach Gemini API."

        prompt = f"""\
ERROR_SUMMARY: {error_type}
SPECIFIC_MESSAGE: {error_msg}

CODE_CONTEXT:
Line of Error: {line_content}

FULL_SOURCE:
{user_code}

Please analyze the error against our EBNF grammar.
Explain the logic error and suggest a fix.
"""
        return self._safe_send(prompt)

    # ====================================================================
    # Internal Helpers
    # ====================================================================

    def _safe_send(self, prompt: str) -> str:
        """
        Send a message to Gemini with error handling.
        
        Handles:
        - API connection errors
        - Rate limiting
        - Timeout
        - Unexpected exceptions
        """
        try:
            response = self.chat.send_message(prompt)
            return response.text
        except genai.types.BlockedPromptException as e:
            logger.error(f"Prompt blocked by safety filters: {e}")
            return "[Safety Filter] The prompt was blocked. Please rephrase your code."
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning(f"Rate limited: {e}")
                return "[Rate Limited] Too many requests. Please wait a moment and try again."
            elif "timeout" in error_msg.lower():
                logger.warning(f"Request timed out: {e}")
                return "[Timeout] The request took too long. Please try again."
            else:
                logger.error(f"API error: {e}")
                return f"[API Error] {error_msg}"


class AgenticGeminiClient(GeminiCompilerAgent):
    """
    Agentic extension of GeminiCompilerAgent implementing the ReAct loop
    (Reason → Act → Observe → Reason) via the Gemini Function Calling API.

    Week 9 Implementation.

    The agent can autonomously call compiler tools (check_scope, get_errors,
    reparse_code, etc.) to investigate errors before producing a final answer.
    This mirrors how a human developer debugs: look up the symbol table,
    check for errors, try a fix, verify it compiles.
    """

    MAX_ITERATIONS = 8  # Safety cap on the ReAct loop

    def __init__(self):
        """Initialize the agentic client with tool declarations."""
        super().__init__()
        self._tools = None
        if self.is_ready:
            self._setup_tools()

    def _setup_tools(self):
        """Load tool declarations from the registry."""
        try:
            from .tool_registry import build_gemini_tools
            self._tools = build_gemini_tools()
            logger.info(
                f"AgenticGeminiClient: loaded {len(self._tools[0].function_declarations)} tools"
                if self._tools and hasattr(self._tools[0], 'function_declarations')
                else "AgenticGeminiClient: tools loaded (dict mode)"
            )
        except Exception as e:
            logger.warning(f"Could not load tool registry: {e}")
            self._tools = None

    # =========================================================================
    # Main Public Method
    # =========================================================================

    def investigate_with_tools(self,
                               source_code: str,
                               compiler_context: str,
                               toolbox=None) -> str:
        """
        Investigate code errors using the full ReAct agentic loop.

        The agent will:
          1. Receive the compiler context (AST, errors, symbol table)
          2. Reason about what additional info it needs
          3. Call compiler tools to gather that info
          4. Repeat until it can produce a complete answer

        Args:
            source_code:       The Mini-Python source code
            compiler_context:  Pre-built context string from ContextProvider
            toolbox:           Optional CompilerToolbox; if None, one is built
                               from source_code

        Returns:
            The agent's final answer after investigation (string)
        """
        if not self.is_ready:
            return "[Agent not initialized] Cannot reach Gemini API."

        # Build toolbox from source if not provided
        if toolbox is None:
            from .compiler_tools import CompilerToolbox
            toolbox = CompilerToolbox.from_source(source_code)

        # Build the initial investigation prompt
        initial_prompt = f"""\
You are investigating a Mini-Python program that has been compiled.
Use the available compiler tools to investigate the code thoroughly before giving your final answer.

--- COMPILER CONTEXT ---
{compiler_context}
--- END CONTEXT ---

Instructions:
1. Use check_scope() to look up any undefined variables.
2. Use get_errors() to get the full error list.
3. Use check_function() for any undefined function errors.
4. Use reparse_code() to verify if your suggested fix compiles.
5. After your investigation, provide a clear explanation and corrected code.
"""
        return self._agentic_loop(initial_prompt, toolbox)

    # =========================================================================
    # ReAct Loop
    # =========================================================================

    def _agentic_loop(self, initial_prompt: str, toolbox) -> str:
        """
        Drive the ReAct (Reason → Act → Observe) loop.

        Continues until Gemini stops calling tools (produces a text-only
        response) or the MAX_ITERATIONS safety cap is reached.

        Args:
            initial_prompt: The first message sent to Gemini
            toolbox:        CompilerToolbox instance for tool execution

        Returns:
            Gemini's final text response
        """
        if not self.is_ready:
            return "[Agent not initialized]"

        try:
            import google.generativeai as genai

            # Create a fresh model instance with tools enabled
            model_with_tools = genai.GenerativeModel(
                model_name=self.model.model_name,
                system_instruction=SYSTEM_PROMPT,
                tools=self._tools,
            )
            chat = model_with_tools.start_chat(
                enable_automatic_function_calling=False
            )

            # Send the initial investigation prompt
            response = chat.send_message(initial_prompt)
            tool_calls_made = []

            for iteration in range(self.MAX_ITERATIONS):
                # Check if this response contains function calls
                fn_calls = self._extract_function_calls(response)

                if not fn_calls:
                    # No more tool calls — extract and return final text answer
                    final_text = self._extract_text(response)
                    logger.info(
                        f"Agentic loop completed in {iteration + 1} iteration(s). "
                        f"Tools used: {tool_calls_made}"
                    )
                    return final_text if final_text else "[No response generated]"

                # Execute each tool call and collect results
                tool_responses = []
                for fn_call in fn_calls:
                    tool_name = fn_call.name
                    tool_args = dict(fn_call.args) if fn_call.args else {}

                    logger.info(f"Agent calling tool: {tool_name}({tool_args})")
                    tool_calls_made.append(tool_name)

                    # Execute the tool
                    result = toolbox.dispatch(tool_name, tool_args)
                    logger.info(f"Tool result ({tool_name}): {result[:120]}...")

                    tool_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response={"result": result}
                            )
                        )
                    )

                # Send all tool results back to Gemini
                response = chat.send_message(tool_responses)

            # Safety cap reached
            logger.warning(
                f"Agentic loop hit MAX_ITERATIONS ({self.MAX_ITERATIONS}). "
                f"Returning last text response."
            )
            return self._extract_text(response) or "[Max iterations reached]"

        except Exception as e:
            logger.error(f"Agentic loop error: {e}")
            return f"[Agentic Loop Error] {e}"

    # =========================================================================
    # Helpers
    # =========================================================================

    def _extract_function_calls(self, response) -> list:
        """Extract function call parts from a Gemini response."""
        try:
            fn_calls = []
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call.name:
                    fn_calls.append(part.function_call)
            return fn_calls
        except Exception:
            return []

    def _extract_text(self, response) -> str:
        """Extract plain text parts from a Gemini response."""
        try:
            text_parts = []
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
            return "\n".join(text_parts)
        except Exception:
            try:
                return response.text
            except Exception:
                return ""

    def simulate_agentic_investigation(self,
                                       source_code: str,
                                       error_description: str,
                                       toolbox=None) -> dict:
        """
        Simulate the agentic investigation WITHOUT calling the Gemini API.

        Useful for demonstrations and testing the tool-use pipeline
        without needing an API key. Mimics what Gemini would do.

        Args:
            source_code:       The Mini-Python source code
            error_description: Human-readable description of the error
            toolbox:           Optional CompilerToolbox (built from source if None)

        Returns:
            dict with keys: 'tool_calls', 'observations', 'final_answer'
        """
        if toolbox is None:
            from .compiler_tools import CompilerToolbox
            toolbox = CompilerToolbox.from_source(source_code)

        # Simulate the ReAct steps
        steps = []

        # Step 1: Always check errors first
        errors_result = toolbox.get_errors()
        steps.append({
            "step": 1,
            "action": "get_errors()",
            "reasoning": "First, check what errors the compiler found.",
            "observation": errors_result,
        })

        # Step 2: Check symbol table for context
        symbols_result = toolbox.get_symbol_table()
        steps.append({
            "step": 2,
            "action": "get_symbol_table()",
            "reasoning": "Check the symbol table to understand what is defined.",
            "observation": symbols_result,
        })

        # Step 3: Check AST structure
        ast_result = toolbox.get_ast_summary()
        steps.append({
            "step": 3,
            "action": "get_ast_summary()",
            "reasoning": "Understand the program structure from the AST.",
            "observation": ast_result,
        })

        # Step 4: If there are errors, identify undefined names and check scope
        from .compiler_tools import CompilerToolbox as TB
        if toolbox.analyzer and toolbox.analyzer.errors:
            for err in toolbox.analyzer.errors[:2]:  # check first 2 errors max
                # Try to extract a variable/function name from the error message
                import re
                match = re.search(r"'(\w+)'", err.message)
                if match:
                    name = match.group(1)
                    scope_result = toolbox.check_scope(name)
                    steps.append({
                        "step": len(steps) + 1,
                        "action": f"check_scope('{name}')",
                        "reasoning": (
                            f"Error mentions '{name}'. Checking if it's defined anywhere."
                        ),
                        "observation": scope_result,
                    })

        # Produce a simulated final answer
        error_count = len(toolbox.analyzer.errors) if toolbox.analyzer else 0
        if error_count == 0:
            final = (
                "✅ After investigation, the code compiles without errors.\n"
                "The symbol table is correct and all variables are defined."
            )
        else:
            error_list = "\n".join(
                f"  • Line {e.line}: {e.message}"
                for e in toolbox.analyzer.errors
            )
            final = (
                f"🔍 Investigation complete. Found {error_count} error(s):\n"
                f"{error_list}\n\n"
                f"Please fix the above errors and reparse_code() to verify the fix."
            )

        return {
            "tool_calls": [s["action"] for s in steps],
            "observations": steps,
            "final_answer": final,
        }


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Quick sanity check
    logging.basicConfig(level=logging.INFO)
    agent = GeminiCompilerAgent()
    if agent.is_ready:
        print("Agent initialized successfully!")
        result = agent.get_assistance(
            "if x > 5 print(x)", "SyntaxError",
            "Expected ':'", "if x > 5 print(x)"
        )
        print(result)
    else:
        print("Agent failed to initialize. Check GEMINI_API_KEY.")