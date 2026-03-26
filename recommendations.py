import pandas as pd
import numpy as np
import pickle
import search_engine
import config
from database import get_db

# lda 
lda_model = None
lda_vectorizer = None

def load_recommender():
    global lda_model, lda_vectorizer

    if not config.LDA_MODEL_PATH.exists():
        print("lda_model.pkl not found!")
        return False

    print("Loading recommender (lda_model.pkl)...")
    with open(config.LDA_MODEL_PATH, 'rb') as f:
        saved = pickle.load(f)

    lda_model = saved['lda']
    lda_vectorizer = saved['vectorizer']
    print("Recommender loaded!")
    return True

# get vector for a recipe text
def get_recipe_topic_vector(text):
    X = lda_vectorizer.transform([text])
    vec = lda_model.transform(X)
    return vec[0]


# get all bookmarked recipe id
def get_user_bookmarked_ids(user_id):
    conn = get_db()
    try:
        rows = conn.execute(
            'SELECT DISTINCT recipe_id FROM bookmarks WHERE user_id = ?',
            (user_id,)
        ).fetchall()
        return [r['recipe_id'] for r in rows]
    finally:
        conn.close()


def recipe_to_dict(recipe): #row to dict
    return {
        'recipe_id': int(recipe['RecipeId']),
        'name': recipe['Name'],
        'description': recipe['Description'],
        'category': recipe['RecipeCategory'],
        'rating': float(recipe['AggregatedRating']),
        'review_count': int(recipe['ReviewCount']),
        'image_url': recipe['image_url'],
        'ingredients': recipe['ingredients_str'],
        'instructions': recipe['instructions_str'],
    }


# get recommendation from all folders
def get_recommended_for_you(user_id, n=10):
    df = search_engine.df_recipes
    if df is None or lda_model is None:
        return []

    bookmarked_ids = get_user_bookmarked_ids(user_id)

    # default return top rated if no bookmarks
    if not bookmarked_ids:
        top = df[df['AggregatedRating'] > 0]\
                .sort_values('AggregatedRating', ascending=False)\
                .head(n)
        return [recipe_to_dict(r) for _, r in top.iterrows()]

    bookmarked = df[df['RecipeId'].isin(
        [float(i) for i in bookmarked_ids]
    )]

    if bookmarked.empty:
        return []

    # average LDA topic vector
    topic_vectors = []
    for _, recipe in bookmarked.iterrows():
        vec = get_recipe_topic_vector(recipe['search_text_clean'])
        topic_vectors.append(vec)
    user_profile = np.mean(topic_vectors, axis=0)

    # leave bookmarked recipes for recommendation,
    candidates = df[~df['RecipeId'].isin(
        [float(i) for i in bookmarked_ids]
    )].copy()

    candidate_vectors = lda_vectorizer.transform(
        candidates['search_text_clean'].fillna('')
    )
    candidate_topics = lda_model.transform(candidate_vectors)

    # cosine similarity
    user_norm = user_profile/(np.linalg.norm(user_profile) + 1e-10)
    candidate_norms = candidate_topics/(
        np.linalg.norm(candidate_topics, axis=1, keepdims=True) + 1e-10
    )
    similarities = candidate_norms.dot(user_norm)

    top_indices = np.argsort(similarities)[::-1][:n]
    top_recipes = candidates.iloc[top_indices]

    return [recipe_to_dict(r) for _, r in top_recipes.iterrows()]

# get random
def get_random_recipes(n=10):
    df = search_engine.df_recipes
    if df is None:
        return []

    random_recipes = df.sample(n=n)
    return [recipe_to_dict(r) for _, r in random_recipes.iterrows()]
