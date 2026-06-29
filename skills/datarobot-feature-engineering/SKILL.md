---
name: datarobot-feature-engineering
description: >-
  Guidance for feature engineering, feature discovery, feature importance
  analysis, and understanding DataRobot's automated feature engineering
  capabilities. Use when working with feature engineering, feature discovery, or
  analyzing feature importance in DataRobot.
metadata:
  category: data
  source:
    repository: 'https://github.com/datarobot-oss/datarobot-agent-skills'
    path: skills/datarobot-feature-engineering
    license_path: LICENSE
    commit: f4b3c29db60e1d735285a6f51328a69a2b500338
---

# DataRobot Feature Engineering Skill

This skill provides guidance for working with features in DataRobot, including understanding automated feature engineering, analyzing feature importance, and optimizing feature sets.

## Quick Start

**Most common use case**: Analyze feature importance for a model

1. **Get feature importance**: `get_feature_importance(model_id)` to get importance scores
2. **Analyze top features**: Sort by importance and identify key drivers
3. **Export feature list**: `export_feature_list(project_id)` to document features

**Example**: "Show me the top 10 most important features for model xyz123"

## When to use this skill

Use this skill when you need to:
- Understand what features DataRobot creates automatically
- Analyze feature importance for models
- Discover which features drive predictions
- Optimize feature sets for better performance
- Understand feature types and transformations
- Export feature lists and definitions

## Key capabilities

### 1. Feature Discovery

- Understand automated feature engineering in DataRobot
- Review derived features and transformations
- Identify feature types (numeric, categorical, text, date)
- Explore feature relationships and interactions

### 2. Feature Importance Analysis

- Get feature importance scores for models
- Understand which features drive predictions
- Compare feature importance across models
- Identify redundant or low-value features

### 3. Feature Optimization

- Select important features for model performance
- Remove low-importance features to reduce complexity
- Understand feature impact on predictions
- Optimize feature sets for deployment

### 4. Feature Documentation

- Export feature lists and definitions
- Document feature transformations
- Understand feature derivation logic
- Share feature information with stakeholders

## Workflow examples

### Example 1: Analyze feature importance

**User request**: "Show me the top 10 most important features for model xyz123 and explain what they mean."

**Agent workflow**:
1. Get feature importance scores for the model
2. Sort features by importance (descending)
3. Get top 10 features with their scores
4. Retrieve feature metadata and descriptions
5. Explain what each feature represents and why it's important
6. Provide insights on feature relationships

### Example 2: Optimize feature set for deployment

**User request**: "Create a simplified feature set for deployment abc123, keeping only features with importance > 0.1."

**Agent workflow**:
1. Get feature importance for the deployed model
2. Filter features by importance threshold (> 0.1)
3. Verify filtered features are sufficient for predictions
4. Document the optimized feature set
5. Update deployment configuration if needed

## Using DataRobot SDK

This skill guides you to use the DataRobot Python SDK directly. Install the SDK if needed:

```bash
pip install datarobot
```

### Key SDK Operations

Use these DataRobot SDK methods for feature analysis:

**Feature Information**:
- `model.get_features()` - List all features in a model
- `model.get_feature_impact()` - Get feature importance scores
- `project.get_features()` - List features in a project

**Feature Analysis**:
- `feature.name` - Feature name
- `feature.feature_type` - Feature type (Numeric, Categorical, etc.)
- `feature.importance` - Feature importance score

See the [Common Patterns](#common-patterns) section below for complete examples.

## Best practices

1. **Review automated features**: DataRobot creates many derived features automatically - review them
2. **Focus on important features**: Pay attention to high-importance features for insights
3. **Understand feature types**: Different feature types require different handling
4. **Feature documentation**: Document important features for stakeholders
5. **Feature selection**: Consider removing very low-importance features for simplicity
6. **Feature stability**: Consider feature stability over time, not just importance

## Common patterns

### Pattern 1: Feature importance analysis
```python
import datarobot as dr
import os

# Initialize client
client = dr.Client(
    token=os.getenv("DATAROBOT_API_TOKEN"),
    endpoint=os.getenv("DATAROBOT_ENDPOINT")
)

# Get model and feature importance
model = dr.Model.get("xyz123")
feature_impact = model.get_feature_impact()

# Sort by importance
sorted_features = sorted(
    feature_impact,
    key=lambda x: x.get('impactNormalized', 0),
    reverse=True
)

# Get top 10 features
top_features = sorted_features[:10]
for feature in top_features:
    print(f"{feature['featureName']}: {feature.get('impactNormalized', 0):.3f}")
```

### Pattern 2: Feature filtering
```python
import datarobot as dr

# Get model and feature importance
model = dr.Model.get("xyz123")
feature_impact = model.get_feature_impact()

# Filter by importance threshold (> 0.1)
important_features = [
    f for f in feature_impact
    if f.get('impactNormalized', 0) > 0.1
]

print(f"Found {len(important_features)} features with importance > 0.1")
```

## Feature types in DataRobot

### Numeric Features
- Continuous numeric values
- Automatically scaled and normalized
- Can be used in mathematical operations

### Categorical Features
- Discrete categories or labels
- Automatically encoded (one-hot, target encoding)
- Important for many model types

### Text Features
- Text data (descriptions, comments)
- Automatically processed with NLP techniques
- Creates multiple text-derived features

### Date/Time Features
- Temporal data
- Automatically creates time-based features
- Important for time series models

## Understanding feature importance

Feature importance scores indicate:
- **High importance (> 0.1)**: Feature significantly impacts predictions
- **Medium importance (0.05-0.1)**: Feature contributes to predictions
- **Low importance (< 0.05)**: Feature has minimal impact

Note: Importance thresholds vary by model type and problem domain.

## Error handling

Common errors and solutions:

- **Feature not found**: Verify feature name and model compatibility
- **Importance unavailable**: Some model types don't provide importance scores
- **Feature access errors**: Check project and model permissions

## SDK Setup

### Install DataRobot SDK

```bash
pip install datarobot
```

### Initialize Client

```python
import datarobot as dr
import os

client = dr.Client(
    token=os.getenv("DATAROBOT_API_TOKEN"),
    endpoint=os.getenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com")
)
```

## Resources

- [DataRobot Python SDK Documentation](https://datarobot-public-api-client.readthedocs-hosted.com/)
- [DataRobot Feature Engineering Documentation](https://docs.datarobot.com/en/docs/modeling/index.html)
- [Feature Importance Guide](https://docs.datarobot.com/en/docs/modeling/analyze-models/index.html)
- [Feature Discovery Documentation](https://docs.datarobot.com/en/docs/data/transform-data/feature-discovery/index.html)
