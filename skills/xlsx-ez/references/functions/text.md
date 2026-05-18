# Excel Text Functions

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

---

## Concatenation

`CONCAT(text1, [text2], ...)` — Joins text from a list of values or ranges. Replaces the older CONCATENATE.

`CONCATENATE(text1, [text2], ...)` — Legacy join function. Use CONCAT or `&` instead.

`TEXTJOIN(delimiter, ignore_empty, text1, [text2], ...)` — Joins text with a delimiter between items. ignore_empty=TRUE skips blank cells.
```excel
=TEXTJOIN(", ", TRUE, A1:A10)        → "Alice, Bob, Carol"
=TEXTJOIN(CHAR(10), TRUE, A1:A5)     → newline-separated (wrap_text must be on)
```

`&` operator — Most concise concatenation: `=A1&" "&B1`

## Splitting and Extracting (Excel 365+)

`TEXTSPLIT(text, col_delimiter, [row_delimiter], [ignore_empty], [match_mode], [pad_with])` — Splits text into a 2D array using column and/or row delimiters. Spills automatically.
```excel
=TEXTSPLIT("Alice,Bob,Carol", ",")         → {"Alice","Bob","Carol"}
=TEXTSPLIT("A:1|B:2", ":", "|")            → 2×2 array
```

`TEXTBEFORE(text, delimiter, [instance_num], [match_mode], [match_end_mode])` — Returns everything before the nth occurrence of a delimiter. Negative instance_num counts from the end.
```excel
=TEXTBEFORE("first.middle.last", ".", 2)   → "first.middle"
```

`TEXTAFTER(text, delimiter, [instance_num], [match_mode], [match_end_mode])` — Returns everything after the nth occurrence.
```excel
=TEXTAFTER("path/to/file.txt", "/", -1)    → "file.txt"
```

## Substrings

`LEFT(text, [num_chars])` — Returns the first num_chars characters (default 1).

`RIGHT(text, [num_chars])` — Returns the last num_chars characters.

`MID(text, start_num, num_chars)` — Returns num_chars characters starting at start_num (1-based).

```excel
=LEFT("Hello World", 5)      → "Hello"
=RIGHT("Hello World", 5)     → "World"
=MID("Hello World", 7, 5)    → "World"
```

**Byte-count variants** (for double-byte character sets — East Asian languages):
`LEFTB`, `RIGHTB`, `MIDB` — Same as above but count bytes instead of characters.

## Length

`LEN(text)` — Number of characters in a string.

`LENB(text)` — Number of bytes (differs from LEN for double-byte characters).

## Case Conversion

`UPPER(text)` — Converts to UPPERCASE.

`LOWER(text)` — Converts to lowercase.

`PROPER(text)` — Capitalizes the First Letter Of Each Word.

## Search and Find

`FIND(find_text, within_text, [start_num])` — Case-sensitive search; returns position (1-based) or #VALUE! if not found. Does not support wildcards.

`SEARCH(find_text, within_text, [start_num])` — Case-insensitive search; supports `*` and `?` wildcards.

`FINDB` / `SEARCHB` — Byte-position variants.

```excel
=FIND("@", email)                    → position of @ sign
=SEARCH("*manager*", A1)             → 1 if "manager" appears anywhere
=ISNUMBER(SEARCH("abc", A1))         → TRUE if A1 contains "abc"
```

## Replacing and Substituting

`REPLACE(old_text, start_num, num_chars, new_text)` — Replaces characters by position.
```excel
=REPLACE("ABCDEF", 3, 2, "XX")       → "ABXXEF"
```

`SUBSTITUTE(text, old_text, new_text, [instance_num])` — Replaces all (or the nth) occurrence of old_text with new_text.
```excel
=SUBSTITUTE(A1, " ", "_")            → replace all spaces with underscores
=SUBSTITUTE(A1, ".", "", 1)          → remove first period
=SUBSTITUTE(A1, CHAR(10), " ")       → remove newlines
```

`REPLACEB` — Byte-position variant of REPLACE.

