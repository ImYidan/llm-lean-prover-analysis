"""Deterministic mappings to the study's eight manually defined error categories."""


from __future__ import annotations

import re


CATEGORY_ORDER = (
    "Syntax error",
    "Unresolved name",
    "Type mismatch",
    "Missing instance",
    "Tactic failure",
    "Unsolved goals",
    "Termination failure",
    "Resource exhaustion",
)


CATEGORY_DEFINITIONS = (
    (
        "Syntax error",
        "syntax",
        "The parser rejects the generated Lean syntax before the affected term can be elaborated.",
    ),
    (
        "Unresolved name",
        "name",
        "Lean cannot find or uniquely resolve a referenced identifier, declaration, namespace, universe level, tactic, or structure field in the pinned environment, or encounters a conflicting declaration name.",
    ),
    (
        "Type mismatch",
        "type",
        "Lean cannot elaborate or type-check a term, application, pattern, constructor, projection, coercion, implicit argument, or universe constraint; under the fixed eight-category scheme, rare kernel-evaluation and code-generation diagnostics are also included here.",
    ),
    (
        "Missing instance",
        "instance",
        "Typeclass instance synthesis fails, becomes stuck, or encounters a term where an instance is required.",
    ),
    (
        "Tactic failure",
        "tactic",
        "While elaborating or executing a recognized tactic, Lean rejects its arguments or current goal, fails to apply a rule or transformation, produces an invalid result, or reports no progress; an unknown tactic is classified as Unresolved name.",
    ),
    (
        "Unsolved goals",
        "goals",
        "The proof or tactic block ends while one or more goals remain open.",
    ),
    (
        "Termination failure",
        "termination",
        "Lean cannot establish termination for a recursive definition.",
    ),
    (
        "Resource exhaustion",
        "resource",
        "Lean exhausts a heartbeat, deterministic-time, recursion-depth, or memory limit.",
    ),
)


def matches(pattern: str, line: str) -> bool:
    """Return whether a case-insensitive regex matches the diagnostic header."""
    return re.search(pattern, line, re.IGNORECASE) is not None


def _fallback_category(line: str) -> str:
    """Classify a raw line without changing it; fail closed if no rule applies."""
    if line == "unsolved goals":
        return "Unsolved goals"

    if matches(
        r"maximum (recursion depth|number of heartbeats)|resource exhausted|"
        r"out of memory|timeout at|deterministic\)? timeout",
        line,
    ):
        return "Resource exhaustion"

    if matches(r"^fail to show termination", line):
        return "Termination failure"

    if matches(
        r"^failed to compile definition, consider marking it as ['`]noncomputable['`]|"
        r"^\(kernel\) cannot evaluate code because",
        line,
    ):
        # The paper uses one uniform eight-class taxonomy.  These rare
        # post-elaboration failures stay verbatim in the appendix and are
        # grouped with the closest compiler-checking class.
        return "Type mismatch"

    if matches(
        r"^(expected (token|command|term|no space|interpolated string)|"
        r"unexpected (token|identifier|syntax|end of input|type ascription))",
        line,
    ):
        return "Syntax error"

    if matches(
        r"^(unknown (identifier|constant|tactic|lemma|namespace|universe level|free variable)|"
        r"invalid dotted identifier notation, unknown identifier|ambiguous|overloaded)|"
        r"the environment does not contain|is not a field of structure",
        line,
    ):
        return "Unresolved name"

    if matches(
        r"failed to synthesize|typeclass instance problem|type class instance expected|"
        r"synthesized type class instance is not definitionally equal",
        line,
    ):
        return "Missing instance"

    # Outermost tactic emitters take precedence over type words inside the same
    # line, e.g. "invalid 'simp', proposition expected" remains a tactic error.
    if matches(
        r"tactic|linarith|omega|ring failed|`?simp`? made no progress|simp_all made no progress|"
        r"dsimp made no progress|ring_nf made no progress|abel_nf made no progress|"
        r"push(?:_neg)? made no progress|"
        r"tauto failed|positivity|nonzeroness|invalid rewrite argument|"
        r"failed to rewrite using|"
        r"rearrange comparison|^'specialize' requires|case tag|"
        r"dependent elimination failed|interval_cases failed|extensionality theorem|"
        r"target \(or one of its indices\) occurs|no goals to be solved|"
        r"applyExtTheorem|invalid ['`]simp|invalid simp theorem|"
        r"alternative [`'][^`']+[`'] has not been provided|"
        r"^alternative [`'][^\n]+ has not been provided|invalid alternative name|"
        r"too many variable names provided at alternative|missing cases:|"
        r"unexpected term .*expected single reference to variable|"
        r"too many arguments supplied to [`']use[`']|aesop:|"
        r"['`]compute_degree['`] inapplicable",
        line,
    ):
        return "Tactic failure"

    if matches(
        r"^target$|^failed: .* is not the type of a function|"
        r"type mismatch|function expected|type expected|invalid field notation|"
        r"invalid use of field notation with [`']@[`'] modifier|"
        r"invalid constructor|invalid `⟨\.\.\.⟩` notation|insufficient number of fields|"
        r"invalid 'calc' step, left-hand[- ]side|invalid argument|invalid pattern|numerals are data|"
        r"mod_cast has type|stuck at solving universe constraint|"
        r"failed to solve universe constraint|failed to infer|"
        r"expected a term of the shape|index in target|failed to prove index is valid|"
        r"proposition expected|invalid projection|invalid occurrence|"
        r"unexpected bound variable|application type mismatch|"
        r"expected type must not contain free( or meta)? variables|"
        r"synthesize (placeholder|implicit argument)|existsunique|fields missing|"
        r"invalid `▸` notation|invalid \{\.\.\.\} notation|"
        r"^a placeholder `_` cannot be used where a function is expected|"
        r"^['`]calc['`] expression has type|"
        r"^expected resulting type of eliminator",
        line,
    ):
        return "Type mismatch"

    raise ValueError(f"unclassified raw compiler first line: {line!r}")


