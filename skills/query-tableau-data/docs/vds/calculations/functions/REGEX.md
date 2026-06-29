# Regular Expression Functions

Regular expression functions are available for VDS queries when the underlying data source supports them. For Tableau extracts, regular expression syntax conforms to the standards of the ICU (International Components for Unicode) library.

> **VDS Note**: These functions are available for: Text File, Hadoop Hive, Google BigQuery, PostgreSQL, Tableau Data Extract, Microsoft Excel, Salesforce, Vertica, Pivotal Greenplum, Teradata (version 14.1 and above), Snowflake, and Oracle data sources. They work in VDS `calculation` strings as long as the underlying published data source uses a supported connector.

> **Not available in VDS**: Hadoop Hive-specific functions (`GET_JSON_OBJECT`, `PARSE_URL`, `PARSE_URL_QUERY`, `XPATH_*`) and Google BigQuery-specific functions (`DOMAIN`, `GROUP_CONCAT`, `HOST`, `LOG2`, `LTRIM_THIS`, `RTRIM_THIS`, `TIMESTAMP_TO_USEC`, `USEC_TO_TIMESTAMP`, `TLD`) are data-source-specific and are not supported in VDS. See research archives `HADOOP_HIVE.md` and `BIGQUERY.md`.

---

### REGEXP\_REPLACE

|  |  |
| --- | --- |
| Syntax | `REGEXP_REPLACE(string, pattern, replacement)` |
| Output | String |
| Definition | Returns a copy of the given string where the regular expression pattern is replaced by the replacement string. |
| Example | ``` REGEXP_REPLACE('abc 123', '\s', '-') = 'abc-123' ``` |
| Notes | For Tableau data extracts, the pattern and the replacement must be constants. |

### REGEXP\_MATCH

|  |  |
| --- | --- |
| Syntax | `REGEXP_MATCH(string, pattern)` |
| Output | Boolean |
| Definition | Returns true if a substring of the specified string matches the regular expression pattern. |
| Example | ``` REGEXP_MATCH('-([1234].[The.Market])-','\[\s*(\w*\.)(\w*\s*\])')=true ``` |
| Notes | For Tableau data extracts, the pattern must be a constant. |

### REGEXP\_EXTRACT

|  |  |
| --- | --- |
| Syntax | `REGEXP_EXTRACT(string, pattern)` |
| Output | String |
| Definition | Returns the portion of the string that matches the regular expression pattern. |
| Example | ``` REGEXP_EXTRACT('abc 123', '[a-z]+\s+(\d+)') = '123' ``` |
| Notes | For Tableau data extracts, the pattern must be a constant. |

### REGEXP\_EXTRACT\_NTH

|  |  |
| --- | --- |
| Syntax | `REGEXP_EXTRACT_NTH(string, pattern, index)` |
| Output | String |
| Definition | Returns the portion of the string that matches the regular expression pattern. The substring is matched to the nth capturing group, where n is the given index. If index is 0, the entire string is returned. |
| Example | ``` REGEXP_EXTRACT_NTH('abc 123', '([a-z]+)\s+(\d+)', 2) = '123' ``` |
| Notes | For Tableau data extracts, the pattern must be a constant. |
