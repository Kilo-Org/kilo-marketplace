# Excel Engineering Functions

Engineering functions cover number-base conversions, bitwise operations,
complex number arithmetic, and unit conversions.

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

---

## Number Base Conversions

`BIN2DEC(number)` — Converts a binary number (text) to decimal.
`BIN2HEX(number, [places])` — Converts a binary number to hexadecimal.
`BIN2OCT(number, [places])` — Converts a binary number to octal.
`DEC2BIN(number, [places])` — Converts a decimal number to binary.
`DEC2HEX(number, [places])` — Converts a decimal number to hexadecimal.
`DEC2OCT(number, [places])` — Converts a decimal number to octal.
`HEX2BIN(number, [places])` — Converts a hexadecimal number to binary.
`HEX2DEC(number)` — Converts a hexadecimal number to decimal.
`HEX2OCT(number, [places])` — Converts a hexadecimal number to octal.
`OCT2BIN(number, [places])` — Converts an octal number to binary.
`OCT2DEC(number)` — Converts an octal number to decimal.
`OCT2HEX(number, [places])` — Converts an octal number to hexadecimal.
`BASE(number, radix, [min_length])` — Converts a number to a text representation in the given base (2–36). *(Math category in some versions.)*
`DECIMAL(text, radix)` — Converts a text representation of a number in the given base to decimal.

## Bitwise Operations

`BITAND(number1, number2)` — Returns a bitwise AND of two numbers.
`BITOR(number1, number2)` — Returns a bitwise OR of two numbers.
`BITXOR(number1, number2)` — Returns a bitwise XOR (exclusive OR) of two numbers.
`BITLSHIFT(number, shift_amount)` — Returns a number shifted left by shift_amount bits (equivalent to × 2^shift).
`BITRSHIFT(number, shift_amount)` — Returns a number shifted right by shift_amount bits (equivalent to ÷ 2^shift).

## Threshold / Comparison

`DELTA(number1, [number2])` — Returns 1 if number1 = number2 (defaults to 0), otherwise 0. Useful for counting matching pairs with SUMPRODUCT.

`GESTEP(number, [step])` — Returns 1 if number ≥ step (defaults to 0), otherwise 0. Useful for counting values above a threshold.

## Error Functions

`ERF(lower_limit, [upper_limit])` — Returns the error function integrated between lower_limit and upper_limit.
`ERF.PRECISE(x)` — Returns the error function integrated from 0 to x.
`ERFC(x)` — Returns the complementary error function (1 − ERF(x)).
`ERFC.PRECISE(x)` — Returns the complementary error function integrated between x and infinity.

## Bessel Functions

`BESSELI(x, n)` — Modified Bessel function Iₙ(x) — useful in heat transfer and signal processing.
`BESSELJ(x, n)` — Bessel function Jₙ(x) — common in wave propagation problems.
`BESSELK(x, n)` — Modified Bessel function Kₙ(x).
`BESSELY(x, n)` — Bessel function Yₙ(x) (Neumann function).

## Complex Numbers

Complex numbers are stored as text strings in the form `"a+bi"` or `"a+bj"`.

`COMPLEX(real_num, i_num, [suffix])` — Creates a complex number from real and imaginary parts. suffix is "i" (default) or "j".
`IMREAL(inumber)` — Returns the real part of a complex number.
`IMAGINARY(inumber)` — Returns the imaginary coefficient of a complex number.
`IMARGUMENT(inumber)` — Returns the argument θ (angle in radians) of a complex number.
`IMABS(inumber)` — Returns the modulus (absolute value) of a complex number.
`IMCONJUGATE(inumber)` — Returns the complex conjugate (negates the imaginary part).

### Arithmetic
`IMADD(inumber1, inumber2)` — Returns the sum of two complex numbers.
`IMSUB(inumber1, inumber2)` — Returns the difference of two complex numbers.
`IMPRODUCT(inumber1, [inumber2], ...)` — Returns the product of complex numbers.
`IMDIV(inumber1, inumber2)` — Returns the quotient of two complex numbers.
`IMSUM(inumber1, [inumber2], ...)` — Returns the sum of multiple complex numbers.
`IMPOWER(inumber, number)` — Returns a complex number raised to an integer power.
`IMSQRT(inumber)` — Returns the positive square root of a complex number.
`IMEXP(inumber)` — Returns the exponential of a complex number (eˢ).
`IMLN(inumber)` — Returns the natural logarithm of a complex number.
`IMLOG10(inumber)` — Returns the base-10 logarithm of a complex number.
`IMLOG2(inumber)` — Returns the base-2 logarithm of a complex number.

### Trigonometric (complex)
`IMSIN(inumber)` — Sine of a complex number.
`IMCOS(inumber)` — Cosine of a complex number.
`IMTAN(inumber)` — Tangent of a complex number.
`IMCOT(inumber)` — Cotangent of a complex number.
`IMSEC(inumber)` — Secant of a complex number.
`IMCSC(inumber)` — Cosecant of a complex number.
`IMSINH(inumber)` — Hyperbolic sine of a complex number.
`IMCOSH(inumber)` — Hyperbolic cosine of a complex number.
`IMSECH(inumber)` — Hyperbolic secant of a complex number.
`IMCSCH(inumber)` — Hyperbolic cosecant of a complex number.

## Unit Conversion

`CONVERT(number, from_unit, to_unit)` — Converts a number from one unit system to another.

Common unit strings:

| Category | Units |
|----------|-------|
| Weight | "g", "kg", "lbm", "ozm", "stone", "ton", "uk_ton" |
| Distance | "m", "km", "mi", "Nmi", "in", "ft", "yd", "ang", "ly" |
| Time | "yr", "day", "hr", "mn", "sec" |
| Pressure | "Pa", "atm", "mmHg", "psi", "Torr" |
| Force | "N", "dyn", "lbf", "pond" |
| Energy | "J", "e", "c", "cal", "eV", "HPh", "Wh", "BTU" |
| Power | "W", "HP", "PS" |
| Temperature | "C", "F", "K", "Rank", "Reau" |
| Volume | "l", "L", "lt", "tsp", "tbs", "oz", "cup", "pt", "qt", "gal", "m3" |
| Area | "m2", "mi2", "km2", "in2", "ft2", "yd2", "acre", "ha" |
| Speed | "m/s", "m/h", "mph", "kn", "admkn" |

```excel
=CONVERT(100, "F", "C")     → 37.78  (100°F to Celsius)
=CONVERT(1, "mi", "km")     → 1.609
=CONVERT(1, "lbm", "kg")    → 0.454
```
