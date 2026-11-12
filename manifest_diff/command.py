"""Build a serializable offline manifest preview."""

from dataclasses import asdict
from decimal import Decimal, InvalidOperation

from .differ import diff_workloads
from .formatter import decimal_text, render_markdown
from .git_reader import read_git_states
from .parser import ManifestError


def node_price(value):
    try:
        price = Decimal(str(value))
        if not price.is_finite() or price < 0:
            raise InvalidOperation
        return price
    except InvalidOperation as exc:
        raise ManifestError("node-monthly-cost must be a finite non-negative number") from exc


def _serialize(value):
    if isinstance(value, Decimal):
        return decimal_text(value)
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_serialize(v) for v in value]
    return value


def build_preview(base, head, repo=".", node_monthly_cost=None):
    price = None if node_monthly_cost is None else node_price(node_monthly_cost)
    base_commit, head_commit, before, after = read_git_states(base, head, repo)
    changes = diff_workloads(before, after)
    return {
        "schema_version": 1,
        "base": base_commit,
        "head": head_commit,
        "changes": _serialize([asdict(c) for c in changes]),
        "pricing": {"currency": "USD", "node_monthly_cost": None if price is None else decimal_text(price),
                    "monthly_allocation_delta": None, "billing_delta": None,
                    "reason": "Node capacity and placement are not modeled."},
        "markdown": render_markdown(changes, price),
    }
