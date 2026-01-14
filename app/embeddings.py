from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Global model
model = SentenceTransformer("all-MiniLM-L6-v2")

# In-memory storage for duplicates (list of dicts or embeddings)
# We store embeddings as a numpy array for speed if possible, but list is fine for small scale.
# Format: {'id': str, 'embedding': np.array}
known_embeddings = []

def get_embedding(text: str) -> np.ndarray:
    return model.encode([text])[0]

def check_duplicate(text: str, threshold: float = 0.90) -> bool:
    """
    Generate embedding for text and check against known_embeddings.
    If similarity > threshold, return True.
    Also adds the new embedding to the store if not duplicate? 
    The requirement says 'Flag as duplicate', not necessarily 'Prevent adding'.
    But usually we want to know if it IS a duplicate.
    """
    global known_embeddings
    
    new_emb = get_embedding(text)
    
    if not known_embeddings:
        known_embeddings.append(new_emb)
        return False
        
    # Stack known embeddings
    known_matrix = np.array(known_embeddings)
    
    # Calculate similarities
    sims = cosine_similarity([new_emb], known_matrix)[0]
    max_sim = np.max(sims)
    
    if max_sim > threshold:
        return True
    
    # If not duplicate, add to known (runtime cache)
    known_embeddings.append(new_emb)
    return False

def load_initial_embeddings(texts: list[str]):
    """
    Populate known_embeddings from DB texts on startup.
    """
    global known_embeddings
    if not texts:
        return
        
    print(f"⏳ Bulk embedding {len(texts)} existing resumes...")
    embeddings = model.encode(texts)
    known_embeddings = list(embeddings)
    print("✅ Embeddings loaded.")
