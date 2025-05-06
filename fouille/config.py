from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file if it exists
load_dotenv()

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]
logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Datasets
RAW_DATASET = INTERIM_DATA_DIR / "frwikisource-current.parquet"
CLEAN_DATASET = INTERIM_DATA_DIR / "frwikisource-cleaned.parquet"
FULL_DATASET = PROCESSED_DATA_DIR / "frwikisource-full.parquet"
TRAIN_DATASET = PROCESSED_DATA_DIR / "frwikisource-train.parquet"
TEST_DATASET = PROCESSED_DATA_DIR / "frwikisource-test.parquet"
DEV_DATASET = PROCESSED_DATA_DIR / "frwikisource-dev.parquet"
TINY_TEST_DATASET = PROCESSED_DATA_DIR / "frwikisource-test-tiny.parquet"
TINY_DEV_DATASET = PROCESSED_DATA_DIR / "frwikisource-dev-tiny.parquet"

# Visualizations
RAW_CATEGORIES = INTERIM_DATA_DIR / "raw-cats.csv"
RAW_CATEGORIES_LIST = INTERIM_DATA_DIR / "raw-cats-list.json"
RAW_CATEGORIES_VIZ = FIGURES_DIR / "raw-cats-distrib.html"
CLEAN_CATEGORIES_VIZ = FIGURES_DIR / "clean-cats-distrib.html"

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
	from tqdm.rich import tqdm

	logger.remove(0)
	logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
	pass
