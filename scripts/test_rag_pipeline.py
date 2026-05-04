import sys
import os

# Ensure the root of the project is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sdk.tr_academic_nlp.rag import AcademicRAG
from sdk.tr_academic_nlp.pipeline import AcademicPipeline

def run_smoke_test():
    print("=== RAG Smoke Test Başlıyor ===")
    
    # 1. Initialize RAG Engine
    print("\n1. RAG Motoru Başlatılıyor...")
    rag = AcademicRAG(
        collection_name="smoke_test_collection",
        embed_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    
    parquet_path = "data/corpora/full/data.parquet"
    print(f"\n2. Sadece 500 Tez İndeksleniyor... ({parquet_path})")
    
    # Check if there is already data in the collection
    count = rag.collection.count()
    if count < 500:
        try:
            rag.index_corpus(parquet_path, batch_size=100, limit=500)
        except Exception as e:
            print(f"Hata oluştu: Veri seti bulunamadı veya okunamadı. Detay: {e}")
            return
    else:
        print(f"Koleksiyonda zaten {count} kayıt var, indeksleme atlanıyor.")
        
    print("\n3. Pipeline (RAG + Anonymizer + Ollama) Başlatılıyor...")
    pipeline = AcademicPipeline(rag_engine=rag, timeout=120)
    
    # 4. Run End-to-End Query
    query = "Piyano eğitiminin öğrenciler üzerindeki etkileri nelerdir?"
    print(f"\n[Kullanıcı Sorusu]: {query}")
    
    print("\n[İşleniyor] Lütfen bekleyin (Ollama'ya istek atılıyor)...")
    try:
        # We pass the query both as text (to summarize/answer) and as rag_query (to search db)
        result = pipeline.analyze_and_rewrite(text=query, task="qa", rag_query=query)
        print("\n=== Ollama (Qwen2.5:7b) Yanıtı ===")
        print(result)
        print("==================================")
    except Exception as e:
        print(f"Hata oluştu: Ollama'ya ulaşılamadı veya pipeline patladı. Detay: {e}")

if __name__ == "__main__":
    run_smoke_test()
