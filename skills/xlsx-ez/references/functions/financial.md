# Excel Financial Functions

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

**Convention:** positive values = cash inflows; negative values = cash outflows.
**type argument:** 0 = payments at end of period (ordinary annuity); 1 = payments at beginning of period (annuity due).
**basis argument (day-count):** 0=US 30/360, 1=actual/actual, 2=actual/360, 3=actual/365, 4=European 30/360.

---

## Core Time Value of Money

`PV(rate, nper, pmt, [fv], [type])` — Present value of a series of equal payments and/or a lump-sum future value.

`FV(rate, nper, pmt, [pv], [type])` — Future value of a series of equal payments and/or a present lump sum.

`PMT(rate, nper, pv, [fv], [type])` — Periodic payment for a loan or annuity (principal + interest).

`NPER(rate, pmt, pv, [fv], [type])` — Number of periods required to pay off a loan or reach a future value.

`RATE(nper, pmt, pv, [fv], [type], [guess])` — Interest rate per period; iterative solver — provide a guess if it fails to converge.

`FVSCHEDULE(principal, schedule)` — Future value of a principal after applying a schedule of variable interest rates (array of rates).

## Loan Amortization

`IPMT(rate, per, nper, pv, [fv], [type])` — Interest portion of a payment for a specific period.

`PPMT(rate, per, nper, pv, [fv], [type])` — Principal portion of a payment for a specific period.

`ISPMT(rate, per, nper, pv)` — Interest paid during a specific period for a straight-line loan (equal principal repayment).

`CUMIPMT(rate, nper, pv, start_period, end_period, type)` — Cumulative interest paid between two periods.

`CUMPRINC(rate, nper, pv, start_period, end_period, type)` — Cumulative principal paid between two periods.

## Investment Returns

`NPV(rate, value1, [value2], ...)` — Net present value of a series of cash flows assumed to occur at equal time intervals (end of each period). Add initial outlay separately: `=NPV(r, flows) - initial_cost`.

`XNPV(rate, values, dates)` — Net present value for irregular (non-periodic) cash flows specified by date. More accurate than NPV for real-world cash flows.

`IRR(values, [guess])` — Internal rate of return for a series of periodic cash flows. The first value is typically negative (initial investment).

`XIRR(values, dates, [guess])` — IRR for irregular cash flows specified by date.

`MIRR(values, finance_rate, reinvest_rate)` — Modified IRR using different rates for financing and reinvestment; addresses IRR's reinvestment-rate assumption.

`RRI(nper, pv, fv)` — Equivalent constant interest rate for growth from pv to fv over nper periods. Useful for CAGR: `=RRI(years, start_value, end_value)`.

`PDURATION(rate, pv, fv)` — Number of periods required for an investment at a constant rate to grow from pv to fv.

## Depreciation

`SLN(cost, salvage, life)` — Straight-line depreciation per period.

`SYD(cost, salvage, life, per)` — Sum-of-years-digits depreciation for a specific period.

`DB(cost, salvage, life, period, [month])` — Declining balance depreciation (fixed-percentage) for a specific period.

`DDB(cost, salvage, life, period, [factor])` — Double-declining balance depreciation. factor defaults to 2.

`VDB(cost, salvage, life, start_period, end_period, [factor], [no_switch])` — Variable declining balance depreciation over any partial period; optionally switches to straight-line when SLN exceeds DDB.

`AMORDEGRC(cost, date_purchased, first_period, salvage, period, rate, [basis])` — French accounting declining-balance depreciation.

`AMORLINC(cost, date_purchased, first_period, salvage, period, rate, [basis])` — French accounting linear depreciation.

## Bonds and Fixed Income

`PRICE(settlement, maturity, rate, yld, redemption, frequency, [basis])` — Price per $100 face value of a coupon-bearing security.

`YIELD(settlement, maturity, rate, pr, redemption, frequency, [basis])` — Yield of a coupon-bearing security given its price.

`DURATION(settlement, maturity, coupon, yld, frequency, [basis])` — Macaulay duration (weighted average time to cash flows) in years.

