import os
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
from typing import List, Dict, Any

class AcademicRAG:
    """
    Local RAG Engine using ChromaDB.
    Indexes Turkish academic theses and performs semantic search.
    """
    
    def __init__(
        self,
        db_path: str = None,
        collection_name: str = "turkish_theses",
        embed_model: str = None,
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        if db_path is None:
            db_path = os.path.join(base_dir, "data", "chroma_db")

        if embed_model is None:
            # Default: well-tested multilingual model. trakad-embed-v1 is currently
            # paused (SimCSE collapse on first attempt — to be retrained in v2 with
            # hard negatives + larger batch).
            embed_model = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)

        print(f"[RAG] Loading embedding model: {embed_model} ...")
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embed_model)
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embed_fn
        )

    def index_corpus(self, parquet_path: str, batch_size: int = 500, limit: int = None):
        """Read derived parquet file and index into ChromaDB."""
        if not os.path.exists(parquet_path):
            raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
            
        print(f"[RAG] Reading dataset from {parquet_path}...")
        df = pd.read_parquet(parquet_path)
        
        # Filter rows with valid abstracts
        df = df[df['abstract_tr'].notna()]
        if limit is not None:
            df = df.head(limit)
        total = len(df)
        print(f"[RAG] Found {total} records with Turkish abstracts. Indexing...")
        
        # Convert to lists for batching
        ids = [str(t_id) for t_id in df['tez_no'].tolist()]
        documents = df['abstract_tr'].tolist()
        metadatas = []
        for _, row in df.iterrows():
            meta = {
                "title": str(row.get('title_tr', 'Unknown')),
                "author": str(row.get('author', 'Unknown')),
                "year": str(row.get('year', 'Unknown')),
                "subject": str(row.get('subject', 'Unknown'))
            }
            metadatas.append(meta)
            
        # Add in batches
        for i in range(0, total, batch_size):
            end_idx = min(i + batch_size, total)
            self.collection.upsert(
                ids=ids[i:end_idx],
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )
            print(f"[RAG] Indexed {end_idx}/{total} records...")
            
        print("[RAG] Indexing complete.")
        
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant thesis abstracts."""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        parsed_results = []
        if results['documents'] and len(results['documents']) > 0:
            docs = results['documents'][0]
            metas = results['metadatas'][0]
            for doc, meta in zip(docs, metas):
                parsed_results.append({
                    "text": doc,
                    "metadata": meta
                })
        return parsed_results

# CLI interface for indexing
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=str, help="Path to parquet file to index")
    parser.add_argument("--query", type=str, help="Query string to search")
    args = parser.parse_args()
    
    rag = AcademicRAG()
    
    if args.index:
        rag.index_corpus(args.index)
        
    if args.query:
        print(f"Searching for: {args.query}")
        results = rag.search(args.query)
        for i, res in enumerate(results):
            print(f"\n--- Result {i+1} ---")
            print(f"Title: {res['metadata']['title']}")
            print(f"Author: {res['metadata']['author']} ({res['metadata']['year']})")
            print(f"Abstract Snippet: {res['text'][:200]}...")
