import pickle
import re
import config
from nltk.stem import PorterStemmer

word_freq = None
total = None
vocabulary = None
ps = PorterStemmer()

#check with raw vocabs (not stemmed)
def load_spell_checker():
    global word_freq, total, vocabulary

    if not config.VOCAB_PATH.exists():
        print("vocab.pkl not found!")
        print("Please run python scripts/build_index.py")
        return False

    print("Loading spell checker...")
    with open(config.VOCAB_PATH, 'rb') as f:
        saved = pickle.load(f)

    word_freq = saved['word_freq']
    total = saved['total']
    vocabulary = set(word_freq.index)

    print(f"  Vocabulary: {len(vocabulary)} words")
    return True


def p_word(word):
    """
    P(w) = frequency / total
    """
    if word_freq is None or word not in word_freq:
        return 0
    return float(word_freq[word]) / float(total)


def edit_distance_1(word):
    """
    Generate all strings within edit distance 1.
    """
    letters = 'abcdefghijklmnopqrstuvwxyz'
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    inserts = [L + c + R for L, R in splits for c in letters]
    replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    return set(deletes + inserts + replaces + transposes)


def edit_distance_2(word):
    """Generate all strings within edit distance 2"""
    return set(
        e2 for e1 in edit_distance_1(word)
           for e2 in edit_distance_1(e1)
    )


def get_candidates(word):
    """
    Find valid correction candidates.
    Try ed1 first, fall back to ed2.
    """
    if word in vocabulary:
        return [word]

    candidates = edit_distance_1(word) & vocabulary
    if candidates:
        return list(candidates)

    candidates = edit_distance_2(word) & vocabulary
    if candidates:
        return list(candidates)

    return [word]


def best_candidate(candidates):
    """
    Pick best candidate by P(w).
    """
    return max(candidates, key=lambda w: p_word(w))


def correct_query(query):
    """
    Step 1: spell check raw query against raw vocabulary
    Step 2: stem corrected query for BM25 search
    Returns original, corrected, and stemmed version
    """
    if word_freq is None:
        stemmed = ' '.join([ps.stem(w) for w in query.lower().split()])
        return {
            'original': query,
            'corrected': query,
            'has_correction': False,
            'corrections': {},
            'search_query': stemmed
        }

    words = query.lower().split()
    corrections = {}
    new_words = []

    for word in words:
        # only check words longer than 2 characters
        if len(word) <= 2:
            new_words.append(word)
            continue

        candidates = get_candidates(word)
        best = best_candidate(candidates)
        new_words.append(best)

        if best != word:
            corrections[word] = best

    corrected_query = ' '.join(new_words)

    # stem corrected query for BM25
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    stop_words = set(stopwords.words('english'))

    tokens = word_tokenize(corrected_query)
    tokens = [w for w in tokens if w not in stop_words and len(w) > 2]
    tokens = [ps.stem(w) for w in tokens]
    search_query = ' '.join(tokens)

    return {
        'original': query,
        'corrected': corrected_query,
        'has_correction': len(corrections) > 0,
        'corrections': corrections,
        'search_query': search_query  # stemmed
    }