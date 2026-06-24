---
name: "scikit-learn"
description: "Machine learning in Python with scikit-learn. Use when working with supervised learning (classification, regression), unsupervised learning (clustering, dimensionality reduction), model evaluation, hyperparameter tuning, preprocessing, or building ML pipelines. Provides comprehensive reference documentation for algorithms, preprocessing techniques, pipelines, and best practices."
metadata:
  category: data
  source:
    repository: "https://github.com/k-dense-ai/scientific-agent-skills"
    path: "skills/scikit-learn"
    license_path: "LICENSE.md"
---

# Scikit-learn

## Overview

This skill provides comprehensive guidance for machine learning tasks using scikit-learn, the industry-standard Python library for classical machine learning. Use this skill for classification, regression, clustering, dimensionality reduction, preprocessing, model evaluation, and building production-ready ML pipelines.

## Installation

Tested against **scikit-learn 1.8.0** (stable; December 2025). Requires **Python 3.11–3.14** (free-threaded CPython 3.14 wheels available in 1.8+).

Install the PyPI package **`scikit-learn`** (not the deprecated `sklearn` package on PyPI). Import in code as `sklearn`.

```bash
# Install scikit-learn using uv
uv pip install "scikit-learn>=1.7"

# Optional plotting utilities
uv pip install "scikit-learn[plots]" matplotlib seaborn

# Commonly used with
uv pip install pandas numpy
```

Check your version:

```python
import sklearn
print(sklearn.__version__)
```

## When to Use This Skill

Use the scikit-learn skill when:

- Building classification or regression models
- Performing clustering or dimensionality reduction
- Preprocessing and transforming data for machine learning
- Evaluating model performance with cross-validation
- Tuning hyperparameters with grid or random search
- Creating ML pipelines for production workflows
- Comparing different algorithms for a task
- Working with both structured (tabular) and text data
- Need interpretable, classical machine learning approaches

## Workflow

1. Identify the task type, target variable or unsupervised objective, dataset size, feature types, grouping or time constraints, and success metric.
2. Split training, validation, and test data before fitting preprocessors; use stratification, groups, or time-aware splits when the data requires them.
3. Put imputation, encoding, scaling, feature selection, and the estimator in a `Pipeline` or `ColumnTransformer` so cross-validation cannot leak fitted state.
4. Start with an interpretable baseline, select metrics that match class balance and business cost, and compare candidates under the same cross-validation strategy.
5. Tune only on training/validation folds. Evaluate the final selected pipeline once on the held-out test set and report uncertainty and limitations.
6. Read [workflows-and-examples.md](references/workflows-and-examples.md) only when algorithm catalogs, full examples, or troubleshooting patterns are needed.

## Safety and Correctness

- Never fit preprocessing or feature selection on test data.
- Do not use random splits for temporal data or allow records from the same entity to cross grouped folds.
- Set random seeds where supported and record package versions, features, metrics, and validation strategy.
- Do not load untrusted pickle or joblib model artifacts.
- Avoid claiming causal effects or production readiness from predictive metrics alone.
- For deep learning, distributed training, or data volumes that do not fit scikit-learn's in-memory model, defer to a more suitable framework.

## Reference Navigation

[workflows-and-examples.md](references/workflows-and-examples.md) contains:

- classification and mixed-data pipeline examples
- supervised and unsupervised algorithm selection
- preprocessing, evaluation, tuning, and pipeline composition
- end-to-end classification and clustering workflows
- leakage prevention, scaling guidance, and common failure remedies
