"""Pre-flight VDS query validation against datasource metadata.

All functions are synchronous and pure — no HTTP, no I/O.
Validation rules are ported from the Tableau MCP TypeScript validators.

Primary entry point: ``validate_query(request, schema)`` runs all applicable
rules and returns non-blocking context-filter warnings. Structural and
metadata rule violations raise ``ValidationError``.
"""

from __future__ import annotations

import datetime
from typing import Any

from query_tableau_data_py.errors import ValidationError
from query_tableau_data_py.models import (
    DatasourceParameter,
    DatasourceSchema,
    FieldMeta,
    QueryField,
    QueryFilter,
    QueryParameter,
    QueryRequest,
)

# ---------------------------------------------------------------------------
# Aggregation compatibility map
# ---------------------------------------------------------------------------

_ALLOWED_AGGREGATIONS: dict[str, set[str]] = {
    "INTEGER": {
        "SUM",
        "AVG",
        "MEDIAN",
        "COUNT",
        "COUNTD",
        "MIN",
        "MAX",
        "STDEV",
        "VAR",
    },
    "REAL": {
        "SUM",
        "AVG",
        "MEDIAN",
        "COUNT",
        "COUNTD",
        "MIN",
        "MAX",
        "STDEV",
        "VAR",
    },
    "STRING": {"MIN", "MAX", "COUNT", "COUNTD"},
    "BOOLEAN": {"MIN", "MAX", "COUNT", "COUNTD"},
    "DATE": {
        "MIN",
        "MAX",
        "COUNT",
        "COUNTD",
        "YEAR",
        "QUARTER",
        "MONTH",
        "WEEK",
        "DAY",
        "TRUNC_YEAR",
        "TRUNC_QUARTER",
        "TRUNC_MONTH",
        "TRUNC_WEEK",
        "TRUNC_DAY",
    },
    "DATETIME": {
        "MIN",
        "MAX",
        "COUNT",
        "COUNTD",
        "YEAR",
        "QUARTER",
        "MONTH",
        "WEEK",
        "DAY",
        "TRUNC_YEAR",
        "TRUNC_QUARTER",
        "TRUNC_MONTH",
        "TRUNC_WEEK",
        "TRUNC_DAY",
    },
    "SPATIAL": set(),
    "UNKNOWN": set(),
}

