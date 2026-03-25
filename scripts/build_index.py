import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import pickle
import re
import nltk
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from scipy import sparse

import config

print("Preprocess and build index..")

stop_words = set(stopwords.words('english'))
ps = PorterStemmer()

def preprocess(text):
    text = re.sub(r'[^A-Za-z]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    tokens = word_tokenize(text)
    tokens = [w for w in tokens
              if w not in stop_words]
    tokens = [w for w in tokens if len(w) > 2]
    tokens = [ps.stem(w) for w in tokens]
    return ' '.join(tokens)


def load_data():
    print("\nLoading recipes.parquet...")
    df = pd.read_parquet(config.RECIPES_RAW_PATH)
    print(f"    Loaded {len(df)} recipes")
    return df


def prepare_recipes(df):
    print("\nCleaning and preparing recipes...")
    df['Description'] = df['Description'].fillna('')
    df['RecipeCategory'] = df['RecipeCategory'].fillna('Unknown')
    df['AggregatedRating'] = df['AggregatedRating'].fillna(0.0)
    df['ReviewCount'] = df['ReviewCount'].fillna(0).astype(int)

    # change array to strings
    df['ingredients_str'] = df['RecipeIngredientParts'].apply(
        lambda x: ' '.join(x) if isinstance(x, np.ndarray) else ''
    )
    df['instructions_str'] = df['RecipeInstructions'].apply(
        lambda x: ' '.join(x) if isinstance(x, np.ndarray) else ''
    )
    # gonna take only first image link, don't want to deal with so many images with inconsistent count:")
    df['image_url'] = df['Images'].apply(
        lambda x: x[0] if isinstance(x, np.ndarray) and len(x) > 0 else None
    )
    df['keywords_str'] = df['Keywords'].apply(
        lambda x: ' '.join([i for i in x if i is not None]) if isinstance(x, np.ndarray) else ''
    )

    # combine all text for search (now includes keywords)
    df['search_text'] = (
        df['Name'] + ' ' +
        df['Description'] + ' ' +
        df['ingredients_str'] + ' ' +
        df['instructions_str'] + ' ' +
        df['keywords_str']
    )

    print("Cleaning text...")
    df['search_text_clean'] = df['search_text'].apply(preprocess)

    # keep only columns we need
    df_clean = df[[
        'RecipeId',
        'Name',
        'Description',
        'ingredients_str',
        'instructions_str',
        'keywords_str',
        'image_url',
        'RecipeCategory',
        'AggregatedRating',
        'ReviewCount',
        'search_text_clean'
    ]].copy()

    print(f"Finished cleaning. Lenght: {len(df_clean)}")
    return df_clean



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

def build_bm25(df_clean):
    print("\n[Building BM25 index...")
    tfidf_vectorizer = TfidfVectorizer(
        preprocessor=identity,
        ngram_range=(1, 2)
    )
    bm25 = BM25(tfidf_vectorizer)
    bm25.fit(df_clean['search_text_clean'])
    print("Saving bm25_index.pkl...")
    with open(config.BM25_INDEX_PATH, 'wb') as f:
        pickle.dump(bm25, f)
    print("    Done!")
    return bm25

# got this error without this...and fixed by claude :")
#  File "/Users/minthantko/Documents/cmu/cmu3_2/ir/food_bookmarking_recommendation_project/se481-backend/scripts/build_index.py", line 130, in build_bm25
#     pickle.dump(bm25, f)
# AttributeError: Can't pickle local object 'build_bm25.<locals>.<lambda>'
def identity(x):
    return x



def build_lda(df_clean):
    print("\nBuilding LDA model for recommendations...")
    count_vectorizer = CountVectorizer(
        ngram_range=(1, 1),
        max_features=5000
    )
    X_tf = count_vectorizer.fit_transform(df_clean['search_text_clean'])
    lda = LatentDirichletAllocation(
        n_components=config.LDA_TOPICS,
        random_state=0,
        n_jobs=-1
    )
    lda.fit(X_tf)

    print("Saving lda_model.pkl...")
    with open(config.LDA_MODEL_PATH, 'wb') as f:
        pickle.dump({
            'lda': lda,
            'vectorizer': count_vectorizer
        }, f)
    print("lda done")


if __name__ == "__main__":
    print("Preprocess and build index..")
    df = load_data()
    df_clean = prepare_recipes(df)

    print("\nSaving recipes_clean.parquet...")
    df_clean.to_parquet(config.RECIPES_CLEAN_PATH, index=False)
    print("    Saved!")

    bm25 = build_bm25(df_clean)
    build_lda(df_clean)

    print("\nFinished xD")