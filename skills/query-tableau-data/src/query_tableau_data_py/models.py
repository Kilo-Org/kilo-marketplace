"""Shared Pydantic models for the query_tableau_data_py package."""

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class TableauModel(BaseModel):
    """Base Pydantic model for all Tableau-facing shapes.

    Uses ``extra='ignore'`` for forward compatibility with new Tableau
    fields, and ``populate_by_name=True`` so aliases can be passed as
    keyword arguments.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class FieldPreview(TableauModel):
    """Lightweight field preview from the Metadata API.

    Gives agents a quick sense of available dimensions and measures
    without requiring a full introspection call.
    """

    name: str
    data_type: str = ""
    role: str = ""


class DatasourceSummary(TableauModel):
    """Summary of a published Tableau datasource.

    Returned by catalog discovery; carries enough metadata for an agent
    to rank relevance and decide which datasource to introspect next.
    """

    luid: str
    name: str
    description: str | None = None
    project_name: str | None = None
    owner_name: str | None = None
    has_extracts: bool | None = None
    is_certified: bool | None = None
    tags: list[str] = []
    field_preview: list[FieldPreview] = []
    downstream_workbooks: list["WorkbookRef"] = []


# ── Workbook & View catalog models ────────────────────────────────


class WorkbookRef(TableauModel):
    """Lightweight reference to a workbook (luid + name only).

    Used wherever a full ``WorkbookSummary`` is too heavy — e.g. in
    ``DatasourceSummary.downstream_workbooks``.
    """

    luid: str
    name: str


class DatasourceRef(TableauModel):
    """Lightweight reference to a published datasource (luid + name only).

    Used in ``EmbeddedDatasourceRef.upstream_datasources`` to link an
    embedded datasource back to the published datasource it layers on top of.
    """

    luid: str
    name: str


class SheetRef(TableauModel):
    """Sheet reference within a workbook catalog entry or dashboard."""

    luid: str
    name: str
    index: int | None = None


class DashboardRef(TableauModel):
    """Dashboard reference within a workbook catalog entry or sheet."""

    luid: str
    name: str
    index: int | None = None


class EmbeddedDatasourceRef(TableauModel):
    """Embedded datasource reference with upstream published datasource links.

    Carries only the fields needed for catalog-level navigation.  Full
    field-level detail is reserved for ``introspect_workbook``.
    """

    name: str
    upstream_datasources: list[DatasourceRef] = []


class WorkbookSummary(TableauModel):
    """Summary of a Tableau workbook from catalog discovery.

    The GraphQL path populates ``sheets``, ``dashboards``, and
    ``embedded_datasources``.  The REST fallback path leaves those three
    fields as empty lists — it only provides the top-level workbook
    metadata.
    """

    luid: str
    name: str
    description: str | None = None
    project_name: str | None = None
    owner_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    sheets: list[SheetRef] = []
    dashboards: list[DashboardRef] = []
    embedded_datasources: list[EmbeddedDatasourceRef] = []
    tags: list[str] = []


class ViewSummary(TableauModel):
    """Summary of a view (sheet or dashboard) from catalog discovery.

    ``view_type`` is ``"sheet"`` for individual worksheets and
    ``"dashboard"`` for dashboards.

    For sheets:
    - ``contained_in_dashboards`` lists the dashboards this sheet appears in.
    - ``sheets_in_dashboard`` is always empty.

    For dashboards:
    - ``sheets_in_dashboard`` lists the constituent sheets.
    - ``contained_in_dashboards`` is always empty.

    ``total_view_count`` is populated by the REST path when usage statistics
    are available (``includeUsageStatistics=true``).  The GraphQL path does
    not expose usage data, so this field is ``None`` for GraphQL results.

    On the REST fallback path ``workbook_name`` is ``None`` because the
    REST ``/views`` endpoint only provides ``workbook.id``.
    """

    luid: str
    name: str
    view_type: str = "sheet"  # "sheet" or "dashboard"
    content_url: str | None = None
    workbook_luid: str | None = None
    workbook_name: str | None = None
    index: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    total_view_count: int | None = None
    contained_in_dashboards: list[DashboardRef] = []  # sheets only
    sheets_in_dashboard: list[SheetRef] = []  # dashboards only


# ── Introspection models ──────────────────────────────────────────


class FieldMeta(TableauModel):
    """Enriched metadata for a single datasource field.

    Base properties come from VDS ``readMetadata``; enrichment properties
    (``description``, ``data_category``, ``semantic_role``) come from the
    Metadata API GraphQL layer when available.
    """

    name: str
    data_type: str
    column_class: str
    logical_table_id: str | None = None
    default_aggregation: str | None = None
    formula: str | None = None
    description: str | None = None
    data_category: str | None = None
    semantic_role: str | None = None

    @property
    def caption(self) -> str:
        """User-facing field caption (alias for ``name``).

        Use this value as ``QueryField.field_caption`` when building VDS
        query requests.
        """
        return self.name

    _DIMENSION_TYPES = frozenset({"STRING", "DATE", "DATETIME", "BOOLEAN"})
    _MEASURE_TYPES = frozenset({"INTEGER", "REAL", "FLOAT"})

    @property
    def role(self) -> str:
        """Resolved field role: ``DIMENSION``, ``MEASURE``, or ``UNKNOWN``.

        Returns ``column_class`` when populated by VDS.  On Tableau versions
        where ``column_class`` is empty, infers the role from ``data_type``.
        """
        if self.column_class:
            return self.column_class
        if self.data_type in self._DIMENSION_TYPES:
            return "DIMENSION"
        if self.data_type in self._MEASURE_TYPES:
            return "MEASURE"
        return "UNKNOWN"


class LogicalTable(TableauModel):
    """Logical table within a datasource model."""

    logical_table_id: str
    caption: str
    description: str | None = None


class LogicalTableRelationship(TableauModel):
    """Relationship between two logical tables."""

    from_table_id: str
    to_table_id: str
    expression: dict = {}


# ── Parameter discriminated union ─────────────────────────────────


class AnyValueParameter(TableauModel):
    """Parameter that accepts any value matching its data type."""

    parameter_type: Literal["ANY_VALUE"]
    parameter_caption: str
    data_type: str
    parameter_name: str | None = None
    value: Any | None = None


class ListParameter(TableauModel):
    """Parameter with a predefined list of allowed values."""

    parameter_type: Literal["LIST"]
    parameter_caption: str
    data_type: str
    parameter_name: str | None = None
    value: Any | None = None
    members: list[Any] = []


class QuantitativeDateParameter(TableauModel):
    """Date parameter with optional range and period constraints."""

    parameter_type: Literal["QUANTITATIVE_DATE"]
    parameter_caption: str
    data_type: str
    parameter_name: str | None = None
    value: str | None = None
    min_date: str | None = None
    max_date: str | None = None
    period_value: int | None = None
    period_type: str | None = None


class QuantitativeRangeParameter(TableauModel):
    """Numeric parameter with optional min, max, and step constraints."""

    parameter_type: Literal["QUANTITATIVE_RANGE"]
    parameter_caption: str
    data_type: str
    parameter_name: str | None = None
    value: float | int | None = None
    min: float | int | None = None
    max: float | int | None = None
    step: float | int | None = None


DatasourceParameter = Annotated[
    Union[
        AnyValueParameter,
        ListParameter,
        QuantitativeDateParameter,
        QuantitativeRangeParameter,
    ],
    Field(discriminator="parameter_type"),
]


# ── Higher-order introspection models ──────────────────────────────


class FieldGroup(TableauModel):
    """Fields grouped by their logical table."""

    logical_table_id: str | None = None
    logical_table_caption: str | None = None
    fields: list[FieldMeta] = []


class DatasourceModel(TableauModel):
    """Logical table model returned by VDS ``getDatasourceModel``.

    Only available on Tableau 2025.3+; ``None`` on earlier versions.
    """

    logical_tables: list[LogicalTable] = []
    logical_table_relationships: list[LogicalTableRelationship] = []


class DatasourceSchema(TableauModel):
    """Comprehensive, merged metadata for a single datasource.

    Produced by ``introspect_datasource.introspect()``. Contains all queryable fields
    (from VDS ``readMetadata``), optional GraphQL enrichment, and the
    logical-table model when the server supports it.
    """

    luid: str
    name: str | None = None
    description: str | None = None
    datasource_model: DatasourceModel | None = None
    field_groups: list[FieldGroup] = []
    parameters: list[DatasourceParameter] = []


# ── Query models ────────────────────────────────────────────────────


class QueryField(TableauModel):
    """A field requested in a VDS query.

    Agents reference fields by ``field_caption`` (the user-visible name).
    Optional ``function`` applies an aggregation (e.g. ``SUM``).
    Optional ``calculation`` provides a custom Tableau formula.
    Optional ``field_alias`` controls the response key name — without it,
    aggregated fields return as ``FUNCTION(fieldCaption)`` (e.g. ``SUM(Sales)``).
    """

    field_caption: str = Field(..., alias="fieldCaption")
    field_alias: str | None = Field(default=None, alias="fieldAlias")
    function: str | None = Field(default=None, alias="function")
    calculation: str | None = Field(default=None, alias="calculation")
    sort_priority: int | None = Field(default=None, alias="sortPriority")
    max_decimal_places: int | None = Field(default=None, alias="maxDecimalPlaces")
    bin_size: int | None = Field(default=None, alias="binSize")


class QueryFilter(TableauModel):
    """A filter clause in a VDS query.

    Filter shape varies by ``filter_type`` (SET, MATCH, QUANTITATIVE_DATE,
    etc.).  Common fields are modelled explicitly; extra keys are ignored.
    """

    field_caption: str | None = Field(default=None, alias="fieldCaption")
    calculation: str | None = Field(default=None, alias="calculation")
    filter_type: str | None = Field(default=None, alias="filterType")
    values: list[Any] = Field(default_factory=list, alias="values")
    anchor_date: str | None = Field(default=None, alias="anchorDate")
    period_type: str | None = Field(default=None, alias="periodType")
    period_count: int | None = Field(default=None, alias="periodCount")
    field_to_measure: str | None = Field(default=None, alias="fieldToMeasure")
    starts_with: str | None = Field(default=None, alias="startsWith")
    ends_with: str | None = Field(default=None, alias="endsWith")
    contains: str | None = Field(default=None, alias="contains")
    context: bool | None = Field(default=None, alias="context")
    include_all: bool | None = Field(default=None, alias="includeAll")
    exclude: bool | None = Field(default=None, alias="exclude")


class QueryParameter(TableauModel):
    """A parameter binding in a VDS query."""

    parameter_caption: str | None = Field(default=None, alias="parameterCaption")
    value: Any = Field(default=None, alias="value")
    values: list[Any] = Field(default_factory=list, alias="values")
    date_range: str | None = Field(default=None, alias="dateRange")
    start_date: str | None = Field(default=None, alias="startDate")
    end_date: str | None = Field(default=None, alias="endDate")


class QueryOptions(TableauModel):
    """Options that control how VDS processes and returns data."""

    return_format: Literal["OBJECTS", "ARRAYS"] = Field(
        default="OBJECTS", alias="returnFormat"
    )
    debug: bool = Field(default=False, alias="debug")
    disaggregate: bool = Field(default=False, alias="disaggregate")
    row_limit: int | None = Field(default=None, alias="rowLimit")
    bypass_metadata_cache: bool = Field(default=False, alias="bypassMetadataCache")
    interpret_field_captions_as_field_names: bool = Field(
        default=False, alias="interpretFieldCaptionsAsFieldNames"
    )
    include_hidden_fields: bool = Field(default=False, alias="includeHiddenFields")
    include_group_formulas: bool = Field(default=False, alias="includeGroupFormulas")
    return_server_sent_events: bool = Field(
        default=False, alias="returnServerSentEvents"
    )


class Connection(TableauModel):
    """Database connection credentials for a datasource with embedded auth."""

    connection_luid: str | None = Field(default=None, alias="connectionLuid")
    connection_username: str = Field(..., alias="connectionUsername")
    connection_password: str = Field(..., alias="connectionPassword")


class QueryRequest(TableauModel):
    """Complete VDS query request.

    Serialises to the nested VDS body shape via
    ``modules.query.build_query_payload()``.
    """

    datasource_luid: str
    fields: list[QueryField] = []
    filters: list[QueryFilter] = []
    parameters: list[QueryParameter] = []
    options: QueryOptions = Field(default_factory=QueryOptions)
    connections: list[Connection] | None = None


class QueryResultMetadata(TableauModel):
    """Derived metadata for a query result.

    ``field_captions`` are taken from the request; ``row_count`` and
    ``is_complete`` are computed client-side from the response.
    """

    field_captions: list[str] = []
    row_count: int = 0
    is_complete: bool = True


class QueryResult(TableauModel):
    """Buffered (non-streaming) query result.

    ``rows`` is a list of dicts for ``OBJECTS`` format or a list of lists
    for ``ARRAYS`` format.
    """

    rows: list[dict[str, Any]] | list[list[Any]] = []
    metadata: QueryResultMetadata = Field(default_factory=QueryResultMetadata)
    debug_info: dict[str, Any] | None = None


class QueryChunk(TableauModel):
    """A single chunk yielded by the streaming query path.

    ``index`` is the zero-based chunk sequence number.
    ``is_final`` is ``True`` for the last chunk in the stream.
    """

    index: int = 0
    data: list[dict[str, Any]] | list[list[Any]] = []
    is_final: bool = False


class SupportedFunction(TableauModel):
    """A Tableau function supported by a specific datasource."""

    name: str
    argument_types: list[str] = Field(default_factory=list, alias="argumentTypes")
    return_type: str = Field(default="", alias="returnType")


# ── Workbook introspection models ──────────────────────────────────


class SheetFieldInstance(TableauModel):
    """A field used by a specific sheet, or a field in an embedded datasource.

    ``formula`` is populated for ``CalculatedField`` nodes only; it is
    ``None`` for ``ColumnField`` and ``DatasourceField`` nodes.
    """

    name: str
    data_type: str | None = None
    role: str | None = None
    formula: str | None = None


class SheetDetail(TableauModel):
    """Detailed sheet with field instances and worksheet-level calculated fields.

    ``field_instances`` — fields placed on the sheet's shelves (from
    ``sheetFieldInstances`` in the Metadata API).

    ``worksheet_fields`` — calculated fields authored directly on the
    sheet (from ``worksheetFields``).

    ``contained_in_dashboards`` — dashboards that embed this sheet.
    """

    luid: str
    name: str
    index: int | None = None
    field_instances: list[SheetFieldInstance] = []
    worksheet_fields: list[SheetFieldInstance] = []
    contained_in_dashboards: list[DashboardRef] = []


class DashboardDetail(TableauModel):
    """Dashboard with its component sheet references."""

    luid: str
    name: str
    index: int | None = None
    sheets: list[SheetRef] = []


class EmbeddedDatasourceDetail(TableauModel):
    """Embedded datasource with fields and upstream published datasource links.

    ``upstream_datasources`` provides the bridge from workbook to
    published datasource for further VDS introspection.
    """

    name: str
    has_extracts: bool | None = None
    fields: list[SheetFieldInstance] = []
    upstream_datasources: list[DatasourceRef] = []


class WorkbookSchema(TableauModel):
    """Comprehensive introspection result for a single workbook.

    Produced by ``introspect_workbook.introspect_workbook()``.

    ``parameters`` is a plain list of dicts — Metadata API parameter
    shapes differ from VDS parameters, so raw data is preserved.
    """

    luid: str
    name: str
    description: str | None = None
    project_name: str | None = None
    owner_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    sheets: list[SheetDetail] = []
    dashboards: list[DashboardDetail] = []
    embedded_datasources: list[EmbeddedDatasourceDetail] = []
    parameters: list[dict] = []


# ── Server info model (pre-auth probe) ─────────────────────────────


class ServerInfo(TableauModel):
    """Server version from the unauthenticated /serverinfo endpoint.

    Populated by auth.server_info() during Session.__enter__(), before
    sign_in(). Used to gate VDS feature availability and auto-negotiate
    the REST API version.
    """

    product_version: str  # e.g. "2025.3"
    build_number: str  # e.g. "20253.24.0919.1043"
    rest_api_version: str  # e.g. "3.27"
    vds_available: bool = False
    vds_feature_tier: str = "none"  # "none"|"2025.1"|"2025.2"|"2025.3"|"2026.1"


# ── Scope models (fast site-size probe) ────────────────────────────


class ProjectItem(TableauModel):
    """A Tableau project from the REST API.

    Returned within ``SiteScope.projects`` by ``scope_site()``.
    ``parent_project_id`` is ``None`` for top-level projects.
    ``content_permissions`` is the project's content permission mode
    (e.g. ``"ManagedByOwner"`` or ``"LockedToProject"``).
    """

    luid: str
    name: str
    description: str | None = None
    parent_project_id: str | None = None
    content_permissions: str | None = None


class SiteScope(TableauModel):
    """Fast site-scale snapshot from minimal REST probes.

    Returned by ``scope_site()`` / ``session.scope_site()``.

    Asset counts come from three ``pageSize=1`` REST requests (one per content
    type) — each round trip returns ``pagination.totalAvailable`` without
    iterating through items.  The single item in each response is discarded.

    Projects come from a single paginated REST call (``pageSize=1000``), which
    is usually one HTTP request.  Pagination continues if the site has >1000
    projects.

    Use the counts to branch discovery strategy before committing to any
    ``inventory_*`` call:

    - ``datasource_count < 500`` and ``workbook_count < 1000``:
      full inventory is safe in the REPL.
    - Otherwise: use ``filter_project``, ``is_certified``, and explicit
      ``limit`` values; fall back to ``scripts/`` for exhaustive pulls.
    """

    datasource_count: int
    workbook_count: int
    view_count: int
    projects: list[ProjectItem] = []
    server_info: ServerInfo | None = None


# ── Inventory models (REST-only flat catalog) ───────────────────────


class DatasourceInventoryItem(TableauModel):
    """Flat inventory entry for a published datasource (REST-only).

    Returned by ``inventory_datasources()``.  Deliberately slimmer than
    ``DatasourceSummary`` — no nested relationship data, no field preview.
    Use ``datasource_lineage()`` if downstream workbook or upstream table
    relationships are needed.

    Note: ``owner_id`` is the owner's LUID, not their display name.
    The REST ``GET /datasources`` endpoint returns ``owner.id`` only.
    Name resolution requires a separate users call.
    """

    luid: str
    name: str
    description: str | None = None
    project_name: str | None = None
    owner_id: str | None = None  # REST returns owner.id (luid), not owner.name
    has_extracts: bool | None = None
    is_certified: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None
    content_url: str | None = None
    tags: list[str] = []


class ViewInventoryItem(TableauModel):
    """Flat inventory entry for a view (REST-only).

    Returned by ``inventory_views()``.  Always includes ``total_view_count``
    because ``inventory_views()`` always requests ``includeUsageStatistics=true``.

    Note: ``workbook_luid`` is populated from ``workbook.id`` in the REST
    response. The REST ``GET /views`` endpoint does not return workbook name —
    resolving the workbook name requires a separate call to
    ``inventory_workbooks()`` and a join on ``workbook_luid``.
    """

    luid: str
    name: str
    content_url: str | None = None
    workbook_luid: str | None = None  # REST: workbook.id only, no name
    owner_id: str | None = None
    total_view_count: int | None = None


class WorkbookInventoryItem(TableauModel):
    """Flat inventory entry for a workbook (REST-only).

    Returned by ``inventory_workbooks()``.  Deliberately slimmer than
    ``WorkbookSummary`` — no sheets, dashboards, or embedded datasource lists.
    Use ``workbook_lineage()`` for relationship data.

    Note: ``owner_id`` is the owner's LUID, not their display name.
    """

    luid: str
    name: str
    description: str | None = None
    project_name: str | None = None
    owner_id: str | None = None  # REST returns owner.id (luid), not owner.name
    content_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    tags: list[str] = []


# ── Lineage models (targeted GraphQL per-asset queries) ────────────


class UpstreamTableRef(TableauModel):
    """Reference to an upstream database table for a datasource.

    Returned within ``DatasourceLineage.upstream_tables``.
    ``database_name`` is the name of the database hosting this table,
    parsed from the nested ``database { name }`` GraphQL field.
    """

    name: str
    database_name: str | None = None


class UpstreamDatabaseRef(TableauModel):
    """Reference to an upstream database (connection) for a datasource or workbook.

    Returned within ``DatasourceLineage.upstream_databases`` and
    ``WorkbookLineage.upstream_databases``.
    ``connection_type`` is the Tableau connection type string (e.g. ``"postgres"``).
    """

    name: str
    connection_type: str | None = None


class DatasourceLineage(TableauModel):
    """Targeted lineage result for a single published datasource.

    Returned by ``lineage.datasource_lineage()``.  Answers "what consumes this
    datasource, and where does its data come from?" with one GraphQL request.

    ``field_preview`` contains the first 30 fields from the Metadata API,
    giving a lightweight sense of available dimensions and measures without
    a full introspection call.

    Downstream relationships are populated from:
      - ``downstreamWorkbooks``  → ``downstream_workbooks``
      - ``downstreamSheets``     → ``downstream_sheets``
      - ``downstreamDashboards`` → ``downstream_dashboards``

    Upstream relationships are populated from:
      - ``upstreamTables``    → ``upstream_tables``
      - ``upstreamDatabases`` → ``upstream_databases``
    """

    luid: str
    name: str
    description: str | None = None
    project_name: str | None = None
    owner_name: str | None = None
    is_certified: bool | None = None
    has_extracts: bool | None = None
    downstream_workbooks: list[WorkbookRef] = []
    downstream_sheets: list[SheetRef] = []
    downstream_dashboards: list[DashboardRef] = []
    upstream_tables: list[UpstreamTableRef] = []
    upstream_databases: list[UpstreamDatabaseRef] = []
    field_preview: list[FieldPreview] = []  # first 30 fields


class WorkbookLineage(TableauModel):
    """Targeted lineage result for a single workbook.

    Returned by ``lineage.workbook_lineage()``.  Answers "what views does this
    workbook contain, and what published datasources power it?" with one
    GraphQL request.

    ``embedded_datasources`` maps embedded datasource names to the published
    datasources they layer on top of (via ``EmbeddedDatasourceRef``).

    ``upstream_datasources`` is a flat list of all published datasources
    that feed this workbook (from ``upstreamDatasources``).

    ``upstream_databases`` lists the raw database connections used.
    """

    luid: str
    name: str
    description: str | None = None
    project_name: str | None = None
    owner_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    sheets: list[SheetRef] = []
    dashboards: list[DashboardRef] = []
    embedded_datasources: list[EmbeddedDatasourceRef] = []
    upstream_datasources: list[DatasourceRef] = []
    upstream_databases: list[UpstreamDatabaseRef] = []


# ── View data query model ───────────────────────────────────────────


class ViewQueryResult(TableauModel):
    """Result from querying a Tableau view via the REST API.

    ``column_names`` is the CSV header row.
    ``rows`` is each data row as a dict keyed by column name.
    ``row_count`` is the number of data rows (excludes the header).
    ``raw_csv`` is the original response text for agents that prefer
    to process it themselves.
    """

    column_names: list[str] = []
    rows: list[dict[str, str]] = []
    row_count: int = 0
    raw_csv: str = ""


# ── Orchestrator result ─────────────────────────────────────────────
class ExplorationResult(TableauModel):
    """Result of the ``run()`` convenience orchestrator.

    Carries the selected datasource, its schema, the query result, and
    any temp files that were written.  Deliberately excludes ``AuthToken``
    for security — tokens are never persisted to disk.
    """

    selected_datasource: DatasourceSummary
    datasource_schema: DatasourceSchema
    query_result: QueryResult | None = None
    temp_files: list[str] = []