## Trimming and Cleaning

`TRIM(text)` — Removes leading and trailing spaces, and reduces internal multiple spaces to single spaces. Handles regular ASCII spaces (code 32) only.

`CLEAN(text)` — Removes non-printable characters (ASCII 1–31). Useful for imported data.

```excel
=TRIM(CLEAN(A1))                     → strip both non-printable chars and extra spaces
```

## Padding and Formatting

`REPT(text, number_times)` — Repeats text n times. Used for simple bar charts in cells or zero-padding.
```excel
=REPT("■", A1/10)                   → visual bar chart
=REPT("0", 5-LEN(A1)) & A1          → zero-pad to 5 digits
```

`TEXT(value, format_text)` — Formats a number or date as text using Excel format codes.
```excel
=TEXT(A1, "$#,##0.00")              → "$1,234.56"
=TEXT(TODAY(), "DD MMM YYYY")        → "15 Mar 2024"
=TEXT(0.1234, "0.0%")               → "12.3%"
=TEXT(A1, "000000")                 → zero-padded 6-digit number
```

`FIXED(number, [decimals], [no_commas])` — Formats a number as text with a fixed number of decimal places and optional comma separators.

`DOLLAR(number, [decimals])` — Formats as currency text (locale-specific symbol).

## Character Codes

`CHAR(number)` — Returns the character for an ASCII/ANSI code.
```excel
=CHAR(10)   → newline (line feed)
=CHAR(13)   → carriage return
=CHAR(9)    → tab
=CHAR(160)  → non-breaking space
```

`CODE(text)` — Returns the numeric code of the first character.

`UNICHAR(number)` — Returns the Unicode character for a code point.

`UNICODE(text)` — Returns the Unicode code point of the first character.

## Type Conversion

`VALUE(text)` — Converts a text representation of a number to a number. Useful for numbers imported as text.

`NUMBERVALUE(text, [decimal_separator], [group_separator])` — Locale-aware text-to-number conversion. Handles different decimal/thousands separators.

`T(value)` — Returns the text if value is text, empty string otherwise.

`VALUETOTEXT(value, [format])` — Converts any value to text. format 0=concise, 1=strict (adds quotes around strings, etc.).

`ARRAYTOTEXT(array, [format])` — Converts a range or array to a single text string. format 0=concise, 1=strict.

## Formatting Helpers

`BAHTTEXT(number)` — Converts a number to Thai text.

`ASC(text)` — Converts full-width (double-byte) characters to half-width. (East Asian locales.)

`DBCS(text)` / `JIS(text)` — Converts half-width to full-width. JIS is the Japanese alias.

`PHONETIC(reference)` — Extracts phonetic (furigana) text annotations from CJK characters.

## Common Patterns

```excel
# Extract domain from email
=TEXTAFTER(A1, "@")

# Extract filename from full path
=TEXTAFTER(A1, "\", -1)
# Older Excel alternative:
=MID(A1, FIND("~", SUBSTITUTE(A1,"\","~",LEN(A1)-LEN(SUBSTITUTE(A1,"\",""))))+1, 100)

# Count occurrences of a character
=(LEN(A1)-LEN(SUBSTITUTE(A1,"e","")))/LEN("e")

# Pad to fixed width (left-justify)
=LEFT(A1&REPT(" ",20), 20)

# Extract numbers from mixed text
=VALUE(TEXTJOIN("",TRUE,IFERROR(MID(A1,ROW(INDIRECT("1:"&LEN(A1))),1)*1,"")))
# ↑ array formula; spills in 365

# Remove all spaces
=SUBSTITUTE(A1," ","")

# Check if cell contains a substring (case-insensitive)
=ISNUMBER(SEARCH("keyword", A1))

# Title case a full name
=PROPER(LOWER(A1))

# Split "Last, First" into two cells
=TEXTBEFORE(A1, ", ")             → Last name
=TEXTAFTER(A1, ", ")              → First name

# Join non-blank cells with commas
=TEXTJOIN(", ", TRUE, A1:A10)
```
