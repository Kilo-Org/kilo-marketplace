---
name: "knowledge-catalog-discovery"
description: "Use these skills when you need to discover and explore data assets in the Knowledge Catalog. It allows you to search for entries, lookup specific metadata, and explore aspect types to understand your data platform's assets."
metadata:
  category: data
  source:
    repository: "https://github.com/gemini-cli-extensions/knowledge-catalog"
    path: "skills/knowledge-catalog-discovery"
    license_path: "LICENSE"
---

## Usage

All scripts can be executed using Node.js. Replace `<param_name>` and `<param_value>` with actual values.

**Bash:**
`node <skill_dir>/scripts/<script_name>.js '{"<param_name>": "<param_value>"}'`

**PowerShell:**
`node <skill_dir>/scripts/<script_name>.js '{\"<param_name>\": \"<param_value>\"}'`

Note: The scripts automatically load the environment variables from various .env files. Do not ask the user to set vars unless skill executions fails due to env var absence.


## Scripts


### lookup_context

Retrieves rich metadata regarding one or more data assets along with their relationships.

#### Parameters

| Name | Type | Description | Required | Default |
| :--- | :--- | :--- | :--- | :--- |
| resources | array | Required. A list of up to 10 resource names. Resources may belong to different projects, but all must belong to the same location. | Yes |  |


---

### lookup_entry

Retrieves a specific metadata regarding a data asset (e.g. table/dataset/view) from Catalog

#### Parameters

| Name | Type | Description | Required | Default |
| :--- | :--- | :--- | :--- | :--- |
| entry | string | Required. The resource name of the Entry in the following form: projects/{project}/locations/{location}/entryGroups/{entryGroup}/entries/{entry}. | Yes |  |
| view | integer |
				## Argument: view

				**Type:** Integer

				**Description:** Optional. Specifies the parts of the entry and its aspects to return.

				**Possible Values:**

				*   1 (BASIC): Returns entry without aspects.
				*   2 (FULL): Return all required aspects and the keys of non-required aspects. (Default)
				*   3 (CUSTOM): Return the entry and aspects requested in aspect_types field (at most 100 aspects). Always use this view when aspect_types is not empty.
				*   4 (ALL): Return the entry and both required and optional aspects (at most 100 aspects)
				 | No | `2` |
| aspectTypes | array | Optional. Limits the aspects returned to the provided aspect types. It only works when used together with CUSTOM view. | No | `[]` |


---

### search_aspect_types

Search aspect types relevant to the query.

#### Parameters

| Name | Type | Description | Required | Default |
| :--- | :--- | :--- | :--- | :--- |
| query | string | The query against which aspect type should be matched. | Yes |  |
| pageSize | integer | Number of returned aspect types in the search page. | No | `5` |
| orderBy | string | Specifies the ordering of results. Supported values are: relevance, last_modified_timestamp, last_modified_timestamp asc | No | `relevance` |


---

### search_entries

Searches for data assets (eg. table/dataset/view) in Catalog based on the provided search query.

#### Parameters

| Name | Type | Description | Required | Default |
| :--- | :--- | :--- | :--- | :--- |
| query | string | A query string for searching entries, following Dataplex search syntax. Supports logical operators (AND, OR, NOT) and grouping. For example, to find a table that might have been renamed, you could use 'type:table (name:books OR fiction)'. This can be more efficient than multiple separate calls.Warning: Performing broad searches without specific filters (e.g., type:table) can be slow and consume significant resources. When performing exploratory searches, always use the pageSize parameter to limit the number of results returned. | Yes |  |
| scope | string | A scope limits the search space to a particular project or organization. It must be in the format: organizations/<org_id> or projects/<project_id> or projects/<project_number>. | No | `` |
| pageSize | integer | Number of results in the search page. | No | `5` |
| orderBy | string | Specifies the ordering of results. Supported values are: relevance, last_modified_timestamp, last_modified_timestamp asc | No | `relevance` |


---
