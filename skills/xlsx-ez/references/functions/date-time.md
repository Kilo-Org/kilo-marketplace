# Excel Date and Time Functions

Excel stores dates as serial numbers (1 = January 1, 1900) and times as decimal
fractions of a day (0.5 = noon). Date arithmetic is therefore just subtraction.

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

---

## Construction

`DATE(year, month, day)` — Returns the serial number of a specific date. Handles overflow (e.g. month=13 rolls to next year).

`TIME(hour, minute, second)` — Returns the serial number of a specific time as a fraction of a day.

`DATEVALUE(date_text)` — Converts a date stored as text (e.g. "2024-03-15") to a serial number.

`TIMEVALUE(time_text)` — Converts a time stored as text (e.g. "14:30:00") to a serial fraction.

## Current Date / Time

`TODAY()` — Returns today's date serial number. Recalculates each time the sheet opens.

`NOW()` — Returns the current date and time as a serial number. Recalculates on each calculation.

## Extracting Components

`YEAR(serial_number)` — Returns the year (1900–9999) from a date serial number.

`MONTH(serial_number)` — Returns the month (1–12) from a date serial number.

`DAY(serial_number)` — Returns the day of the month (1–31) from a date serial number.

`HOUR(serial_number)` — Returns the hour (0–23) from a time serial number.

`MINUTE(serial_number)` — Returns the minute (0–59) from a time serial number.

`SECOND(serial_number)` — Returns the second (0–59) from a time serial number.

`WEEKDAY(serial_number, [return_type])` — Returns the day of the week as a number. return_type 1 = Sun=1…Sat=7 (default), 2 = Mon=1…Sun=7, 3 = Mon=0…Sun=6.

`WEEKNUM(serial_number, [return_type])` — Returns the week number within the year. return_type 21 = ISO week numbering (Monday start).

`ISOWEEKNUM(date)` — Returns the ISO 8601 week number (1–53) for a date.

## Date Arithmetic

`DAYS(end_date, start_date)` — Returns the number of days between two dates (end − start).

`DAYS360(start_date, end_date, [method])` — Number of days between two dates based on a 360-day year (12 months × 30 days). method=FALSE (US) or TRUE (European).

`EDATE(start_date, months)` — Returns the date that is a given number of months before or after start_date. Useful for maturity/expiry dates.

`EOMONTH(start_date, months)` — Returns the last day of the month that is a given number of months from start_date. months=0 = last day of the current month.

`YEARFRAC(start_date, end_date, [basis])` — Returns the fraction of the year represented by the days between two dates. basis: 0=US 30/360, 1=actual/actual, 2=actual/360, 3=actual/365, 4=European 30/360.

## Working Days

`NETWORKDAYS(start_date, end_date, [holidays])` — Returns the number of whole working days (Mon–Fri) between two dates, excluding optional holidays.

`NETWORKDAYS.INTL(start_date, end_date, [weekend], [holidays])` — Like NETWORKDAYS but with a configurable weekend. weekend can be a number (1=Sat+Sun, 11=Sun only, etc.) or a 7-character string of 0s and 1s (e.g. "0000011" = Sat+Sun).

`WORKDAY(start_date, days, [holidays])` — Returns the date that is a given number of working days (Mon–Fri) from start_date.

`WORKDAY.INTL(start_date, days, [weekend], [holidays])` — Like WORKDAY with configurable weekend.

## Common Patterns

```excel
# Age in years
=DATEDIF(birth_date, TODAY(), "Y")

# Days until deadline
=deadline - TODAY()

# First day of current month
=DATE(YEAR(TODAY()), MONTH(TODAY()), 1)

# Last day of current month
=EOMONTH(TODAY(), 0)

# Same date next year
=DATE(YEAR(A1)+1, MONTH(A1), DAY(A1))

# Quarter number
=INT((MONTH(A1)-1)/3)+1

# Financial year (Apr–Mar, UK)
=IF(MONTH(A1)>=4, YEAR(A1), YEAR(A1)-1)

# Convert text "20240315" to date
=DATE(LEFT(A1,4), MID(A1,5,2), RIGHT(A1,2))
```
