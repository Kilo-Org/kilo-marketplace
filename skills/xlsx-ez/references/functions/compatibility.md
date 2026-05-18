# Excel Compatibility Functions

These functions are kept for backward compatibility with earlier versions of Excel.
Microsoft recommends using the newer equivalents listed in parentheses.

Source: https://support.microsoft.com/en-us/office/excel-functions-by-category-5f91f4e9-7b42-46d2-9bd1-63f26a86c0eb

---

`BETADIST(probability, alpha, beta, [A], [B])` — Cumulative beta probability density function. Use BETA.DIST instead.

`BETAINV(probability, alpha, beta, [A], [B])` — Inverse of the cumulative beta probability density function. Use BETA.INV instead.

`BINOMDIST(number_s, trials, probability_s, cumulative)` — Individual term binomial distribution probability. Use BINOM.DIST instead.

`CHIDIST(x, degrees_freedom)` — One-tailed probability of the chi-squared distribution. Use CHISQ.DIST.RT instead.

`CHIINV(probability, degrees_freedom)` — Inverse of the one-tailed chi-squared probability. Use CHISQ.INV.RT instead.

`CHITEST(actual_range, expected_range)` — Test for independence. Use CHISQ.TEST instead.

`CONFIDENCE(alpha, standard_dev, size)` — Confidence interval for a population mean. Use CONFIDENCE.NORM instead.

`COVAR(array1, array2)` — Population covariance. Use COVARIANCE.P instead.

`EXPONDIST(x, lambda, cumulative)` — Exponential distribution. Use EXPON.DIST instead.

`FDIST(x, degrees_freedom1, degrees_freedom2)` — F probability distribution (right-tailed). Use F.DIST.RT instead.

`FINV(probability, degrees_freedom1, degrees_freedom2)` — Inverse of the F probability distribution. Use F.INV.RT instead.

`FTEST(array1, array2)` — Result of an F-test. Use F.TEST instead.

`GAMMADIST(x, alpha, beta, cumulative)` — Gamma distribution. Use GAMMA.DIST instead.

`GAMMAINV(probability, alpha, beta)` — Inverse of the gamma cumulative distribution. Use GAMMA.INV instead.

`HYPGEOMDIST(sample_s, number_sample, population_s, number_pop)` — Hypergeometric distribution. Use HYPGEOM.DIST instead.

`LOGNORMDIST(x, mean, standard_dev)` — Cumulative lognormal distribution. Use LOGNORM.DIST instead.

`LOGNORMINV(probability, mean, standard_dev)` — Inverse of the lognormal cumulative distribution. Use LOGNORM.INV instead.

`NORMDIST(x, mean, standard_dev, cumulative)` — Normal cumulative distribution. Use NORM.DIST instead.

`NORMINV(probability, mean, standard_dev)` — Inverse of the normal cumulative distribution. Use NORM.INV instead.

`NORMSDIST(z)` — Standard normal cumulative distribution. Use NORM.S.DIST instead.

`NORMSINV(probability)` — Inverse of the standard normal cumulative distribution. Use NORM.S.INV instead.

`PERCENTILE(array, k)` — K-th percentile of values in a data set. Use PERCENTILE.INC instead.

`PERCENTRANK(array, value, [significance])` — Percentage rank of a value in a data set. Use PERCENTRANK.INC instead.

`POISSON(x, mean, cumulative)` — Poisson distribution. Use POISSON.DIST instead.

`QUARTILE(array, quart)` — Quartile of a data set. Use QUARTILE.INC instead.

`RANK(value, array, [order])` — Rank of a number in a list. Use RANK.AVG or RANK.EQ instead.

`STDEV(number1, [number2], ...)` — Standard deviation based on a sample. Use STDEV.S instead.

`STDEVP(number1, [number2], ...)` — Standard deviation based on the entire population. Use STDEV.P instead.

`TDIST(x, degrees_freedom, tails)` — Student's t-distribution. Use T.DIST instead.

`TINV(probability, degrees_freedom)` — Inverse of the Student's t-distribution. Use T.INV instead.

`TTEST(array1, array2, tails, type)` — Probability associated with a Student's t-test. Use T.TEST instead.

`VAR(number1, [number2], ...)` — Variance based on a sample. Use VAR.S instead.

`VARP(number1, [number2], ...)` — Variance based on the entire population. Use VAR.P instead.

`WEIBULL(x, alpha, beta, cumulative)` — Weibull distribution. Use WEIBULL.DIST instead.

`ZTEST(array, x, [sigma])` — One-tailed probability-value of a z-test. Use Z.TEST instead.
