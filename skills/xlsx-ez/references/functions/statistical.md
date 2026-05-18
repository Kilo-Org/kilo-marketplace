# Excel Statistical Functions

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

---

## Counting

`COUNT(value1, [value2], ...)` — Counts cells containing numbers. Ignores text, blanks, and logical values.

`COUNTA(value1, [value2], ...)` — Counts non-empty cells (numbers, text, errors, logical values).

`COUNTBLANK(range)` — Counts empty cells in a range.

`COUNTIF(range, criteria)` — Counts cells matching a single condition.
```excel
=COUNTIF(A:A, "North")
=COUNTIF(B:B, ">1000")
=COUNTIF(A:A, "A*")          → starts with "A" (wildcard)
=COUNTIF(A:A, A1)             → matches cell A1's value
```

`COUNTIFS(range1, criteria1, [range2, criteria2], ...)` — Counts cells matching all conditions.
```excel
=COUNTIFS(A:A,"North", B:B,">1000")
```

## Central Tendency

`AVERAGE(number1, [number2], ...)` — Arithmetic mean. Ignores text and blanks; counts 0.

`AVERAGEA(value1, [value2], ...)` — Arithmetic mean including TRUE=1, FALSE=0, text=0.

`AVERAGEIF(range, criteria, [average_range])` — Mean of cells where a condition is met.

`AVERAGEIFS(average_range, range1, criteria1, [range2, criteria2], ...)` — Mean where all conditions are met.

`MEDIAN(number1, [number2], ...)` — Middle value of a sorted dataset. For an even count, averages the two middle values.

`MODE.SNGL(number1, [number2], ...)` — Most frequently occurring value. Returns the lowest if tied.

`MODE.MULT(number1, [number2], ...)` — All modes (returns a vertical array; requires spill space in 365 or Ctrl+Shift+Enter).

`GEOMEAN(number1, [number2], ...)` — Geometric mean: (x₁ × x₂ × … × xₙ)^(1/n). Used for growth rates.

`HARMEAN(number1, [number2], ...)` — Harmonic mean: n / Σ(1/xᵢ). Used for average rates and ratios.

`TRIMMEAN(array, percent)` — Mean after excluding the top and bottom percent/2 of values. percent=0.1 excludes the extreme 10%.

## Dispersion / Spread

`STDEV.S(number1, [number2], ...)` — Sample standard deviation (divides by n−1).

`STDEV.P(number1, [number2], ...)` — Population standard deviation (divides by n).

`STDEVA(value1, [value2], ...)` — Sample std dev including TRUE=1, FALSE=0, text=0.

`STDEVPA(value1, [value2], ...)` — Population std dev including TRUE/FALSE/text.

`VAR.S(number1, [number2], ...)` — Sample variance.

`VAR.P(number1, [number2], ...)` — Population variance.

`VARA(value1, ...)` / `VARPA(value1, ...)` — Variance including TRUE/FALSE/text.

`AVEDEV(number1, [number2], ...)` — Mean of absolute deviations from the mean.

`DEVSQ(number1, [number2], ...)` — Sum of squared deviations from the mean.

## Range Functions

`MAX(number1, [number2], ...)` — Maximum value. Ignores text and blanks.

`MAXA(value1, ...)` — Maximum including TRUE=1, FALSE=0, text=0.

`MAXIFS(max_range, range1, criteria1, [range2, criteria2], ...)` — Maximum where all conditions are met.

`MIN(number1, [number2], ...)` — Minimum value.

`MINA(value1, ...)` — Minimum including TRUE/FALSE/text.

`MINIFS(min_range, range1, criteria1, [range2, criteria2], ...)` — Minimum where all conditions are met.

`LARGE(array, k)` — k-th largest value. LARGE(A:A, 1) = MAX.

`SMALL(array, k)` — k-th smallest value. SMALL(A:A, 1) = MIN.

## Ranking and Percentiles

`RANK.EQ(number, ref, [order])` — Rank with ties all getting the same rank (skips subsequent ranks). order=0 descending (default), 1 ascending.

`RANK.AVG(number, ref, [order])` — Rank with ties averaged.

`PERCENTILE.INC(array, k)` — k-th percentile (inclusive; k=0 returns MIN, k=1 returns MAX).

