from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Set

from compiler.canonical_schema import (
    ALLOWED_REVIEW_MARKERS,
    ALLOWED_STEP_KINDS,
    CanonicalAbilityModel,
    CanonicalStep,
    ConditionStep,
    KNOWN_CONDITIONS,
    KNOWN_COSTS,
    KNOWN_EFFECTS,
    KNOWN_TARGETS,
    KNOWN_TRIGGERS,
    KNOWN_ZONES,
    RESERVED_BINDINGS,
    BinaryExpr,
    FilterSpec,
    LiteralExpr,
    ReferenceExpr,
    ValueExpr,
    parse_canonical_ability_model,
)


@dataclass
class ValidationIssue:
    code: str
    message: str
    path: str = ""


@dataclass
class ValidationReport:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def add(self, code: str, message: str, path: str = "") -> None:
        self.issues.append(ValidationIssue(code=code, message=message, path=path))


def validate_canonical_model_payload(data: dict[str, Any]) -> ValidationReport:
    report = ValidationReport()
    try:
        model = parse_canonical_ability_model(data)
    except Exception as exc:
        report.add("schema_error", str(exc), path="$")
        return report

    return validate_canonical_model(model)


def validate_canonical_model(model: CanonicalAbilityModel) -> ValidationReport:
    report = ValidationReport()

    if model.trigger not in KNOWN_TRIGGERS:
        report.add("unknown_trigger", f"Unknown trigger '{model.trigger}'", path="trigger")

    _validate_review_markers(report, model.review_reasons, "review_reasons")

    scope: Set[str] = set()
    _validate_steps(report, model.steps, "steps", scope)
    return report


def _validate_steps(report: ValidationReport, steps: Iterable[CanonicalStep], path: str, scope: Set[str]) -> None:
    local_scope = set(scope)
    for idx, step in enumerate(steps):
        step_path = f"{path}[{idx}]"
        if step.kind not in ALLOWED_STEP_KINDS:
            report.add("unknown_step_kind", f"Unknown step kind '{step.kind}'", path=step_path)
            continue

        _validate_review_markers(report, step.review_markers, f"{step_path}.review_markers")

        if step.kind == "cost":
            if step.op not in KNOWN_COSTS and step.op not in KNOWN_EFFECTS:
                report.add("unknown_cost_op", f"Unknown cost op '{step.op}'", path=f"{step_path}.op")
            _validate_target(report, step.target, f"{step_path}.target")
            _validate_zone(report, step.zone, f"{step_path}.zone")
            _validate_filter(report, step.filter, f"{step_path}.filter")
            _validate_expr(report, step.count, local_scope, f"{step_path}.count")
            _validate_store_as(report, step.store_as, local_scope, f"{step_path}.store_as")
        elif step.kind == "condition":
            _validate_condition_step(report, step, local_scope, step_path)
        elif step.kind == "effect":
            if step.op not in KNOWN_EFFECTS and step.op not in KNOWN_COSTS:
                report.add("unknown_effect_op", f"Unknown effect op '{step.op}'", path=f"{step_path}.op")
            _validate_target(report, step.target, f"{step_path}.target")
            _validate_zone(report, step.zone, f"{step_path}.zone")
            _validate_filter(report, step.filter, f"{step_path}.filter")
            _validate_expr(report, step.count, local_scope, f"{step_path}.count")
            _validate_args(report, step.args, local_scope, f"{step_path}.args")
            _validate_store_as(report, step.store_as, local_scope, f"{step_path}.store_as")
        elif step.kind == "select":
            if step.op not in KNOWN_EFFECTS and step.op not in KNOWN_COSTS:
                report.add("unknown_select_op", f"Unknown select op '{step.op}'", path=f"{step_path}.op")
            _validate_target(report, step.target, f"{step_path}.target")
            _validate_zone(report, step.zone, f"{step_path}.zone")
            _validate_filter(report, step.filter, f"{step_path}.filter")
            _validate_expr(report, step.count, local_scope, f"{step_path}.count")
            _validate_store_as(report, step.store_as, local_scope, f"{step_path}.store_as", required=True)
        elif step.kind == "assign":
            _validate_store_as(report, step.store_as, local_scope, f"{step_path}.store_as", required=True)
            _validate_expr(report, step.expr, local_scope, f"{step_path}.expr")
        elif step.kind == "if":
            _validate_condition_step(report, step.condition, local_scope, f"{step_path}.condition")
            branch_scope = set(local_scope)
            _validate_steps(report, step.then, f"{step_path}.then", branch_scope)
            _validate_steps(report, step.else_, f"{step_path}.else", set(local_scope))
        elif step.kind == "choose_one":
            _validate_target(report, step.target, f"{step_path}.target")
            if len(step.branches) < 2:
                report.add("invalid_choose_one", "choose_one must contain at least 2 branches", path=f"{step_path}.branches")
            _validate_store_as(report, step.store_as, local_scope, f"{step_path}.store_as")
            for branch_idx, branch in enumerate(step.branches):
                _validate_steps(report, branch.steps, f"{step_path}.branches[{branch_idx}].steps", set(local_scope))
        elif step.kind == "repeat":
            if step.times is None and step.while_condition is None:
                report.add("invalid_repeat", "repeat requires times or while_condition", path=step_path)
            _validate_expr(report, step.times, local_scope, f"{step_path}.times")
            if step.while_condition is not None:
                _validate_condition_step(report, step.while_condition, local_scope, f"{step_path}.while_condition")
            _validate_steps(report, step.body, f"{step_path}.body", set(local_scope))


