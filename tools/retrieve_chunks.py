import os
import pickle
import faiss
from sentence_transformers import SentenceTransformer

# =====================================================
# CONFIG
# =====================================================
BASE_DIR = "data"
FAISS_DIR = os.path.join(BASE_DIR, "faiss")

index_path = os.path.join(FAISS_DIR, "index.faiss")
meta_path = os.path.join(FAISS_DIR, "metadata.pkl")

# =====================================================
# LOAD FAISS INDEX AND METADATA
# =====================================================
if not os.path.exists(index_path) or not os.path.exists(meta_path):
    print(" FAISS index or metadata not found. Please run chunking_indexing.py first.")
    exit(1)

index = faiss.read_index(index_path)
metadata = pickle.load(open(meta_path, "rb"))

print(f" Loaded FAISS index with {index.ntotal} vectors")
print(f" Loaded {len(metadata)} metadata entries\n")

# =====================================================
# LOAD EMBEDDING MODEL
# =====================================================
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# =====================================================
# RETRIEVAL FUNCTION
# =====================================================
def retrieve_top_k(query, k=5):
    """
    Retrieve top-k most similar chunks for a given query.
    
    Args:
        query: Search query string
        k: Number of top results to return
    
    Returns:
        List of tuples (distance, metadata_dict)
    """
    # Embed the query
    query_embedding = embedder.encode([query], convert_to_numpy=True)
    
    # Search in FAISS index
    distances, indices = index.search(query_embedding, k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(metadata):
            results.append({
                'rank': i + 1,
                'distance': float(distances[0][i]),
                'similarity_score': 1 / (1 + distances[0][i]),  # Convert distance to similarity
                'file': metadata[idx]['file'],
                'chunk_id': metadata[idx]['chunk_id'],
                'text': metadata[idx]['text']
            })
    
    return results

# =====================================================
# MAIN QUERY
# =====================================================
if __name__ == "__main__":
    query = "how many blocks?"
    
    print(f"🔍 Query: '{query}'\n")
    print("=" * 80)
    
    results = retrieve_top_k(query, k=5)
    
    if not results:
        print(" No results found.")
    else:
        for result in results:
            print(f"\n📄 Rank {result['rank']}")
            print(f"   File: {result['file']}")
            print(f"   Chunk ID: {result['chunk_id']}")
            print(f"   Similarity Score: {result['similarity_score']:.4f}")
            print(f"   Distance: {result['distance']:.4f}")
            print(f"\n   Text Preview:")
            print(f"   {'-' * 76}")
            # Show first 500 characters of the chunk
            text_preview = result['text'][:500] + "..." if len(result['text']) > 500 else result['text']
            print(f"   {text_preview}")
            print(f"   {'-' * 76}")
    
    print("\n" + "=" * 80)
    print(f" Retrieved {len(results)} chunks successfully")