`PERCENTILE.EXC(array, k)` — k-th percentile (exclusive; k must be between 0 and 1 exclusive).

`PERCENTRANK.INC(array, x, [significance])` — Percentage rank of x in array (inclusive).

`PERCENTRANK.EXC(array, x, [significance])` — Percentage rank of x in array (exclusive).

`QUARTILE.INC(array, quart)` — Quartile (inclusive). quart: 0=min, 1=Q1, 2=median, 3=Q3, 4=max.

`QUARTILE.EXC(array, quart)` — Quartile (exclusive).

`STANDARDIZE(x, mean, standard_dev)` — Returns the z-score: (x − mean) / standard_dev.

## Correlation and Regression

`CORREL(array1, array2)` — Pearson correlation coefficient (−1 to 1).

`PEARSON(array1, array2)` — Same as CORREL.

`RSQ(known_y's, known_x's)` — R² (square of Pearson coefficient).

`COVARIANCE.P(array1, array2)` — Population covariance.

`COVARIANCE.S(array1, array2)` — Sample covariance.

`SLOPE(known_y's, known_x's)` — Slope of a linear regression line.

`INTERCEPT(known_y's, known_x's)` — Y-intercept of a linear regression line.

`STEYX(known_y's, known_x's)` — Standard error of the predicted y-values in a linear regression.

`LINEST(known_y's, [known_x's], [const], [stats])` — Full linear regression statistics as an array (slope, intercept, r², standard errors, etc.). Enter with Ctrl+Shift+Enter in older Excel.

`LOGEST(known_y's, [known_x's], [const], [stats])` — Like LINEST for exponential regression.

`TREND(known_y's, [known_x's], [new_x's], [const])` — Predicted y-values from a linear regression.

`GROWTH(known_y's, [known_x's], [new_x's], [const])` — Predicted y-values from an exponential regression.

`FORECAST.LINEAR(x, known_y's, known_x's)` — Predicted y at a given x using linear regression.

`FORECAST(x, known_y's, known_x's)` — Same as FORECAST.LINEAR (legacy name).

`FISHER(x)` — Fisher transformation: ln((1+x)/(1−x)) / 2. Stabilizes correlation distributions.

`FISHERINV(y)` — Inverse Fisher transformation.

## Time Series (Excel 365+)

`FORECAST.ETS(target_date, values, timeline, [seasonality], [data_completion], [aggregation])` — Exponential smoothing forecast for a future date.

`FORECAST.ETS.CONFINT(target_date, values, timeline, [confidence_level], ...)` — Confidence interval for ETS forecast.

`FORECAST.ETS.SEASONALITY(values, timeline, [data_completion], [aggregation])` — Detects the length of the seasonal pattern.

`FORECAST.ETS.STAT(values, timeline, statistic_type, ...)` — Returns a named statistic from the ETS model (alpha, beta, gamma, MASE, SMAPE, MAE, RMSE, step size).

## Frequency and Distribution Fitting

`FREQUENCY(data_array, bins_array)` — Returns a vertical array of frequency counts. Spills in 365; enter with Ctrl+Shift+Enter + one extra row in older Excel.

`PROB(x_range, prob_range, [lower_limit], [upper_limit])` — Probability that values in x_range fall within a range, using probabilities from prob_range.

## Normal Distribution

`NORM.DIST(x, mean, standard_dev, cumulative)` — CDF (cumulative=TRUE) or PDF (cumulative=FALSE) of a normal distribution.

`NORM.INV(probability, mean, standard_dev)` — Inverse of NORM.DIST; returns x for a given cumulative probability.

`NORM.S.DIST(z, cumulative)` — Standard normal (μ=0, σ=1) CDF or PDF.

`NORM.S.INV(probability)` — Inverse of the standard normal CDF.

`PHI(x)` — Standard normal PDF at x.

`GAUSS(z)` — Probability of a standard normal between 0 and z: NORM.S.DIST(z,TRUE) − 0.5.

`CONFIDENCE.NORM(alpha, standard_dev, size)` — Half-width of a confidence interval for the mean (normal). alpha = significance level (e.g. 0.05 for 95% CI).

`CONFIDENCE.T(alpha, standard_dev, size)` — Half-width using the t-distribution (better for small samples).

