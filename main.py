import argparse
import init_logger
from dotenv import load_dotenv
load_dotenv(override=True, dotenv_path=".env.local")

from etl.pipeline import run_pipeline, TASKS


def main():
    parser = argparse.ArgumentParser(description="Pipeline ETL de Water Watch")
    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        choices=list(TASKS.keys()),
        help="Módulo a cargar (por defecto: todos)",
    )
    args = parser.parse_args()
    run_pipeline(only=args.source)


if __name__ == "__main__":
    main()