`MDURATION(settlement, maturity, coupon, yld, frequency, [basis])` — Modified duration (price sensitivity to yield changes).

`PRICEDISC(settlement, maturity, discount, redemption, [basis])` — Price per $100 of a discounted (zero-coupon) security.

`YIELDDISC(settlement, maturity, pr, redemption, [basis])` — Annual yield of a discounted security.

`PRICEMAT(settlement, maturity, issue, rate, yld, [basis])` — Price per $100 of a security that pays interest at maturity.

`YIELDMAT(settlement, maturity, issue, rate, pr, [basis])` — Annual yield of a security that pays interest at maturity.

`DISC(settlement, maturity, pr, redemption, [basis])` — Discount rate for a security.

`INTRATE(settlement, maturity, investment, redemption, [basis])` — Interest rate for a fully invested security.

`RECEIVED(settlement, maturity, investment, discount, [basis])` — Amount received at maturity for a fully invested security.

`ACCRINT(issue, first_interest, settlement, rate, par, frequency, [basis])` — Accrued interest for a security with periodic interest payments.

`ACCRINTM(issue, settlement, rate, par, [basis])` — Accrued interest for a security that pays at maturity.

## Coupon Bond Helpers

`COUPDAYBS(settlement, maturity, frequency, [basis])` — Days from the start of the coupon period to the settlement date.

`COUPDAYS(settlement, maturity, frequency, [basis])` — Total days in the coupon period containing the settlement date.

`COUPDAYSNC(settlement, maturity, frequency, [basis])` — Days from settlement to the next coupon date.

`COUPNCD(settlement, maturity, frequency, [basis])` — Next coupon date after the settlement date.

`COUPNUM(settlement, maturity, frequency, [basis])` — Number of coupon payments remaining between settlement and maturity.

`COUPPCD(settlement, maturity, frequency, [basis])` — Previous coupon date before the settlement date.

## Treasury Bills

`TBILLEQ(settlement, maturity, discount)` — Bond-equivalent yield for a Treasury bill.

`TBILLPRICE(settlement, maturity, discount)` — Price per $100 face value of a T-bill.

`TBILLYIELD(settlement, maturity, pr)` — Yield of a T-bill given its price.

## Bonds with Odd Periods

`ODDFPRICE(settlement, maturity, issue, first_coupon, rate, yld, redemption, frequency, [basis])` — Price of a security with an irregular first coupon period.

`ODDFYIELD(settlement, maturity, issue, first_coupon, rate, pr, redemption, frequency, [basis])` — Yield of a security with an irregular first coupon period.

`ODDLPRICE(settlement, maturity, last_interest, rate, yld, redemption, frequency, [basis])` — Price of a security with an irregular last coupon period.

`ODDLYIELD(settlement, maturity, last_interest, rate, pr, redemption, frequency, [basis])` — Yield of a security with an irregular last coupon period.

## Interest Rate Conversions

`EFFECT(nominal_rate, npery)` — Effective annual interest rate from a nominal rate compounded npery times per year.

`NOMINAL(effect_rate, npery)` — Nominal annual interest rate from an effective rate.

## Dollar Fractions

`DOLLARDE(fractional_dollar, fraction)` — Converts a price expressed as an integer + fraction (e.g. 1.02 meaning 1 and 2/8) to a decimal.

`DOLLARFR(decimal_dollar, fraction)` — Converts a decimal price to fractional notation.

## Common Patterns

```excel
# Monthly mortgage payment
=PMT(6%/12, 30*12, 200000)        → -$1,199.10

# Loan balance after k payments
=FV(rate/12, k, pmt, -pv)

# CAGR over n years
=RRI(n, start_value, end_value)

# Bond price check (semi-annual, act/act)
=PRICE("2024-01-15","2034-01-15", 4%, 3.8%, 100, 2, 1)

# Project IRR
=IRR({-100000, 25000, 30000, 35000, 40000})

# NPV with initial investment in A1, cash flows in B1:B5
=NPV(10%, B1:B5) + A1
```
