"""Rule-based diagnostic templates; no fitted model or unsupervised clustering."""


from __future__ import annotations

import re


def lower_initial(text: str) -> str:
    """Normalize surrounding whitespace, quote style and initial case for a template; leave the raw message untouched."""
    text = text.strip().replace("‘", "'").replace("’", "'")
    return text[:1].lower() + text[1:] if text else text


def replace_quoted(text: str, placeholder: str = "ID") -> str:
    """Replace quoted identifier payloads with a placeholder, handling identifier-final primes and word apostrophes."""
    text = re.sub(r"`[^`\n]*`", f"'{placeholder}'", text)
    # Do not interpret apostrophes inside words (e.g. "don't") as Lean's
    # single-quoted identifier delimiters. Consume identifier-final primes as
    # part of the quoted payload, e.g. 'map_zero'' -> 'ID'.
    text = re.sub(
        r"(?<![A-Za-z0-9])'[^'\n]+?'+(?=\s|[,.;:)\]}]|$)",
        f"'{placeholder}'",
        text,
    )
    return text


def replace_dynamic(text: str, placeholder: str = "ID") -> str:
    """Parameterize quoted values, metavariables and numeric indices; collapse whitespace in a template only."""
    text = replace_quoted(text, placeholder)
    text = re.sub(r"\?[A-Za-z_][A-Za-z0-9_.'⁻¹]*", "ID", text)
    text = re.sub(r"#\d+", "#NUM", text)
    text = re.sub(r"\b\d+\b", "NUM", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def syntax_template(line: str) -> str:
    """Return a syntax-error template retaining expected-token structure while masking concrete tokens."""
    low = lower_initial(line)
    if low.startswith("unexpected token"):
        if "; expected " in low:
            _, expected = low.split("; expected ", 1)
            return f"unexpected token 'TOKEN'; expected {replace_quoted(expected, 'TOKEN')}"
        return "unexpected token 'TOKEN'"
    if low.startswith("unexpected identifier"):
        if "; expected " in low:
            _, expected = low.split("; expected ", 1)
            return f"unexpected identifier; expected {replace_quoted(expected, 'TOKEN')}"
        return "unexpected identifier"
    if low.startswith("unexpected end of input") and "; expected " in low:
        _, expected = low.split("; expected ", 1)
        return f"unexpected end of input; expected {replace_quoted(expected, 'TOKEN')}"
    if low.startswith("expected "):
        return replace_quoted(low, "TOKEN")
    return replace_dynamic(low, "TOKEN")


def name_template(line: str) -> str:
    """Return a name-resolution template with referenced identifiers and fields replaced by ID."""
    low = lower_initial(line)
    for prefix in (
        "unknown identifier",
        "unknown constant",
        "unknown tactic",
        "unknown lemma",
        "unknown namespace",
        "unknown universe level",
        "unknown free variable",
    ):
        if low.startswith(prefix):
            return f"{prefix} 'ID'"
    if low.startswith("invalid dotted identifier notation") and "unknown identifier" in low:
        return "unknown identifier 'ID'"
    if low.startswith("invalid field") and "environment does not contain" in low:
        return "invalid field 'ID', the environment does not contain 'ID'"
    if "is not a field of structure" in low:
        return "'ID' is not a field of structure 'ID'"
    if "has already been declared" in low:
        return "'ID' has already been declared"
    if low.startswith("identifier <missing> not found") or (
        low.startswith("identifier ") and low.endswith(" not found")
    ):
        return "unknown identifier 'ID'"
    if low.startswith("invalid field") and "the environme" in low:
        return "invalid field 'ID', the environment does not contain 'ID'"
    if low.startswith("ambiguous term, use fully qualified name, possible interpretations"):
        return "ambiguous term, use fully qualified name, possible interpretations ['ID']"
    return replace_dynamic(low)


def type_template(line: str) -> str:
    """Return a type-checking template preserving the failure wording while masking concrete term payloads."""
    low = lower_initial(line)
    folded = low.casefold()
    if low.startswith("function expected at"):
        return "function expected at 'ID'"
    if low.startswith("don't know how to synthesize implicit argument"):
        return "don't know how to synthesize implicit argument 'ID'"
    if low.startswith("don't know how to synthesize placeholder"):
        return "don't know how to synthesize placeholder for argument 'ID'"
    if low.startswith("failed to find"):
        if " as the type of a parameter of " in low:
            return "failed to find 'ID' as the type of a parameter of 'ID'"
        return "failed to find 'ID'"
    if low.startswith("failed to infer implicit target"):
        return "failed to infer implicit target 'ID'"
    if low.startswith("fields missing:"):
        return "fields missing: 'ID'"
    if low.startswith("unexpected term"):
        return "unexpected term 'ID'"
    if low.startswith("failed to compile definition, consider marking it as"):
        return (
            "failed to compile definition, consider marking it as 'noncomputable' "
            "because it depends on 'ID', and it does not have executable code"
        )
    if low.startswith("(kernel) cannot evaluate code because"):
        return "(kernel) cannot evaluate code because 'ID' uses 'sorry' and/or contains errors"
    if low.startswith("invalid argument name") and " for function" in low:
        return "invalid argument name 'ID' for function 'ID'"
    if folded.startswith("invalid argument") and "variable" in folded and (
        "not a proposition or let-declaration" in folded
    ):
        return "invalid argument: variable 'ID' is not a proposition or let-declaration"
    if folded.startswith("invalid pattern variable") and "must be atomic" in folded:
        return "invalid pattern variable 'ID', must be atomic"
    if folded.startswith("invalid pattern") and "constructor or constant marked with" in folded:
        return "invalid pattern: constructor or constant marked with 'ID' expected"
    if folded.startswith(("invalid pattern(s):", "invalid patterns,")) and (
        "inaccessible to pattern matching" in folded
    ):
        return (
            "invalid patterns: 'ID' occurs only in positions inaccessible to pattern matching"
        )
    if folded.startswith("invalid projection: index ") and "invalid for this structure" in folded:
        return "invalid projection: index 'ID' is invalid for this structure"
    if folded.startswith("invalid ") and " step, left-hand" in folded:
        return "invalid 'ID' step, left-hand side is"
    if folded.startswith("insufficient number of fields for"):
        return "insufficient number of fields for 'ID' constructor"
    if folded.startswith("invalid constructor ⟨...⟩, insufficient number of arguments"):
        return "invalid constructor ⟨...⟩, insufficient number of arguments for 'ID'"
    if low.startswith("unexpected bound variable #"):
        return "unexpected bound variable #NUM"
    if low.startswith("invalid field notation, function "):
        suffix = low.split(", function ", 1)[1]
        if " does not have argument with type " in suffix:
            return (
                "invalid field notation, function 'ID' does not have an argument with "
                "the required receiver type"
            )
    if folded.startswith("invalid field notation: function ") and "does not have a usable parameter" in folded:
        return (
            "invalid field notation, function 'ID' does not have an argument with "
            "the required receiver type"
        )
    return replace_dynamic(low)


def instance_template(line: str) -> str:
    """Return a typeclass-failure template with concrete instance payloads replaced by TYPE."""
    low = lower_initial(line)
    if low.startswith("choose!: failed to synthesize any nonempty instances"):
        return "choose!: failed to synthesize any nonempty instances 'TYPE'"
    if low.startswith("failed to synthesize instance of ") and low != "failed to synthesize instance of type class":
        return "failed to synthesize instance of 'TYPE'"
    return replace_dynamic(low, "TYPE")


def tactic_suffix_template(suffix: str) -> str:
    """Normalize a tactic diagnostic suffix while retaining the specific kind of tactic failure."""
    low = lower_initial(suffix).rstrip(".:")
    if "nested error" in low:
        return "nested error"
    if "did not find instance of the pattern" in low or "did not find an occurrence of the pattern" in low:
        return "did not find the pattern in the target expression"
    if "equality or iff proof expected" in low:
        return "equality or iff proof expected"
    if low.startswith("failed to unify"):
        return "failed to unify"
    if low.startswith("could not unify the conclusion of"):
        return "could not unify the conclusion of 'ID'"
    if "made no progress" in low:
        return "made no progress"
    if "insufficient number of binders" in low or "no additional binders" in low:
        return "insufficient number of binders"
    if "major premise type is not an inductive type" in low:
        return "major premise type is not an inductive type"
    if "motive is not type correct" in low:
        return "motive is not type correct"
    if "is not an inductive datatype" in low or "is not an inductive type" in low:
        return "'ID' is not an inductive datatype"
    if low.startswith("could not unify the type of"):
        return "could not unify the type of 'ID'"
    if "no applicable constructor" in low:
        return "no applicable constructor found"
    if "result is not type correct" in low:
        return "result is not type correct"
    if "works for inductive types with exactly" in low:
        return "requires an inductive type with NUM constructors"
    if low.startswith("failed for proposition"):
        return "failed for proposition"
    if low.startswith("proved that the proposition"):
        return "proved the proposition"
    if low.startswith("the left-hand side"):
        return "the left-hand side does not match the right-hand side"
    if "expected the goal to be a binary relation" in low:
        return "expected the goal to be a binary relation"
    if "no if-then-else conditions to split" in low:
        return "no if-then-else conditions to split"
    if low.startswith("failed to prove the goal"):
        return "failed to prove the goal"
    if low.startswith(("`", "'")) or " : " in low:
        return "'TERM'"
    return replace_dynamic(low)


def tactic_template(line: str) -> str:
    """Return a tactic-error template preserving meaningful failure suffixes and masking variable payloads."""
    low = lower_initial(line)
    folded = low.casefold()
    if (
        "made no progress" in folded
        and (
            folded.startswith("tactic ")
            or folded.startswith("field_simp ")
            or re.match(r"^(?:`[^`]+`|'[^']+'|[a-z][a-z0-9_]*) made no progress", low)
        )
    ):
        return "tactic 'ID' made no progress"
    match = re.match(r"^tactic\s+(?:'([^']+)'|`([^`]+)`)\s+failed(?:\s+with\s+a\s+nested\s+error:|\s*[:,]\s*(.*))?$", low)
    if match:
        suffix = match.group(3)
        if "nested error" in low and suffix is None:
            suffix = "nested error"
        return "tactic 'ID' failed" + (f", {tactic_suffix_template(suffix)}" if suffix else "")
    match = re.match(r"^aesop: error in norm simp: tactic\s+(?:'[^']+'|`[^`]+`)\s+failed(?:\s+with\s+a\s+nested\s+error:|\s*[:,]\s*(.*))?$", low)
    if match:
        suffix = match.group(1) or ("nested error" if "nested error" in low else "")
        return "aesop: error in norm simp: tactic 'ID' failed" + (
            f", {tactic_suffix_template(suffix)}" if suffix else ""
        )
    if low in {"no goals to be solved", "no goals to be solved."}:
        return "no goals to be solved"
    if low.startswith("the rfl tactic failed"):
        return "tactic 'ID' failed, possible reasons"
    if low.startswith("invalid rewrite argument:"):
        return "invalid rewrite argument: expected an equality or iff proof or definition name"
    if low.startswith("invalid alternative name"):
        return "invalid alternative name 'ID'"
    if low.startswith("alternative ") and "has not been provided" in low:
        return "alternative 'ID' has not been provided"
    if low.startswith("case tag"):
        return "case tag 'ID' not found"
    if low.startswith("field_simp made no progress at"):
        return "field_simp made no progress at 'ID'"
    if low.startswith("rcases tactic failed:"):
        if "not an inductive datatype" in low or "not an inductive type" in low:
            return "rcases tactic failed: 'ID' is not an inductive datatype"
        return "rcases tactic failed: 'TERM'"
    if low.startswith("interval_cases failed: could not find upper bound on"):
        return "interval_cases failed: could not find upper bound on 'TERM'"
    if low.startswith("interval_cases failed: could not find lower bound on"):
        return "interval_cases failed: could not find lower bound on 'TERM'"
    if low.startswith("interval_cases failed: could not find bounds on"):
        return "interval_cases failed: could not find bounds on 'TERM'"
    if low.startswith("interval_cases failed: unsupported type"):
        return "interval_cases failed: unsupported type 'TYPE'"
    if low.startswith("couldn't rearrange comparison"):
        return "couldn't rearrange comparison 'TERM'"
    if low.startswith("not a comparison:"):
        return "not a comparison: 'TERM'"
    if low.startswith("unexpected term") and "expected single reference to variable" in low:
        return "unexpected term 'ID'; expected single reference to variable"
    if low.startswith("no applicable extensionality theorem found for"):
        return "no applicable extensionality theorem found for 'TYPE'"
    if folded.startswith("this extensionality tactic only applies to equalities"):
        return "extensionality tactic only applies to equalities, not 'TYPE'"
    if folded.startswith("applyexttheorem only applies to equations"):
        return "extensionality tactic only applies to equalities, not 'TYPE'"
    if folded.startswith("dependent elimination failed"):
        return "dependent elimination failed, failed to solve equation"
    return replace_dynamic(low)


def resource_template(line: str) -> str:
    """Return a resource-limit template with concrete locations and numeric limits parameterized."""
    low = lower_initial(line)
    if "timeout at" in low and "maximum number of heartbeats" in low:
        return "(deterministic) timeout at 'ID', maximum number of heartbeats (NUM) has been reached"
    return replace_dynamic(low)


def aggregate_template(category: str, line: str) -> str:
    """Dispatch a diagnostic header to its category-specific deterministic template function."""
    if category == "Syntax error":
        return syntax_template(line)
    if category == "Unresolved name":
        return name_template(line)
    if category == "Type mismatch":
        return type_template(line)
    if category == "Missing instance":
        return instance_template(line)
    if category == "Tactic failure":
        return tactic_template(line)
    if category == "Resource exhaustion":
        return resource_template(line)
    return lower_initial(line)


def compiler_template(category: str, message: str) -> str:
    """Return the historical compiler-shaped template for a full diagnostic.

    Category comes from classify_error. Only the header drives template
    grouping, so differing goal contexts do not create different templates;
    callers preserve the complete original message separately.
    """
    lines = message.splitlines()
    return aggregate_template(category, lines[0] if lines else "")