_DIMENSION_FILTER_TYPES: set[str] = {
    "SET",
    "DATE",
    "MATCH",
    "QUANTITATIVE_DATE",
    "QUANTITATIVE_RANGE",
    "RELATIVE_DATE",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize(value: str | None) -> str:
    return (value or "").strip().upper()


def _parse_rfc3339(value: str) -> datetime.datetime | None:
    """Best-effort RFC 3339 / ISO 8601 parser."""
    if not value:
        return None
    try:
        # Python 3.11+ supports Z suffix directly via replace
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_compatible_type(value: Any, data_type: str) -> bool:
    """Check if *value* matches a Tableau *data_type* for ANY_VALUE parameters."""
    dt = _normalize(data_type)
    if dt == "INTEGER":
        return isinstance(value, int) and not isinstance(value, bool)
    if dt in ("REAL", "FLOAT"):
        return _is_numeric(value)
    if dt == "STRING":
        return isinstance(value, str)
    if dt == "BOOLEAN":
        return isinstance(value, bool)
    if dt in ("DATE", "DATETIME"):
        return _parse_rfc3339(str(value)) is not None
    return True  # Unknown types pass through


# ---------------------------------------------------------------------------
# Structural validation (no metadata needed)
# ---------------------------------------------------------------------------


def validate_fields(fields: list[QueryField]) -> None:
    """Validate structural rules for query fields.

    Raises:
        ValidationError: On any structural rule violation.
    """
    if not fields:
        raise ValidationError(
            status_code=None,
            tableau_error_message="Query must include at least one field.",
        )

    seen_sort_priorities: dict[int, str] = {}

    for field in fields:
        caption = (field.field_caption or "").strip()
        if not caption:
            raise ValidationError(
                status_code=None,
                tableau_error_message="Field has an empty fieldCaption.",
            )

        if field.function and field.calculation:
            raise ValidationError(
                status_code=None,
                tableau_error_message=(
                    f"Field '{caption}' cannot have both a function and a calculation."
                ),
            )

        if field.max_decimal_places is not None and field.max_decimal_places < 0:
            raise ValidationError(
                status_code=None,
                tableau_error_message=(f"Field '{caption}' has maxDecimalPlaces < 0."),
            )

        if field.sort_priority is not None:
            if field.sort_priority in seen_sort_priorities:
                other = seen_sort_priorities[field.sort_priority]
                raise ValidationError(
                    status_code=None,
                    tableau_error_message=(
                        f"Duplicate sortPriority {field.sort_priority} on fields "
                        f"'{other}' and '{caption}'."
                    ),
                )
            seen_sort_priorities[field.sort_priority] = caption


def validate_filters(filters: list[QueryFilter] | None) -> None:
    """Validate structural rules for query filters.

    Raises:
        ValidationError: On any structural rule violation.
    """
    if not filters:
        return

    seen_captions: set[str] = set()

    for filt in filters:
        caption = (filt.field_caption or "").strip()
        calculation = (filt.calculation or "").strip()

        if not caption and not calculation:
            raise ValidationError(
                status_code=None,
                tableau_error_message=(
                    "Filter has an empty fieldCaption and no calculation."
                ),
            )

        if caption and calculation:
            raise ValidationError(
                status_code=None,
                tableau_error_message=(
                    f"Filter '{caption}' cannot have both a fieldCaption "
                    "and a calculation."
                ),
            )

        if caption:
            if caption in seen_captions:
                raise ValidationError(
                    status_code=None,
                    tableau_error_message=(f"Duplicate filter on field '{caption}'."),
                )
            seen_captions.add(caption)

        ft = _normalize(filt.filter_type)

        # SET, MATCH, and Relative Date filters cannot have functions or calculations
        if ft in ("SET", "MATCH", "RELATIVE_DATE"):
            if calculation:
                raise ValidationError(
                    status_code=None,
                    tableau_error_message=(f"{ft} filter cannot have a calculation."),
                )
            # Forward-compat guard: QueryFilter model currently has no ``function``
            # field, but if one is added later we catch it via the raw dict.
            raw = filt.model_dump(mode="json", exclude_none=True)
            if raw.get("function"):
                raise ValidationError(
                    status_code=None,
                    tableau_error_message=(f"{ft} filter cannot have a function."),
                )

        if ft == "SET":
            if not filt.values:
                target = caption or calculation or "unknown"
                raise ValidationError(
                    status_code=None,
                    tableau_error_message=(
                        f"SET filter on '{target}' has an empty values array."
                    ),
                )

        if ft == "MATCH":
            if not any([filt.starts_with, filt.ends_with, filt.contains]):
                raise ValidationError(
                    status_code=None,
                    tableau_error_message=(
                        "MATCH filter must specify at least one of "
                        "startsWith, endsWith, or contains."
                    ),
                )

        # Quantitative date filter dates must be valid RFC 3339
        if ft == "QUANTITATIVE_DATE":
            for v in filt.values:
                if _parse_rfc3339(str(v)) is None:
                    raise ValidationError(
                        status_code=None,
                        tableau_error_message=(
                            f"QUANTITATIVE_DATE filter value '{v}' is not a "
                            "valid RFC 3339 date."
                        ),
                    )

        # Relative date filter anchorDate must be valid RFC 3339
        if ft == "RELATIVE_DATE" and filt.anchor_date:
            if _parse_rfc3339(filt.anchor_date) is None:
                raise ValidationError(
                    status_code=None,
                    tableau_error_message=(
                        f"Relative date filter anchorDate "
                        f"'{filt.anchor_date}' is not a valid RFC 3339 date."
                    ),
                )

        # Top N filter fieldToMeasure must be non-empty when provided
        if ft in ("TOP", "BOTTOM"):
            if not (filt.field_to_measure or "").strip():
                raise ValidationError(
                    status_code=None,
                    tableau_error_message=(
                        f"{ft} filter must specify a valid fieldToMeasure."
                    ),
                )


# ---------------------------------------------------------------------------
# Metadata validation
# ---------------------------------------------------------------------------


def validate_fields_against_metadata(
    fields: list[QueryField],
    metadata: list[FieldMeta],
) -> list[str]:
    """Validate query fields against datasource metadata.

    Returns a list of human-readable error strings (empty if all pass).
    """
    errors: list[str] = []
    meta_by_name: dict[str, FieldMeta] = {m.name: m for m in metadata}

    bin_fields: list[QueryField] = []
    fields_with_function: list[QueryField] = []

    for field in fields:
        caption = field.field_caption
        exists = caption in meta_by_name
        meta = meta_by_name.get(caption)

        # Fields that define new entities (calculations or bins) do not need
        # to pre-exist in metadata.  Everything else must exist.
        is_new_field = field.calculation is not None or field.bin_size is not None

        if not is_new_field and not exists:
            errors.append(f"Field '{caption}' does not exist in datasource metadata.")
            continue

        # Cannot provide a calculation for an existing field caption, and cannot
        # override an existing calculated field's formula.
        if field.calculation and exists:
            if meta and meta.formula:
                if field.calculation.strip() != meta.formula.strip():
                    errors.append(
                        f"Cannot override the formula for calculated field '{caption}'."
                    )
                # Same formula is allowed — fall through to other checks
            else:
                errors.append(
                    f"Field '{caption}' already exists in the datasource; "
                    "cannot provide a calculation for an existing field."
                )
            continue

        # Cannot modify binSize on a preexisting field
        if field.bin_size is not None and exists:
            errors.append(f"Cannot modify binSize on existing field '{caption}'.")

        if field.bin_size is not None and not exists:
            bin_fields.append(field)

        if field.function:
            fields_with_function.append(field)

        # Aggregation function must be compatible with field data type
        if field.function and exists and meta:
            allowed = _ALLOWED_AGGREGATIONS.get(_normalize(meta.data_type), set())
            if allowed and _normalize(field.function) not in allowed:
                errors.append(
                    f"Function '{field.function}' is not compatible with "
                    f"field '{caption}' of type '{meta.data_type}'."
                )

    # New bin fields must have a corresponding measure field with a function
    if bin_fields and not fields_with_function:
        for bf in bin_fields:
            errors.append(
                f"Bin field '{bf.field_caption}' requires a measure field "
                "with a function in the same query."
            )

    return errors


def validate_parameters_against_metadata(
    parameters: list[QueryParameter],
    metadata_params: list[DatasourceParameter],
) -> list[str]:
    """Validate query parameters against datasource metadata parameters.

    Returns a list of human-readable error strings (empty if all pass).
    """
    errors: list[str] = []
    meta_by_caption: dict[str, Any] = {}

    for mp in metadata_params:
        caption = getattr(mp, "parameter_caption", None)
        if caption:
            meta_by_caption[caption] = mp

    for param in parameters:
        caption = param.parameter_caption
        if not caption:
            continue

        meta = meta_by_caption.get(caption)
        if meta is None:
            errors.append(
                f"Parameter '{caption}' does not exist in datasource metadata."
            )
            continue

        ptype = getattr(meta, "parameter_type", None)
        value = param.value

        if ptype == "ANY_VALUE":
            if not _is_compatible_type(value, meta.data_type):
                errors.append(
                    f"Parameter '{caption}' value '{value}' does not match "
                    f"declared data type '{meta.data_type}'."
                )

        elif ptype == "LIST":
            members = getattr(meta, "members", []) or []
            if value not in members:
                errors.append(
                    f"Parameter '{caption}' value '{value}' is not in the "
                    f"allowed members list: {members}."
                )

        elif ptype == "QUANTITATIVE_DATE":
            parsed = _parse_rfc3339(str(value) if value is not None else "")
            if parsed is None:
                errors.append(
                    f"Parameter '{caption}' value '{value}' is not a valid date."
                )
            else:
                min_date = getattr(meta, "min_date", None)
                max_date = getattr(meta, "max_date", None)
                if min_date:
                    pmin = _parse_rfc3339(min_date)
                    if pmin and parsed < pmin:
                        errors.append(
                            f"Parameter '{caption}' value '{value}' is before "
                            f"the minimum allowed date '{min_date}'."
                        )
                if max_date:
                    pmax = _parse_rfc3339(max_date)
                    if pmax and parsed > pmax:
                        errors.append(
                            f"Parameter '{caption}' value '{value}' is after "
                            f"the maximum allowed date '{max_date}'."
                        )

        elif ptype == "QUANTITATIVE_RANGE":
            if not _is_numeric(value):
                errors.append(f"Parameter '{caption}' value '{value}' is not a number.")
            else:
                vmin = getattr(meta, "min", None)
                vmax = getattr(meta, "max", None)
                if vmin is not None and value < vmin:
                    errors.append(
                        f"Parameter '{caption}' value '{value}' is below the "
                        f"minimum allowed value '{vmin}'."
                    )
                if vmax is not None and value > vmax:
                    errors.append(
                        f"Parameter '{caption}' value '{value}' is above the "
                        f"maximum allowed value '{vmax}'."
                    )

    return errors


# ---------------------------------------------------------------------------
# Context filter warnings (non-blocking)
# ---------------------------------------------------------------------------


def validate_context_filters(request: QueryRequest) -> list[str]:
    """Return warning strings when TOP/BOTTOM filters are combined with
    dimension filters that lack ``context: true``.

    Never raises.
    """
    warnings: list[str] = []
    has_top_bottom = False

    for filt in request.filters:
        ft = _normalize(filt.filter_type)
        if ft in ("TOP", "BOTTOM"):
            has_top_bottom = True
            break

    if not has_top_bottom:
        return warnings

    for filt in request.filters:
        ft = _normalize(filt.filter_type)
        if ft in _DIMENSION_FILTER_TYPES and not filt.context:
            caption = filt.field_caption or filt.calculation or "unknown"
            warnings.append(
                f"Dimension filter '{caption}' is missing context=True. "
                "When combined with TOP/BOTTOM filters, dimension filters "
                "should have context=True for correct result ordering."
            )

    return warnings


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------


def validate_query(
    request: QueryRequest,
    schema: DatasourceSchema,
) -> list[str]:
    """Run all applicable validation rules for a query request.

    1. Structural field validation (raises on failure).
    2. Structural filter validation (raises on failure).
    3. Metadata field validation (collects errors, raises if any).
    4. Metadata parameter validation (collects errors, raises if any).
    5. Context-filter warnings (non-blocking, returned as list).

    Args:
        request: The VDS query request to validate.
        schema: The datasource schema (from ``introspect_datasource``) to validate against.

    Returns:
        List of non-blocking warning strings. Empty list if no warnings.

    Raises:
        ValidationError: If any structural or metadata rule fails.
    """
    # 1. Structural field rules
    validate_fields(request.fields)

    # 2. Structural filter rules
    validate_filters(request.filters)

    # 3. Flatten field metadata
    all_meta: list[FieldMeta] = []
    for group in schema.field_groups:
        all_meta.extend(group.fields)

    # 4. Metadata field rules
    field_errors = validate_fields_against_metadata(request.fields, all_meta)
    if field_errors:
        raise ValidationError(
            status_code=None,
            tableau_error_message="; ".join(field_errors),
        )

    # 5. Parameter rules
    param_errors = validate_parameters_against_metadata(
        request.parameters, schema.parameters
    )
    if param_errors:
        raise ValidationError(
            status_code=None,
            tableau_error_message="; ".join(param_errors),
        )

    # 6. Context-filter warnings (non-blocking)
    return validate_context_filters(request)
