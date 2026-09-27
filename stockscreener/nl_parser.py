"""Plain-English strategy condition parser.

Translates lines like "150 SMA > 220 EMA" or "Stock must have dipped below
220 EMA at least once in the past 90 trading days" into the JSON condition
schema consumed by strategy_engine.py (see workflows/define_strategy.md).

Deterministic regex-based parsing on purpose — no LLM call. Strategy logic
must be reproducible: the same input line always produces the same JSON,
and every miss is reported so the user can reword rather than guess.
"""

import re
from typing import Dict, List, Optional, Tuple

# Ordered longest-phrase-first so "greater than or equal to" is matched
# before "greater than".
_OPERATOR_ALIASES = [
    (">=", ">="), ("<=", "<="), ("==", "=="), ("!=", "!="),
    ("greater than or equal to", ">="), ("less than or equal to", "<="),
    ("no less than", ">="), ("no more than", "<="),
    ("at least", ">="), ("at most", "<="),
    ("is equal to", "=="), ("equal to", "=="), ("equals", "=="),
    ("is not equal to", "!="), ("not equal to", "!="),
    ("greater than", ">"), ("more than", ">"), ("above", ">"), ("exceeds", ">"),
    ("less than", "<"), ("below", "<"), ("under", "<"),
    (">", ">"), ("<", "<"),
]
_OPERATOR_REGEX = re.compile(
    "(" + "|".join(re.escape(phrase) for phrase, _ in sorted(
        _OPERATOR_ALIASES, key=lambda p: -len(p[0])
    )) + ")",
    re.IGNORECASE,
)
_OPERATOR_MAP = {phrase.lower(): sym for phrase, sym in _OPERATOR_ALIASES}

_DIP_REGEX = re.compile(
    r"(?:dipped|dropped|fell|traded|closed)\s+below\s+(?:the\s+)?(.+?)\s+"
    r"(?:at\s*least\s*once\s+)?(?:in|over|during)\s+the\s+(?:past|last)\s+"
    r"(\d+)\s+(?:trading\s+)?days",
    re.IGNORECASE,
)

# (regex, template) — template may reference regex groups via {0}, {1}, ...
_METRIC_PATTERNS = [
    (re.compile(r"^(\d+)\s*-?\s*(?:day)?\s*sma$", re.IGNORECASE), "sma{0}"),
    (re.compile(r"^(\d+)\s*-?\s*(?:day)?\s*ema$", re.IGNORECASE), "ema{0}"),
    (re.compile(r"^price\s*\(?\s*close\s*\)?$", re.IGNORECASE), "price"),
    (re.compile(r"^(?:current\s+)?price$", re.IGNORECASE), "price"),
    (re.compile(r"^close(?:\s+price)?$", re.IGNORECASE), "price"),
    (re.compile(r"^52\s*-?\s*w(?:ee)?k\s*low$", re.IGNORECASE), "52w_low"),
    (re.compile(r"^rsi\s*\(?14\)?$", re.IGNORECASE), "rsi14"),
    (re.compile(r"^rsi$", re.IGNORECASE), "rsi14"),
    (re.compile(r"^p\s*/?\s*e(?:\s+ratio)?$", re.IGNORECASE), "pe_ratio"),
    (re.compile(r"^forward\s+p\s*/?\s*e$", re.IGNORECASE), "forward_pe"),
    (re.compile(r"^p\s*/?\s*b(?:\s+ratio)?$", re.IGNORECASE), "pb_ratio"),
    (re.compile(r"^debt\s*(?:to|/)\s*equity$", re.IGNORECASE), "debt_to_equity"),
    (re.compile(r"^(?:roe|return\s+on\s+equity)$", re.IGNORECASE), "roe"),
    (re.compile(r"^profit\s+margin$", re.IGNORECASE), "profit_margin"),
    (re.compile(r"^revenue\s+growth$", re.IGNORECASE), "revenue_growth"),
    (re.compile(r"^earnings\s+growth$", re.IGNORECASE), "earnings_growth"),
    (re.compile(r"^dividend\s+yield$", re.IGNORECASE), "dividend_yield"),
    (re.compile(r"^market\s+cap(?:italization)?$", re.IGNORECASE), "market_cap"),
    (re.compile(r"^volume$", re.IGNORECASE), "volume"),
    (re.compile(r"^(?:20[- ]?day\s+)?avg(?:erage)?\s+volume$", re.IGNORECASE), "avg_volume_20d"),
    (re.compile(r"^macd\s+signal$", re.IGNORECASE), "macd_signal"),
    (re.compile(r"^macd$", re.IGNORECASE), "macd"),
    (re.compile(r"^(\d+)\s*(?:day|d)\s*%?\s*change$", re.IGNORECASE), "pct_change_{0}d"),
    (re.compile(r"^(\d+)\s*(?:month|m)\s*%?\s*change$", re.IGNORECASE), "pct_change_{0}m"),
    (re.compile(r"^(\d+)\s*(?:year|y)\s*%?\s*change$", re.IGNORECASE), "pct_change_{0}y"),
]


