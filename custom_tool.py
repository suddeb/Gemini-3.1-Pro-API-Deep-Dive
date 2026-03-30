from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json

# ── Configuration ─────────────────────────────────────────────────────────────
MODEL   = "gemini-3.1-pro-preview-customtools"   # dedicated custom-tools endpoint

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOM TOOL IMPLEMENTATIONS
# Each function is the real logic your app runs when Gemini "calls" the tool.
# ══════════════════════════════════════════════════════════════════════════════

def analyze_code_complexity(code: str, language: str) -> dict:
    """
    Analyze cyclomatic complexity and nesting depth of the provided code.
    Returns a dict with complexity metrics.
    """
    lines       = code.split("\n")
    loc         = len([l for l in lines if l.strip() and not l.strip().startswith("#")])
    max_indent  = max((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    nesting     = max_indent // 4

    # Count branching keywords as a proxy for cyclomatic complexity
    branch_kw   = ["if ", "elif ", "else:", "for ", "while ", "except ", "case "]
    complexity  = sum(code.count(kw) for kw in branch_kw)

    return {
        "language"           : language,
        "lines_of_code"      : loc,
        "estimated_complexity": complexity,
        "max_nesting_depth"  : nesting,
        "complexity_rating"  : "High" if complexity > 10 else "Medium" if complexity > 5 else "Low",
    }


def check_code_patterns(code: str, language: str) -> dict:
    """
    Check for common anti-patterns and bad practices.
    Returns a list of pattern issues found.
    """
    issues = []

    anti_patterns = {
        "magic_numbers"      : any(c.isdigit() for c in code.split() if c.isdigit() and c not in ("0","1")),
        "long_functions"     : code.count("def ") > 0 and len(code.split("\n")) > 50,
        "no_docstrings"      : "def " in code and '"""' not in code and "'''" not in code,
        "bare_except"        : "except:" in code,
        "global_variables"   : "global " in code,
        "hardcoded_strings"  : code.count('"') > 10 or code.count("'") > 10,
        "missing_type_hints" : "def " in code and "->" not in code,
    }

    for pattern, found in anti_patterns.items():
        if found:
            issues.append(pattern.replace("_", " ").title())

    return {
        "language"          : language,
        "anti_patterns_found": issues,
        "total_issues"      : len(issues),
        "severity"          : "High" if len(issues) > 4 else "Medium" if len(issues) > 2 else "Low",
    }


def check_security_vulnerabilities(code: str, language: str) -> dict:
    """
    Scan code for common security vulnerabilities.
    """
    vulnerabilities = []

    security_checks = {
        "SQL Injection risk"           : any(kw in code for kw in ["execute(", "cursor.execute", "raw_query"]),
        "Hardcoded credentials"        : any(kw in code.lower() for kw in ["password =", "secret =", "api_key ="]),
        "Shell injection (subprocess)" : "shell=True" in code,
        "Use of eval()"                : "eval(" in code,
        "Use of exec()"                : "exec(" in code,
        "Insecure random (random.)"    : "import random" in code and "secrets" not in code,
        "Debug mode enabled"           : "debug=True" in code or "DEBUG = True" in code,
        "Broad exception suppression"  : "pass" in code and "except" in code,
    }

    for vuln, found in security_checks.items():
        if found:
            vulnerabilities.append(vuln)

    return {
        "language"           : language,
        "vulnerabilities"    : vulnerabilities,
        "vulnerability_count": len(vulnerabilities),
        "risk_level"         : "Critical" if len(vulnerabilities) > 3
                               else "High" if len(vulnerabilities) > 1
                               else "Low",
    }


def suggest_performance_improvements(code: str, language: str) -> dict:
    """
    Identify performance bottlenecks and suggest optimizations.
    """
    suggestions = []

    perf_checks = {
        "Use list comprehension instead of loops where possible":
            "for " in code and ".append(" in code,
        "Consider caching repeated function calls (@lru_cache)":
            code.count("def ") > 1 and "cache" not in code,
        "Avoid repeated string concatenation in loops — use str.join()":
            "+=" in code and "str" in code.lower(),
        "Use generators instead of lists for large datasets":
            "return [" in code and "yield" not in code,
        "Prefer set/dict lookups over list search (O(1) vs O(n))":
            "in [" in code or " in list" in code,
        "Replace manual loops with built-ins: map(), filter(), sum()":
            code.count("for ") > 3,
        "Profile database queries — potential N+1 problem":
            any(kw in code for kw in ["query(", "filter(", "objects.get("]),
    }

    for suggestion, applies in perf_checks.items():
        if applies:
            suggestions.append(suggestion)

    return {
        "language"               : language,
        "performance_suggestions": suggestions,
        "optimization_count"     : len(suggestions),
        "impact"                 : "High" if len(suggestions) > 4
                                   else "Medium" if len(suggestions) > 2
                                   else "Low",
    }


# ══════════════════════════════════════════════════════════════════════════════
# TOOL DECLARATIONS  (what Gemini "sees" — name, description, JSON schema)
# ══════════════════════════════════════════════════════════════════════════════

TOOL_DECLARATIONS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="analyze_code_complexity",
            description="Analyze the cyclomatic complexity, nesting depth, and lines of code. "
                        "Use this first to understand the overall structure.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "code"    : types.Schema(type=types.Type.STRING, description="Source code to analyze"),
                    "language": types.Schema(type=types.Type.STRING, description="Programming language (e.g. 'python')"),
                },
                required=["code", "language"],
            ),
        ),
        types.FunctionDeclaration(
            name="check_code_patterns",
            description="Detect anti-patterns and bad coding practices such as magic numbers, "
                        "bare excepts, missing docstrings, or missing type hints.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "code"    : types.Schema(type=types.Type.STRING, description="Source code to analyze"),
                    "language": types.Schema(type=types.Type.STRING, description="Programming language"),
                },
                required=["code", "language"],
            ),
        ),
        types.FunctionDeclaration(
            name="check_security_vulnerabilities",
            description="Scan for security vulnerabilities: SQL injection, hardcoded secrets, "
                        "eval/exec usage, shell injection, insecure randomness, debug flags.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "code"    : types.Schema(type=types.Type.STRING, description="Source code to analyze"),
                    "language": types.Schema(type=types.Type.STRING, description="Programming language"),
                },
                required=["code", "language"],
            ),
        ),
        types.FunctionDeclaration(
            name="suggest_performance_improvements",
            description="Identify performance bottlenecks and suggest concrete optimizations "
                        "like list comprehensions, caching, generators, or set lookups.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "code"    : types.Schema(type=types.Type.STRING, description="Source code to analyze"),
                    "language": types.Schema(type=types.Type.STRING, description="Programming language"),
                },
                required=["code", "language"],
            ),
        ),
    ])
]

