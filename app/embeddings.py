# from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Global model - DISABLED for Virex Logic (and to fix timeout error)
# model = SentenceTransformer("all-MiniLM-L6-v2")

class DummyModel:
    def encode(self, texts):
        # Return dummy zero embeddings of shape (len(texts), 384)
        if isinstance(texts, str):
            texts = [texts]
        # 384 is typical BERT dim
        return np.zeros((len(texts), 384))

model = DummyModel()

# In-memory storage for duplicates (list of dicts or embeddings)
# We store embeddings as a numpy array for speed if possible, but list is fine for small scale.
# Format: {'id': str, 'embedding': np.array}
_known_embeddings = []
_embeddings_loaded = False

def get_known_embeddings():
    global _embeddings_loaded, _known_embeddings
    if not _embeddings_loaded:
        _load_embeddings_lazy()
    return _known_embeddings

def _load_embeddings_lazy():
    global _embeddings_loaded, _known_embeddings
    # Avoid circular imports
    from app.db import get_leaderboard
    
    # print("⏳ Lazy loading embeddings...")
    candidates = get_leaderboard()
    texts = [c['resume_text'] for c in candidates if c.get('resume_text')]
    
    if texts:
        embeddings = model.encode(texts)
        _known_embeddings = list(embeddings)
    
    _embeddings_loaded = True
    # print("✅ Embeddings loaded.")

def get_embedding(text: str) -> np.ndarray:
    return model.encode([text])[0]

def check_duplicate(text: str, threshold: float = 0.90) -> bool:
    """
    Generate embedding for text and check against known_embeddings.
    If similarity > threshold, return True.
    """
    known = get_known_embeddings()
    
    new_emb = get_embedding(text)
    
    if not known:
        known.append(new_emb)
        return False
        
    # Stack known embeddings
    known_matrix = np.array(known)
    
    # Calculate similarities
    sims = cosine_similarity([new_emb], known_matrix)[0]
    max_sim = np.max(sims)
    
    if max_sim > threshold:
        return True
    
    # If not duplicate, add to known (runtime cache)
    known.append(new_emb)
    return False

# Legacy function kept for compatibility but no-op or redirects
def load_initial_embeddings(texts: list[str]):
    pass

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple cosine similarity between two texts.
    Returns float 0-100.
    """
    if not text1 or not text2:
        return 0.0
        
    emb1 = get_embedding(text1)
    emb2 = get_embedding(text2)
    
    # Reshape for sklearn
    sim = cosine_similarity([emb1], [emb2])[0][0]
    return round(float(sim) * 100, 2)