def _classify_head(line: str) -> str:
    """Apply historical header-specific overrides, then the broad regex rules; raise on an unknown diagnostic."""
    lower = line.lower()
    if re.match("^unknown identifier '.+?'$", line, re.IGNORECASE):
        return 'Unresolved name'
    if re.match("^tactic '.+?' failed", line, re.IGNORECASE):
        return 'Tactic failure'
    if 'failed to synthesize' in lower:
        return 'Missing instance'
    special: str | None = None
    if line in {'unexpected relation type', "invalid 'calc' step, relation expected"}:
        special = 'Type mismatch'
    elif lower == 'simp failed, maximum number of steps exceeded':
        special = 'Resource exhaustion'
    elif lower.startswith('invalid binder annotation, type is not a class instance'):
        special = 'Type mismatch'
    elif lower == 'expected type must be known':
        special = 'Type mismatch'
    elif lower.startswith('instance does not provide concrete values for (semi-)out-params'):
        special = 'Missing instance'
    elif lower.startswith("placeholders '_'") and 'function is expected' in lower:
        special = 'Type mismatch'
    elif lower == 'missing exponent digits in scientific literal':
        special = 'Syntax error'
    elif lower.startswith('invalid use of `(<- ...)`'):
        special = 'Syntax error'
    elif lower.startswith('cannot evaluate code because') and "uses 'sorry'" in lower:
        special = 'Type mismatch'
    elif lower.startswith('gcongr did not make progress'):
        special = 'Tactic failure'
    elif lower.startswith('unused alternative'):
        special = 'Tactic failure'
    elif lower.startswith('failed to elaborate eliminator'):
        special = 'Type mismatch'
    elif 'has already been declared' in lower:
        special = 'Unresolved name'
    elif lower.startswith('failed to find '):
        special = 'Type mismatch'
    elif 'fun_prop' in lower and 'was unable to prove' in lower:
        special = 'Tactic failure'
    elif lower.startswith('missing end of character literal'):
        special = 'Syntax error'
    elif lower == 'invalid ':
        special = 'Type mismatch'
    elif lower.startswith('insufficient number of targets'):
        special = 'Tactic failure'
    elif lower.startswith('unexpected term ') and 'expected single reference to variable' in lower:
        special = 'Tactic failure'
    elif lower.startswith('unexpected term '):
        special = 'Type mismatch'
    elif lower.startswith('apply_fun can only handle'):
        special = 'Tactic failure'
    elif line == "invalid field 'get', the environme":
        special = 'Unresolved name'
    elif lower.startswith('unknown metavariable'):
        special = 'Type mismatch'
    elif lower.startswith("'obtain' requires") or lower.startswith('`obtain` requires'):
        special = 'Tactic failure'
    elif lower.startswith('expected checkcolgt'):
        special = 'Syntax error'
    elif lower.startswith("unnecessary 'generalizing' argument"):
        special = 'Tactic failure'
    elif lower.startswith('invalid match-expression'):
        special = 'Type mismatch'
    elif lower.startswith('invalid coercion notation'):
        special = 'Type mismatch'
    elif lower.startswith('invalid binder name'):
        special = 'Type mismatch'
    elif lower.startswith("invalid 'calc' step, right-hand side is"):
        special = 'Type mismatch'
    elif lower.startswith('invalid `←` modifier'):
        special = 'Tactic failure'
    elif lower.startswith('invalid dotted identifier notation: the expected type'):
        special = 'Type mismatch'
    elif lower == 'expected type must not contain metavariables':
        special = 'Type mismatch'
    elif lower.startswith('identifier <missing> not found'):
        special = 'Unresolved name'
    elif lower.startswith('cannot coerce'):
        special = 'Type mismatch'
    elif 'must have a function type, not' in lower:
        special = 'Type mismatch'
    elif lower.startswith('not a comparison:'):
        special = 'Tactic failure'
    elif lower.startswith("unexpected '..'"):
        special = 'Syntax error'
    elif lower.startswith('argument `') and lower.endswith('was already set'):
        special = 'Type mismatch'
    elif lower.startswith('failed to create binder'):
        special = 'Type mismatch'
    elif lower.startswith('redundant alternative'):
        special = 'Tactic failure'
    elif lower.startswith('too many variable names provided'):
        special = 'Tactic failure'
    elif lower.startswith("expected ';' or line break"):
        special = 'Syntax error'
    elif lower.startswith("invalid 'end', insufficient scopes"):
        special = 'Syntax error'
    elif 'apply_fun' in lower and 'could not apply' in lower:
        special = 'Tactic failure'
    elif lower == 'expected structure' or lower.endswith('is not a structure'):
        special = 'Type mismatch'
    elif lower.startswith('the given degree is'):
        special = 'Tactic failure'
    elif lower.startswith('duplicate alternative name'):
        special = 'Tactic failure'
    if special is not None:
        return special
    return _fallback_category(line)


def classify_error(message: str) -> str:
    """Map one complete parsed diagnostic to exactly one of CATEGORY_ORDER.

    Historical rules inspect the diagnostic header, not goal-state words in
    its body. This labels every diagnostic independently; it does not choose
    one error or one category per candidate. Raise ValueError for an unknown
    header and TypeError for a non-string message.
    """
    if not isinstance(message, str):
        raise TypeError("diagnostic message must be a string")
    lines = message.splitlines()
    return _classify_head(lines[0] if lines else "")
