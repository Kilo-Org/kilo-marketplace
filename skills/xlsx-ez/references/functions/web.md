# Excel Web Functions

Web functions retrieve and process data from external web services.
They are available in Excel for Windows and Mac with an active internet connection.
They are **not available** in LibreOffice Calc.

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

---

`ENCODEURL(text)` — Returns a percent-encoded (URL-safe) string. Encodes special characters such as spaces, `&`, `#`, etc.
```excel
=ENCODEURL("hello world")        → "hello%20world"
=ENCODEURL(A1)                   → encode a cell value for use in a URL
```

`WEBSERVICE(url)` — Returns data from a web service as a text string. The URL must return plain text (not HTML pages). Volatile — recalculates on every sheet change.
```excel
=WEBSERVICE("https://api.example.com/price?symbol="&ENCODEURL(A1))
```

**Notes:** WEBSERVICE is limited to GET requests with no authentication headers. For anything more complex use Power Query or an external script.

`FILTERXML(xml, xpath)` — Extracts data from XML text using an XPath expression. Combine with WEBSERVICE to parse API responses.
```excel
# Get a value from an XML API response
=FILTERXML(WEBSERVICE("https://api.example.com/data.xml"), "//price")

# Extract multiple values (spills in 365)
=FILTERXML(xml_text, "//item/name")

# Get the second occurrence
=FILTERXML(xml_text, "(//price)[2]")

# Get an attribute value
=FILTERXML(xml_text, "//product/@id")
```

## Typical Pattern

```excel
A1: symbol          → AAPL
B1: =ENCODEURL(A1)  → AAPL (no special chars in this case)
C1: =WEBSERVICE("https://query1.finance.yahoo.com/v8/finance/chart/"&B1&"?interval=1d")
D1: =FILTERXML(C1, "//regularMarketPrice")
```

## Limitations

- WEBSERVICE only fetches URLs returning plain text or XML; JSON responses require Power Query.
- No POST requests, no custom headers, no authentication.
- Both WEBSERVICE and FILTERXML are volatile and recalculate frequently.
- Not available in LibreOffice Calc — use Python/pandas for cross-platform web data.
