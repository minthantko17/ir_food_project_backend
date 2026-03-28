import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from search_engine import BM25, identity

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

# build raw vocab, for spell check for user's query
def build_vocab(df_clean):
    print("\nBuilding spell check vocabulary...")
    
    df_raw = pd.read_parquet(config.RECIPES_RAW_PATH)
    df_raw['Description'] = df_raw['Description'].fillna('')
    df_raw['keywords_str'] = df_raw['Keywords'].apply(
        lambda x: ' '.join([i for i in x if i is not None]) 
        if isinstance(x, np.ndarray) else ''
    )
    df_raw['ingredients_str'] = df_raw['RecipeIngredientParts'].apply(
        lambda x: ' '.join(x) if isinstance(x, np.ndarray) else ''
    )
    df_raw['instructions_str'] = df_raw['RecipeInstructions'].apply(
        lambda x: ' '.join(x) if isinstance(x, np.ndarray) else ''
    )

    df_raw['raw_text'] = (
        df_raw['Name'] + ' ' +
        df_raw['Description'] + ' ' +
        df_raw['ingredients_str'] + ' ' +
        df_raw['instructions_str'] + ' ' +
        df_raw['keywords_str']
    )

    def clean_only(text):   #stem not included here
        text = re.sub(r'[^A-Za-z]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip().lower()
        return text
    
    print("Building raw vocabulary...")
    raw_texts = df_raw['raw_text'].apply(clean_only).tolist()

    vectorizer = CountVectorizer(
        ngram_range=(1, 1),
        min_df=3
    )
    vectorizer.fit(raw_texts)
    matrix = vectorizer.transform(raw_texts)

    word_freq = pd.Series(
        np.asarray(matrix.sum(axis=0)).flatten(),
        index=vectorizer.get_feature_names_out()
    )
    total = word_freq.sum()

    print(f"Vocabulary size: {len(word_freq)} words")
    print("Saving vocab.pkl...")
    with open(config.VOCAB_PATH, 'wb') as f:
        pickle.dump({
            'word_freq': word_freq,
            'total'    : total
        }, f)
    print("Done!")

if __name__ == "__main__":
    print("Preprocess and build index..")
    print("\njust manual delete existing file to create new one, if already exists and wants to run again. Dx")

    #cleaning
    if config.RECIPES_CLEAN_PATH.exists():
        print("\nrecipes_clean.parquet already exists. skip :3")
        df_clean = pd.read_parquet(config.RECIPES_CLEAN_PATH)
        print(f"Loaded {len(df_clean)} recipes")
    else:
        df = load_data()
        df_clean = prepare_recipes(df)
        print("\n Saving recipes_clean.parquet...")
        df_clean.to_parquet(config.RECIPES_CLEAN_PATH, index=False)
        print("Saved!")

    # creat bm25 index
    if config.BM25_INDEX_PATH.exists():
        print("\nbm25_index.pkl already exists. skip :v")
    else:
        build_bm25(df_clean)

    # build lda
    if config.LDA_MODEL_PATH.exists():
        print("\nlda_model.pkl already exists. skip :P")
    else:
        build_lda(df_clean)

    # build vocab for spell check from query
    if config.VOCAB_PATH.exists():
        print("\nvocab.pkl already exists. skip xD")
    else:
        build_vocab(df_clean)

    print("\nFinished xD")