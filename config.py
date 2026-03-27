import os
from pathlib import Path

# Base directory = se481-backend/ folder
BASE_DIR = Path(__file__).parent

# --- Paths ---
RESOURCE_DIR = BASE_DIR / 'resource'
IMAGES_DIR = BASE_DIR / 'resource' / 'images'

RECIPES_RAW_PATH = RESOURCE_DIR / 'recipes.parquet'
REVIEWS_RAW_PATH = RESOURCE_DIR / 'reviews.parquet'
RECIPES_CLEAN_PATH = RESOURCE_DIR / 'recipes_clean.parquet'
BM25_INDEX_PATH = RESOURCE_DIR / 'bm25_index.pkl'
LDA_MODEL_PATH = RESOURCE_DIR / 'lda_model.pkl'
DATABASE_PATH = RESOURCE_DIR / 'app.db'

# --- Flask ---
SECRET_KEY = 'dev-secret-key-change-later'
DEBUG = True

# --- JWT ---
JWT_EXPIRY_HOURS = 24

# --- Search ---
SEARCH_TOP_K = 20        # how many results to return

# --- BM25 tuning ---
BM25_K1 = 1.6       # term frequency saturation
BM25_B = 0.75      # document length normalization

# --- LDA ---
LDA_TOPICS = 50        # number of topics for recommendations

# --- Image ---
IMAGE_DOWNLOAD_TIMEOUT = 5     # seconds before giving up on image download