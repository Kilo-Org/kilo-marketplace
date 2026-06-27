#!/usr/bin/env python3
# Copyright (c) 2026 DataRobot, Inc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Upload a dataset file to DataRobot.

Usage:
    python upload_dataset.py <file_path> <dataset_name>

Supports CSV, Parquet, and other formats.
"""

import sys
import json
import os
import datarobot as dr


def upload_dataset(file_path: str, dataset_name: str) -> dict:
    """
    Upload a dataset file to DataRobot.

    Args:
        file_path: Path to the dataset file (CSV, Parquet, etc.)
        dataset_name: Name for the dataset

    Returns:
        Dataset information including dataset_id
    """
    # Initialize client
    client = dr.Client(
        token=os.getenv("DATAROBOT_API_TOKEN"),
        endpoint=os.getenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com"),
    )

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Upload dataset
    dataset = dr.Dataset.create_from_file(file_path=file_path, name=dataset_name)

    return {
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "file_path": file_path,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python upload_dataset.py <file_path> <dataset_name>",
            file=sys.stderr,
        )
        sys.exit(1)

    file_path = sys.argv[1]
    dataset_name = sys.argv[2]

    try:
        result = upload_dataset(file_path, dataset_name)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
