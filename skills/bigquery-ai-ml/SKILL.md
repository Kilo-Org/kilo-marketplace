---
name: "bigquery-ai-ml"
description: "This skill should be used when implementing BigQuery AI and ML workflows with SQL functions such as AI.FORECAST, AI.DETECT_ANOMALIES, and AI.GENERATE or when integrating BigQuery with Vertex AI."
metadata:
  category: data
  source:
    repository: "https://github.com/google/skills"
    path: "skills/cloud/bigquery-ai-ml"
    license_path: "LICENSE"
---

# BigQuery AI & ML

BigQuery integrates with Vertex AI to provide powerful machine learning and
generative AI capabilities directly within SQL queries using built-in functions
like `AI.FORECAST`, `AI.DETECT_ANOMALIES`, and `AI.GENERATE`.

## Reference Directory

-   [AI Forecast](references/ai_forecast.md): Leveraging pre-trained
    TimesFM model for forecasting without custom training.

-   [AI Detect Anomalies](references/ai_detect_anomalies.md): Identify
    deviations in time series data using pre-trained TimesFM model.

-   [AI Generate](references/ai_generate.md): General-purpose text and
    content generation using Gemini models.

## Related Skills

- [BigQuery Basics Skill](../bigquery-basics):
  SKILL.md file for core BigQuery concepts, resource management, CLI,
  and client libraries.