class ParseError(Exception):
    """A single condition line could not be understood."""


def resolve_metric(phrase: str, metrics_registry: Dict) -> Optional[str]:
    """Map a plain-English phrase (e.g. '150 SMA', 'Price(Close)') to a metric key.

    Returns None if the phrase doesn't match any known pattern or resolves
    to a metric that isn't in the registry.
    """
    cleaned = phrase.strip().strip(".")
    for pattern, template in _METRIC_PATTERNS:
        m = pattern.match(cleaned)
        if m:
            key = template.format(*m.groups()) if m.groups() else template
            if key in metrics_registry:
                return key
            return None
    if cleaned.lower() in metrics_registry:
        return cleaned.lower()
    return None


def _parse_multiplier_operand(text: str, metrics_registry: Dict) -> Optional[Tuple[str, float]]:
    """Parse '1.25*52 week low' or '25% above 52 week low' -> (metric_key, multiplier)."""
    m = re.match(r"^([\d.]+)\s*[*x]\s*(.+)$", text.strip(), re.IGNORECASE)
    if m:
        multiplier = float(m.group(1))
        metric_key = resolve_metric(m.group(2), metrics_registry)
        if metric_key:
            return metric_key, multiplier
        return None

    m = re.match(r"^([\d.]+)\s*%\s*(above|over|below|under)\s+(.+)$", text.strip(), re.IGNORECASE)
    if m:
        pct = float(m.group(1))
        direction = m.group(2).lower()
        metric_key = resolve_metric(m.group(3), metrics_registry)
        if not metric_key:
            return None
        multiplier = 1 + pct / 100 if direction in ("above", "over") else 1 - pct / 100
        return metric_key, multiplier

    return None


def _parse_operand(text: str, metrics_registry: Dict) -> Dict:
    """Parse one side of a comparison into a condition operand fragment."""
    text = text.strip()

    multiplied = _parse_multiplier_operand(text, metrics_registry)
    if multiplied:
        metric_key, multiplier = multiplied
        return {"compare_type": "metric", "compare_metric": metric_key, "multiplier": multiplier}

    metric_key = resolve_metric(text, metrics_registry)
    if metric_key:
        return {"compare_type": "metric", "compare_metric": metric_key}

    try:
        return {"compare_type": "value", "value": float(text)}
    except ValueError:
        raise ParseError(f"Could not understand '{text}' as a known metric or number")


def parse_line(line: str, metrics_registry: Dict) -> Dict:
    """Parse a single plain-English condition line into a condition dict.

    Raises ParseError with a human-readable reason if the line can't be parsed.
    """
    line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
    line = re.sub(r"^(?:stock\s+must\s+have|stock\s+must|must\s+have)\s+", "", line, flags=re.IGNORECASE)
    if not line:
        raise ParseError("Empty line")

    dip_match = _DIP_REGEX.search(line)
    if dip_match:
        metric_phrase, days = dip_match.group(1), int(dip_match.group(2))
        compare_level = resolve_metric(metric_phrase, metrics_registry)
        if not compare_level:
            raise ParseError(f"Could not understand '{metric_phrase}' as a known metric")
        return {"condition_type": "dipped_below", "compare_level": compare_level, "days": days}

    op_match = _OPERATOR_REGEX.search(line)
    if not op_match:
        raise ParseError(
            "No comparison operator found (expected something like >, <, or 'greater than')"
        )

    op_sym = _OPERATOR_MAP[op_match.group(1).lower()]
    left_text = line[: op_match.start()].strip()
    right_text = line[op_match.end():].strip()
    # Strip a trailing free-text explanation after a dash, e.g.
    # "...52week low --Price should be 25% above 52week low" or
    # "...52week low –Price should be 25% above 52week low"
    right_text = re.split(r"\s[-–—]{1,2}", right_text)[0].strip()

    if not left_text or not right_text:
        raise ParseError("Comparison is missing a left-hand or right-hand side")

    left = _parse_operand(left_text, metrics_registry)
    right = _parse_operand(right_text, metrics_registry)

    if left["compare_type"] != "metric":
        raise ParseError(f"Left-hand side '{left_text}' must be a metric, not a fixed number")

    condition = {"metric": left["compare_metric"], "operator": op_sym}
    condition.update({k: v for k, v in right.items()})
    return condition


def parse_conditions_text(text: str, metrics_registry: Dict) -> Tuple[Dict, List[Dict]]:
    """Parse multiple plain-English condition lines into a strategy root node.

    Returns (root_node, errors) where root_node is {"logic": "AND", "items": [...]}
    built from every line that parsed successfully, and errors is a list of
    {"line_number", "line", "reason"} for lines that didn't.
    """
    items = []
    errors = []

    for i, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.lower().startswith("condition"):
            continue
        try:
            items.append(parse_line(line, metrics_registry))
        except ParseError as e:
            errors.append({"line_number": i, "line": raw_line, "reason": str(e)})

    return {"logic": "AND", "items": items}, errors
