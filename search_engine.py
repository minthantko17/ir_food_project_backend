import pickle
import pandas as pd
import numpy as np
import config

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