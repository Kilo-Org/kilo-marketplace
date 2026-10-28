import os
import sys
from pathlib import Path


def get_ultimate_answer() -> int:
    """Function to illustrate testing in this project setup"""
    return 42


class AMLLogger:
    """Logger that uses MLflow when running inside an Azure ML Job, otherwise prints to stderr."""

    def __init__(self) -> None:
        # "MLFLOW_TRACKING_URI" is set-up when running inside an Azure ML Job

        self._tracking_uri = os.getenv("MLFLOW_TRACKING_URI", None)
        if self._tracking_uri:
            # heavyish import, use it only when necessary
            import mlflow

            mlflow.set_tracking_uri(self._tracking_uri)
            self._mlflow = mlflow
        else:
            self._mlflow = None

    def set_tags(self, tags: dict[str, str]) -> None:
        if self._mlflow:
            self._mlflow.set_tags(tags)
        else:
            for name, value in tags.items():
                print(f"tag:{name}={value}", file=sys.stderr)

    def log_metrics(self, metrics: dict[str, int | float]) -> None:
        if self._mlflow:
            self._mlflow.log_metrics(metrics)
        else:
            for name, value in metrics.items():
                print(f"metric:{name}={value}", file=sys.stderr)


def mypkg(data_path: Path, greeting: str = "Hello", outputs_dir: Path = Path("./outputs")):
    """Main function with the things needed to get started with AzureML

    :param data_path: Path where data is stored. Here to exemplify how to connect AzureML data
        (see `aml-job.yaml`).
    :param greeting: Word with which to greet the world.
    :param outputs_dir: Directory where to write outputs. Defaults to `./outputs` which is the
        default AzureML outputs directory.
    """
    aml_logger = AMLLogger()
    # Tags are shown as properties of the job in the Azure ML dashboard. Run once.
    # Good practice to set input values as tags for reproducibility
    tags = {"greeting": greeting}
    aml_logger.set_tags(tags)

    # Console logs in AzureML are captured from stdout and stderr
    print(f"{greeting} world!")
    print(f"'data_path' is pointing to '{data_path}'", file=sys.stderr)
    if isinstance(data_path, Path) and data_path.is_dir():
        for file in data_path.iterdir():
            print(f"  {file.relative_to(data_path)}", file=sys.stderr)

    # Metrics are numerical values
    metrics = {"answer": get_ultimate_answer()}
    aml_logger.log_metrics(metrics)

    values = [1.0, 0.0, 1.0, 2.0, 3.0, 2.0, 4.0]
    for v in values:
        metrics = {"value": v}
        aml_logger.log_metrics(metrics)

    outputs_dir.mkdir(exist_ok=True, parents=True)
    out_filepath = outputs_dir / "hello.txt"
    out_filepath.write_text("Hello darkness, my old friend!")


def main():
    import argparse
    import sys
    from pathlib import Path

    assume_debug = len(sys.argv) <= 1
    if assume_debug:
        # Useful to make it easier to trigger directly from VSCode play/debug button
        print("WARNING: Using debug args because no args were passed", file=sys.stderr)
        args_dict = {
            "data_path": Path("path/to/data"),
            "greeting": "Hello",
            # on isolated run reproduce remote outputs, on direct run keep at repo root
            "outputs_dir": Path("../outputs") if Path.cwd().name == "src" else Path("./outputs"),
        }
    else:
        parser = argparse.ArgumentParser(description="Driver script for mypkg")
        parser.add_argument("--data_path", type=Path, help="Path to data", required=True)
        parser.add_argument("--greeting", type=str, help="Greeting word", required=True)

        args = parser.parse_args()
        args_dict = vars(args)

    mypkg(**args_dict)


if __name__ == "__main__":
    main()
