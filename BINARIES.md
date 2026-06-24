# PR 149 binary and large-blob review

## Verdict

**Pass: no large binary files require Git LFS.** The PR introduces five real binary blobs, all copies of the same 15,366-byte PNG (one unique object), and no archives, audio/video, fonts, executables, compiled libraries, model/data binaries, or Git LFS pointer files. The largest changed blob is a 494,589-byte XML Tableau workbook, below the review threshold and diffable as text.

The large/generated text listed below is worth acknowledging because it adds review and repository weight, but none is an LFS violation. The Tableau workbook/schema and generated marketplace manifests are the most questionable items; keep them only if they are intentional source/reference artifacts.

## Scope and thresholds

- Compared `HEAD` (`9c60c4951a0cec941a63d0e6bcaaad0c808aa33e`) with merge-base range `c7d249097589c6c94808688969097a5048ff5890...HEAD`.
- Inspected all 1,352 changed paths: 1,347 added and 5 modified. This covered every resulting changed blob plus the five replaced base blobs (1,357 blob instances; 1,340 distinct object IDs).
- Resulting blobs total 12,026,206 bytes by path (11,946,009 bytes across unique objects). Size distribution: 1,000 below 10 KiB, 344 from 10 to below 100 KiB, 6 from 100 to below 250 KiB, 2 from 250 to below 500 KiB, and none at or above 500 KiB.
- Review assumptions: flag all binary/archive/media/generated artifacts regardless of size; call text at least 100 KiB unusually large; recommend LFS consideration for non-diffable blobs at least 1 MiB; treat 100 MiB as GitHub's hard per-file limit. A small, required image does not need LFS.

## Methodology

- Enumerated paths and old/new object IDs with `git diff --raw -z --no-abbrev BASE...HEAD`, and verified statuses with `git diff --name-status` and line classification with `git diff --numstat`.
- Read each object directly using `git cat-file blob` / `git cat-file -s`; classified every object from its bytes using `file -b` and `file -b --mime-type` rather than relying only on extensions.
- Scanned changed names for archive, media, executable, compiled, database, model, dataset, dependency/build-output, and generated-path conventions.
- Detected LFS pointers by the canonical `version https://git-lfs.github.com/spec/v1` header; also ran `git lfs ls-files --all`, `git lfs track`, and `git check-attr filter diff merge text` on representative binary and large files.
- Inspected the headers/signatures of the largest Tableau workbook/schema and the PNG. Size/type results refer to Git blobs, not checkout filters or filesystem allocation.

## Largest resulting blobs

| Bytes | Type | Path | Assessment |
|---:|---|---|---|
| 494,589 | XML text | `skills/tableau-dashboard-creator/examples/top-level-workbook-example.twb` | Largest blob; generated-looking Tableau workbook/reference example, but diffable and below 500 KiB. |
| 297,180 | XSD/XML text (`file` labels it exported SGML) | `skills/tableau-dashboard-creator/references/xsd/twb_2026.1.0.xsd` | Published/generated Tableau schema; diffable text. |
| 209,595 | Markdown/UTF-8 text | `skills/azure-databricks/integrations.md` | Unusually large prose/reference text. |
| 193,316 | YAML/ASCII text | `mcps/marketplace.yaml` | Generated manifest (`linguist-generated=true`); grows from 92,543 bytes in the base. |
| 134,268 | YAML/UTF-8 text | `skills/marketplace.yaml` | Generated manifest (`linguist-generated=true`); grows from 27,998 bytes in the base. |
| 118,135 | Markdown/UTF-8 text | `skills/azure-databricks/configuration.md` | Unusually large prose/reference text. |
| 113,971 | XML text | `skills/tableau-dashboard-creator/references/snippets/features/parameter-control.twb` | Generated-looking Tableau snippet; diffable text. |
| 107,066 | XML text | `skills/tableau-dashboard-creator/references/snippets/dashboard/multi-sheet-layout.twb` | Generated-looking Tableau snippet; diffable text. |

No resulting blob reaches 500 KiB, 1 MiB, or GitHub's 100 MiB limit. Other notable near-threshold text includes `skills/nifi-flow-layout/scripts/nifi_layout.py` (96,945 bytes), `skills/azure-machine-learning/references/documentation-catalog.md` (82,640 bytes), and `skills/query-tableau-data/src/schemas/vds.20261.0.openapi.json` (75,434 bytes; generated OpenAPI schema).

## Binary, media, archive, and generated findings

- Binary/media: exactly five PNG paths, each 15,366 bytes, 450x450 RGBA, and all backed by the same blob `263fe98b84e8ff3516edc93e7c99230fb8fb3113`: `skills/databricks-core/assets/databricks.png`, `skills/databricks-jobs/assets/databricks.png`, `skills/databricks-model-serving/assets/databricks.png`, `skills/databricks-pipelines/assets/databricks.png`, and `skills/databricks-spark-structured-streaming/assets/databricks.png`. These are small branding assets; LFS would add overhead without meaningful repository savings. Their duplication by path is questionable but Git stores the content once.
- Vector media: five `.svg` files are plain SVG/XML text, not opaque binaries, and are small.
- Archives/opaque artifacts: none detected. There are no changed ZIP/tar/compressed packages, PDFs, audio/video, fonts, executables, shared libraries, database files, serialized models, Parquet/Avro/ORC files, or similar non-diffable artifacts.
- Generated/reference text: Tableau `.twb` examples/snippets and `.xsd` schemas, `skills/query-tableau-data/src/schemas/vds.20261.0.openapi.json`, `skills/query-tableau-data/uv.lock` (35,608 bytes), and generated marketplace YAML are legitimate-looking source/reference outputs but should be confirmed as intentionally vendored. They are not LFS candidates at current sizes.
- Sample data: three CSV files total 5,871 bytes; no large dataset concern.

## Attributes and LFS

- `.gitattributes` exists and is unchanged by this PR. It only marks `agents/marketplace.yaml`, `mcps/marketplace.yaml`, `modes/marketplace.yaml`, and `skills/marketplace.yaml` as `linguist-generated=true`.
- No `filter=lfs`, `diff=lfs`, or `merge=lfs` patterns are configured. Effective LFS-related attributes are unspecified for the PNGs and the largest text blobs.
- `git lfs ls-files --all` and `git lfs track` return no entries; byte inspection finds zero LFS pointer blobs.
- Therefore the PNGs are committed directly to Git, but their 15 KiB size is acceptable. No missing LFS tracking is identified.

## Questionable items and disposition

1. `skills/tableau-dashboard-creator/examples/top-level-workbook-example.twb` is a nearly 500 KiB generated-looking example. Keep in Git if users need the complete example; otherwise generate or trim it. It does not justify LFS because it remains text and diffable.
2. `skills/tableau-dashboard-creator/references/xsd/twb_2026.1.0.xsd` is a 297 KiB published/generated schema. Vendoring is reasonable for offline validation, but provenance/update policy should be clear; LFS is unnecessary.
3. The six text blobs at or above 100 KiB outside those two files are unusually large. The generated marketplace manifests are expected outputs, while the large Azure Databricks Markdown files may be easier to review and consume if split. None should use LFS.
4. Five paths duplicate one Databricks PNG. Git object deduplication limits storage cost, so this is organizational duplication rather than a binary-size blocker.

**Final determination:** PR 149 contains no large binary without Git LFS and no blob that should be moved to LFS under the stated thresholds. Merge is not blocked on binary/LFS grounds; only confirm that the large generated/reference text artifacts are intentionally vendored.
