"""
Tool Registry for Gemini Function Calling API
Defines the function declaration schemas that tell Gemini what tools are
available and how to call them. Week 9 Implementation.

The schemas follow the Gemini protos format:
  genai.protos.Tool(function_declarations=[...])
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema Definitions (built as plain dicts for portability + testability)
# ---------------------------------------------------------------------------

TOOL_SCHEMA_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "check_scope",
        "description": (
            "Look up a variable or identifier in the compiler's symbol table. "
            "Use this to determine if a variable is defined, its type, and where "
            "it was declared. Call this when you see an 'Undefined variable' error."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "variable_name": {
                    "type": "string",
                    "description": "The variable or identifier name to look up (e.g., 'x', 'counter')"
                }
            },
            "required": ["variable_name"]
        }
    },
    {
        "name": "check_function",
        "description": (
            "Check whether a function is defined in the current scope and retrieve "
            "its parameter list. Use this when you see 'Undefined function' errors "
            "or want to verify function signatures."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "function_name": {
                    "type": "string",
                    "description": "The function name to check (e.g., 'factorial', 'compute')"
                }
            },
            "required": ["function_name"]
        }
    },
    {
        "name": "get_errors",
        "description": (
            "Retrieve the complete list of semantic errors found during compilation. "
            "Returns all error messages with line and column numbers. "
            "Use this to get a comprehensive error report."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_warnings",
        "description": (
            "Retrieve the list of semantic warnings found during compilation, "
            "such as type mismatches or unused variables. "
            "Use this to identify potential issues that are not hard errors."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_symbol_table",
        "description": (
            "Retrieve the complete symbol table showing all variables and functions "
            "in every scope, their types, and definition locations. "
            "Use this to understand the full program state."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_ast_summary",
        "description": (
            "Retrieve a natural language summary of the program's Abstract Syntax Tree (AST), "
            "describing the program structure: functions defined, global statements, "
            "control flow, and assignments. "
            "Use this to understand the program's overall structure."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "reparse_code",
        "description": (
            "Re-run the full compiler pipeline (Lexer → Parser → Semantic Analyzer) "
            "on a new or modified version of the source code. "
            "Use this to verify if a proposed fix actually resolves the errors. "
            "After calling this, other tools (check_scope, get_errors, etc.) will "
            "reflect the new code's state."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source_code": {
                    "type": "string",
                    "description": "The new Mini-Python source code to compile and analyze"
                }
            },
            "required": ["source_code"]
        }
    },
    {
        "name": "audit_security",
        "description": (
            "Run the SAST (Static Application Security Testing) security auditor "
            "on the current source code. "
            "Detects: unsafe builtins (eval, exec, __import__), dangerous imports, "
            "Prompt Injection keywords hidden in comments, Logic Bomb patterns "
            "(time/date-triggered payloads), and infinite recursion heuristics. "
            "Use this whenever you suspect security issues in the code."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]


def get_tool_names() -> List[str]:
    """Return the list of all registered tool names."""
    return [schema["name"] for schema in TOOL_SCHEMA_DEFINITIONS]


def get_schema_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Return a specific tool schema by name, or None if not found."""
    for schema in TOOL_SCHEMA_DEFINITIONS:
        if schema["name"] == name:
            return schema
    return None


def build_gemini_tools():
    """
    Build the Gemini tool declarations from the schema definitions.

    Returns:
        A list containing one genai.protos.Tool object with all function
        declarations, OR a plain-dict fallback if genai is not available.

    Note:
        The return type is intentionally flexible: if google.generativeai
        is not installed or the API is not configured, returns a dict
        representation (useful for testing without API access).
    """
    try:
        import google.generativeai as genai

        function_declarations = []
        for schema in TOOL_SCHEMA_DEFINITIONS:
            properties = {}
            for prop_name, prop_def in schema["parameters"].get("properties", {}).items():
                prop_type = _map_type(prop_def.get("type", "string"))
                properties[prop_name] = genai.protos.Schema(
                    type=prop_type,
                    description=prop_def.get("description", "")
                )

            required = schema["parameters"].get("required", [])

            fn_decl = genai.protos.FunctionDeclaration(
                name=schema["name"],
                description=schema["description"],
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties=properties,
                    required=required
                )
            )
            function_declarations.append(fn_decl)

        return [genai.protos.Tool(function_declarations=function_declarations)]

    except ImportError:
        logger.warning("google-generativeai not installed, returning dict schemas")
        return TOOL_SCHEMA_DEFINITIONS

    except Exception as e:
        logger.error(f"Failed to build Gemini tools: {e}")
        return TOOL_SCHEMA_DEFINITIONS


def _map_type(json_type: str):
    """Map JSON schema type string to genai.protos.Type enum."""
    try:
        import google.generativeai as genai
        mapping = {
            "string": genai.protos.Type.STRING,
            "integer": genai.protos.Type.INTEGER,
            "number": genai.protos.Type.NUMBER,
            "boolean": genai.protos.Type.BOOLEAN,
            "array": genai.protos.Type.ARRAY,
            "object": genai.protos.Type.OBJECT,
        }
        return mapping.get(json_type, genai.protos.Type.STRING)
    except ImportError:
        return json_type
