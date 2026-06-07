import init_logger
from dotenv import load_dotenv
load_dotenv(override=True, dotenv_path=".env.local")

from etl.pipeline import run_pipeline


def main():
    run_pipeline()


if __name__ == "__main__":
    main()