def _validate_condition_step(report: ValidationReport, step: ConditionStep, scope: Set[str], path: str) -> None:
    if step.op not in KNOWN_CONDITIONS and step.op not in KNOWN_EFFECTS:
        report.add("unknown_condition_op", f"Unknown condition op '{step.op}'", path=f"{path}.op")
    _validate_args(report, step.args, scope, f"{path}.args")
    _validate_store_as(report, step.store_as, scope, f"{path}.store_as")


def _validate_args(report: ValidationReport, args: dict[str, Any], scope: Set[str], path: str) -> None:
    for key, value in args.items():
        if isinstance(value, dict) and "kind" in value:
            try:
                expr = _coerce_expr(value)
            except Exception as exc:
                report.add("invalid_expr", str(exc), path=f"{path}.{key}")
                continue
            _validate_expr(report, expr, scope, f"{path}.{key}")
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, dict) and "kind" in item:
                    try:
                        expr = _coerce_expr(item)
                    except Exception as exc:
                        report.add("invalid_expr", str(exc), path=f"{path}.{key}[{idx}]")
                        continue
                    _validate_expr(report, expr, scope, f"{path}.{key}[{idx}]")


def _validate_expr(report: ValidationReport, expr: ValueExpr | None, scope: Set[str], path: str) -> None:
    if expr is None:
        return
    if isinstance(expr, ReferenceExpr):
        if expr.name not in scope and expr.name not in RESERVED_BINDINGS:
            report.add("unknown_binding", f"Unknown binding '{expr.name}'", path=path)
    elif isinstance(expr, BinaryExpr):
        _validate_expr(report, expr.left, scope, f"{path}.left")
        _validate_expr(report, expr.right, scope, f"{path}.right")


def _validate_filter(report: ValidationReport, filter_spec: FilterSpec | None, path: str) -> None:
    if filter_spec is None:
        return
    _validate_review_markers(report, filter_spec.review_markers, f"{path}.review_markers")


def _validate_target(report: ValidationReport, target: str | None, path: str) -> None:
    if target is not None and target not in KNOWN_TARGETS and target not in RESERVED_BINDINGS:
        report.add("unknown_target", f"Unknown target '{target}'", path=path)


def _validate_zone(report: ValidationReport, zone: str | None, path: str) -> None:
    if zone is not None and zone not in KNOWN_ZONES:
        report.add("unknown_zone", f"Unknown zone '{zone}'", path=path)


def _validate_store_as(
    report: ValidationReport,
    store_as: str | None,
    scope: Set[str],
    path: str,
    *,
    required: bool = False,
) -> None:
    if not store_as:
        if required:
            report.add("missing_binding", "Expected store_as binding", path=path)
        return
    if store_as in RESERVED_BINDINGS:
        report.add("reserved_binding", f"Binding '{store_as}' is reserved", path=path)
        return
    if store_as in scope:
        report.add("duplicate_binding", f"Binding '{store_as}' already exists in scope", path=path)
        return
    scope.add(store_as)


def _validate_review_markers(report: ValidationReport, markers: Iterable[str], path: str) -> None:
    for idx, marker in enumerate(markers):
        if marker not in ALLOWED_REVIEW_MARKERS:
            report.add("unknown_review_marker", f"Unknown review marker '{marker}'", path=f"{path}[{idx}]")


def _coerce_expr(data: dict[str, Any]) -> ValueExpr:
    kind = data.get("kind")
    if kind == "reference":
        return ReferenceExpr.model_validate(data)
    if kind == "binary":
        return BinaryExpr.model_validate(data)
    return LiteralExpr.model_validate(data)