## Other Distributions

`T.DIST(x, deg_freedom, cumulative)` / `T.DIST.RT(x, deg)` / `T.DIST.2T(x, deg)` — Student's t CDF (left-tailed, right-tailed, two-tailed).

`T.INV(probability, deg_freedom)` / `T.INV.2T(probability, deg_freedom)` — Inverse t-distribution.

`T.TEST(array1, array2, tails, type)` — p-value for a t-test. type: 1=paired, 2=two-sample equal variance, 3=two-sample unequal variance.

`CHISQ.DIST(x, deg_freedom, cumulative)` / `CHISQ.DIST.RT(x, deg)` — Chi-squared distribution.

`CHISQ.INV(probability, deg_freedom)` / `CHISQ.INV.RT(probability, deg)` — Inverse chi-squared.

`CHISQ.TEST(actual_range, expected_range)` — Chi-squared test for independence.

`F.DIST(x, df1, df2, cumulative)` / `F.DIST.RT(x, df1, df2)` — F distribution.

`F.INV(probability, df1, df2)` / `F.INV.RT(probability, df1, df2)` — Inverse F distribution.

`F.TEST(array1, array2)` — p-value for an F-test of equal variances.

`BINOM.DIST(number_s, trials, probability_s, cumulative)` — Binomial distribution.

`BINOM.DIST.RANGE(trials, probability_s, number_s, [number_s2])` — Probability of getting between number_s and number_s2 successes.

`BINOM.INV(trials, probability_s, alpha)` — Smallest k such that cumulative binomial ≥ alpha.

`NEGBINOM.DIST(number_f, number_s, probability_s, cumulative)` — Negative binomial (failures before the number_s-th success).

`POISSON.DIST(x, mean, cumulative)` — Poisson distribution.

`EXPON.DIST(x, lambda, cumulative)` — Exponential distribution.

`GAMMA.DIST(x, alpha, beta, cumulative)` — Gamma distribution.

`GAMMA.INV(probability, alpha, beta)` — Inverse gamma distribution.

`GAMMALN(x)` / `GAMMALN.PRECISE(x)` — Natural log of the gamma function Γ(x).

`GAMMA(number)` — Gamma function Γ(n).

`BETA.DIST(x, alpha, beta, [cumulative], [A], [B])` — Beta distribution.

`BETA.INV(probability, alpha, beta, [A], [B])` — Inverse beta distribution.

`LOGNORM.DIST(x, mean, standard_dev, cumulative)` — Lognormal distribution.

`LOGNORM.INV(probability, mean, standard_dev)` — Inverse lognormal.

`HYPGEOM.DIST(sample_s, number_sample, population_s, number_pop, cumulative)` — Hypergeometric distribution.

`WEIBULL.DIST(x, alpha, beta, cumulative)` — Weibull distribution.

`Z.TEST(array, x, [sigma])` — One-tailed p-value for a z-test.

## Shape Statistics

`KURT(number1, [number2], ...)` — Kurtosis (excess kurtosis; normal distribution = 0).

`SKEW(number1, [number2], ...)` — Skewness of a sample distribution.

`SKEW.P(number1, [number2], ...)` — Skewness based on the entire population.

## Common Patterns

```excel
# Descriptive stats for a range
Mean:   =AVERAGE(A:A)
Median: =MEDIAN(A:A)
StdDev: =STDEV.S(A:A)
CV:     =STDEV.S(A:A)/AVERAGE(A:A)   ← coefficient of variation

# COUNTIFS for a date range
=COUNTIFS(dates, ">="&DATE(2024,1,1), dates, "<"&DATE(2025,1,1))

# Conditional average ignoring zeros
=AVERAGEIF(A:A, "<>0")

# Percentile-based outlier threshold
Upper: =PERCENTILE.INC(data, 0.95)
Lower: =PERCENTILE.INC(data, 0.05)

# 95% confidence interval half-width
=CONFIDENCE.T(0.05, STDEV.S(data), COUNT(data))

# Correlation matrix element (A vs B)
=CORREL(A:A, B:B)

# Linear regression predicted value
=SLOPE(y,x)*new_x + INTERCEPT(y,x)
# Or equivalently:
=FORECAST.LINEAR(new_x, y, x)
```