# Map function names → actual Python callables
TOOL_REGISTRY = {
    "analyze_code_complexity"       : analyze_code_complexity,
    "check_code_patterns"           : check_code_patterns,
    "check_security_vulnerabilities": check_security_vulnerabilities,
    "suggest_performance_improvements": suggest_performance_improvements,
}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTIC TOOL-CALLING LOOP
# ══════════════════════════════════════════════════════════════════════════════

def execute_tool_call(function_name: str, function_args: dict) -> str:
    """Dispatch a Gemini function-call request to the real Python function."""
    if function_name not in TOOL_REGISTRY:
        return json.dumps({"error": f"Unknown function: {function_name}"})
    try:
        result = TOOL_REGISTRY[function_name](**function_args)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def review_code_with_gemini(code: str, language: str = "python") -> str:
    """
    Send code to Gemini 3.1 Pro with custom tools.
    Runs the agentic loop until Gemini returns a final text response.
    """
    system_prompt = (
        "You are an expert code reviewer. When given code, you MUST use ALL four "
        "available tools — analyze_code_complexity, check_code_patterns, "
        "check_security_vulnerabilities, and suggest_performance_improvements — "
        "before writing your final review. Synthesize all tool results into a "
        "structured, actionable report with prioritized recommendations."
    )

    user_prompt = (
        f"Please perform a comprehensive code review of the following {language} code. "
        f"Use all available tools to analyze it thoroughly.\n\n"
        f"```{language}\n{code}\n```"
    )

    # Conversation history (grows as tool calls are made)
    messages = [types.Content(role="user", parts=[types.Part(text=user_prompt)])]

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=TOOL_DECLARATIONS,
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="AUTO")
        ),
        temperature=0.1,
    )

    print(f"\n🔍 Reviewing {language} code with Gemini {MODEL}...\n")

    # ── Agentic loop ──────────────────────────────────────────────────────────
    while True:
        response = client.models.generate_content(
            model=MODEL,
            contents=messages,
            config=config,
        )

        candidate = response.candidates[0]
        messages.append(types.Content(role="model", parts=candidate.content.parts))

        # Check whether Gemini wants to call any functions
        function_calls = [p for p in candidate.content.parts if p.function_call]

        if not function_calls:
            # No more tool calls → extract and return the final text
            text_parts = [p.text for p in candidate.content.parts if p.text]
            return "\n".join(text_parts)

        # Execute each requested tool and collect responses
        tool_response_parts = []
        for part in function_calls:
            fc   = part.function_call
            name = fc.name
            args = dict(fc.args)

            print(f"  🔧 Tool called: {name}({', '.join(f'{k}=...' for k in args)})")
            result = execute_tool_call(name, args)

            tool_response_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        id=fc.id,       # Gemini 3.x generates unique IDs per call
                        name=name,
                        response={"result": result},
                    )
                )
            )

        # Send tool results back to Gemini and continue the loop
        messages.append(types.Content(role="user", parts=tool_response_parts))


# ══════════════════════════════════════════════════════════════════════════════
# SAMPLE CODE TO REVIEW
# ══════════════════════════════════════════════════════════════════════════════

SAMPLE_CODE = '''
import random

password = "supersecret123"
DEBUG = True

def get_users(db, name):
    query = "SELECT * FROM users WHERE name = '" + name + "'"
    result = db.execute(query)
    users = []
    for u in result:
        users.append(u)
    return users

def calculate_discount(price, items):
    total = 0
    for i in range(len(items)):
        if items[i]["type"] == "A":
            total = total + items[i]["price"] * 0.9
        elif items[i]["type"] == "B":
            total = total + items[i]["price"] * 0.85
        elif items[i]["type"] == "C":
            total = total + items[i]["price"] * 0.8
        else:
            total = total + items[i]["price"]
    return total

def generate_token():
    token = ""
    for i in range(32):
        token += str(random.randint(0, 9))
    return token

def process(data):
    try:
        result = eval(data)
        return result
    except:
        pass
'''


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    report = review_code_with_gemini(SAMPLE_CODE, language="python")
    print("\n" + "═" * 70)
    print("📋  GEMINI CODE REVIEW REPORT")
    print("═" * 70)
    print(report)
