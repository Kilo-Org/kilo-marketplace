---
name: "datarobot-data-preparation"
description: "Tools and guidance for data upload, dataset management, data validation, and preparing data for DataRobot projects. Use when uploading datasets, managing data, or validating data for DataRobot."
metadata:
  category: data
  source:
    repository: "https://github.com/datarobot-oss/datarobot-agent-skills"
    path: "skills/datarobot-data-preparation"
    license_path: "LICENSE"
---

# DataRobot Data Preparation Skill

This skill provides guidance for preparing and managing data in DataRobot, including uploading datasets, validating data quality, and managing dataset versions.

## Quick Start

**Most common use case**: Upload and validate a dataset

1. **Upload dataset**: `upload_dataset(file_path, dataset_name)` to upload data
2. **Validate data**: `validate_dataset(dataset_id)` to check data quality
3. **Check schema**: `get_dataset_schema(dataset_id)` to review structure

**Example**: "Upload sales_data.csv and check if it's ready for training"

## When to use this skill

Use this skill when you need to:
- Upload datasets to DataRobot
- Validate data before project creation
- Manage dataset versions and updates
- Check data quality and completeness
- Prepare data for training or predictions
- Handle data format conversions
- Connect to external data sources

## Key capabilities

### 1. Dataset Upload

- Upload CSV, Parquet, and other file formats
- Connect to databases and data warehouses
- Handle large datasets efficiently
- Manage dataset metadata and descriptions

### 2. Data Validation

- Validate data formats and schemas
- Check for missing values and data quality issues
- Verify column types and formats
- Identify potential data problems

### 3. Dataset Management

- List and search datasets
- Update dataset metadata
- Create dataset versions
- Delete or archive old datasets

### 4. Data Preparation

- Clean and preprocess data
- Handle missing values
- Format data for DataRobot requirements
- Prepare prediction datasets

## Workflow examples

### Example 1: Upload and validate dataset

**User request**: "Upload my sales_data.csv file and check if it's ready for training."

**Agent workflow**:
1. Upload the CSV file to DataRobot
2. Validate the dataset structure and format
3. Check for missing values and data quality issues
4. Verify column types are appropriate
5. Check for potential issues (leakage, formatting)
6. Report validation results and recommendations

### Example 2: Prepare prediction dataset

**User request**: "Prepare a prediction dataset based on the training data structure from project abc123."

**Agent workflow**:
1. Get the training dataset structure from the project
2. Identify required columns and data types
3. Create a template with the same structure
4. Validate the template matches requirements
5. Provide guidance on filling in prediction values

## Using DataRobot SDK

This skill guides you to use the DataRobot Python SDK directly. Install the SDK if needed:

```bash
pip install datarobot
```

### Key SDK Operations

Use these DataRobot SDK methods for data management:

**Dataset Operations**:
- `dr.Dataset.create_from_file(file_path, name)` - Upload dataset
- `dr.Dataset.get(dataset_id)` - Get dataset details
- `dr.Dataset.list()` - List all datasets
- `dataset.row_count` - Get row count
- `dataset.column_count` - Get column count

**Dataset Information**:
- `dataset.name` - Dataset name
- `dataset.id` - Dataset ID
- `dataset.created_at` - Creation timestamp

See the [Common Patterns](#common-patterns) section below for complete examples.

## Helper Scripts

This skill includes executable helper scripts that Claude can run directly:

- `scripts/upload_dataset.py` - Upload a dataset file to DataRobot

**Usage example**:
```bash
# Upload dataset
python scripts/upload_dataset.py sales_data.csv "Sales Data Q4 2024"
```

Claude can run this script directly or use it as reference when writing code.

## Best practices

1. **Data quality**: Clean and validate data before upload
2. **File formats**: Use appropriate formats (CSV for small, Parquet for large)
3. **Naming conventions**: Use clear, descriptive dataset names
4. **Metadata**: Add descriptions and tags for better organization
5. **Versioning**: Create versions for important datasets
6. **Data validation**: Always validate data before using in projects

## Common patterns

### Pattern 1: Upload and validate
```python
import datarobot as dr
import os

# Initialize client
client = dr.Client(
    token=os.getenv("DATAROBOT_API_TOKEN"),
    endpoint=os.getenv("DATAROBOT_ENDPOINT")
)

# Upload dataset
dataset = dr.Dataset.create_from_file(
    file_path="sales_data.csv",
    name="Sales Data Q4 2024"
)

print(f"Dataset ID: {dataset.id}")
print(f"Rows: {dataset.row_count}, Columns: {dataset.column_count}")

# Get dataset details
dataset_info = dr.Dataset.get(dataset.id)
print(f"Dataset name: {dataset_info.name}")
print(f"Created: {dataset_info.created_at}")
```

### Pattern 2: Dataset management
```python
import datarobot as dr

# List all datasets
datasets = dr.Dataset.list()
print(f"Found {len(datasets)} datasets")

# Search for specific dataset
for dataset in datasets:
    if "sales" in dataset.name.lower():
        print(f"Found: {dataset.name} (ID: {dataset.id})")

# Get specific dataset
dataset = dr.Dataset.get("abc123")
print(f"Dataset: {dataset.name}")
print(f"Size: {dataset.row_count} rows x {dataset.column_count} columns")
```

## Data format requirements

### CSV Files
- UTF-8 encoding recommended
- Headers in first row
- Consistent delimiters (comma, tab)
- Proper date/time formatting

### Parquet Files
- Columnar format, efficient for large datasets
- Preserves data types
- Better compression than CSV

### Database Connections
- Support for various databases
- Connection credentials required
- Query-based data access

## Data quality checks

Common checks to perform:

- **Missing values**: Identify columns with high missing value rates
- **Data types**: Verify columns have correct types
- **Value ranges**: Check for outliers and invalid values
- **Duplicates**: Identify duplicate records
- **Consistency**: Check for data consistency issues

## Error handling

Common errors and solutions:

- **Upload failures**: Check file format, size limits, encoding
- **Validation errors**: Fix data quality issues before proceeding
- **Schema mismatches**: Ensure data structure matches expectations
- **Access issues**: Verify permissions for dataset operations

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
- [DataRobot Data Management Documentation](https://docs.datarobot.com/en/docs/data/index.html)
- [Data Management: Uploading Datasets](https://docs.datarobot.com/en/docs/data/index.html)
- [Data Management: Data Quality and Validation](https://docs.datarobot.com/en/docs/data/index.html)
