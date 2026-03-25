import pickle
import pandas as pd
import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
import config

# BM25 is moved here or else 
# AttributeError: Can't get attribute 'BM25' on <module '__main__' 
# from '/Users/minthantko/Documents/cmu/cmu3_2/ir/food_bookmarking_recommendation_project/se481-backend/app.py'>
class BM25(object):
    def __init__(self, vectorizer, b=config.BM25_B, k1=config.BM25_K1):
        self.vectorizer = vectorizer
        self.b = b
        self.k1 = k1

    def fit(self, X):
        self.vectorizer.fit(X)
        self.y = super(TfidfVectorizer, self.vectorizer).transform(X)
        self.avdl = self.y.sum(1).mean()

    def transform(self, q):
        b, k1, avdl = self.b, self.k1, self.avdl
        len_y = self.y.sum(1).A1
        q, = super(TfidfVectorizer, self.vectorizer).transform([q])
        assert sparse.isspmatrix_csr(q)
        y = self.y.tocsc()[:, q.indices]
        denom = y + (k1 * (1 - b + b * len_y / avdl))[:, None]
        idf = self.vectorizer._tfidf.idf_[None, q.indices] - 1.
        numer = y.multiply(np.broadcast_to(idf, y.shape)) * (k1 + 1)
        return (numer / denom).sum(1).A1
    
def identity(x):
    return x

bm25 = None
df_recipes = None

#load bm25 into memo
def load_search_engine():
    global bm25, df_recipes

    # Barricade Strategy ဆိုလား ဘာဆိုလား
    if not config.BM25_INDEX_PATH.exists():
        print("bm25_index.pkl not found.")
        print("Run python scripts/build_index.py")
        return False
    if not config.RECIPES_CLEAN_PATH.exists():
        print("recipes_clean.parquet not found.")
        print("Run: python scripts/build_index.py")
        return False

    print("Loading search engine...")

    #load recipes
    print("Loading recipes_clean.parquet...")
    df_recipes = pd.read_parquet(config.RECIPES_CLEAN_PATH)
    print(f"  Loaded {len(df_recipes)} recipes")

    #load indexed file
    print("Loading bm25_index.pkl...")
    with open(config.BM25_INDEX_PATH, 'rb') as f:
        bm25 = pickle.load(f)
    print("  Search engine ready!")

    return True


#search using bm25
def search(query, top_k=config.SEARCH_TOP_K):
    if bm25 is None or df_recipes is None:
        return []

    scores = bm25.transform(query)
    ranked_indices = np.argsort(scores)[::-1]

    ranked_indices = [i for i in ranked_indices if scores[i] > 0]
    top_indices = ranked_indices[:top_k]

    results = []
    for idx in top_indices:
        recipe = df_recipes.iloc[idx]
        results.append({
            'recipe_id': int(recipe['RecipeId']),
            'name': recipe['Name'],
            'description': recipe['Description'],
            'category': recipe['RecipeCategory'],
            'rating': float(recipe['AggregatedRating']),
            'review_count': int(recipe['ReviewCount']),
            'image_url': recipe['image_url'],
            'ingredients': recipe['ingredients_str'],
            'instructions': recipe['instructions_str'],
            'score': float(scores[idx])
        })

    return results