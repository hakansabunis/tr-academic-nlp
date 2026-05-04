"""Secure Academic Middleware Core (v3.0 — %100 yerel + ücretsiz).

Akış::

    raw text  ─►  Anonymizer (trakad-ner-v1, lokal)
              ─►  PromptEngine (Türkçe akademik system prompt)
              ─►  Ollama (qwen2.5:7b, lokal, ücretsiz)
              ─►  De-anonymizer (mapping üzerinden geri çözüm)
              ─►  user

Hiçbir veri makineden çıkmaz. RTX 3050 Ti 4GB GPU + 16GB RAM dostu.
"""
from typing import Optional, Tuple

import requests

from .anonymizer import LocalAnonymizer
from .prompts.system_prompts import get_prompt_for_task


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_LLM_MODEL = "qwen2.5:7b"


class AcademicPipeline:
    """Secure Academic Middleware Core.

    Orchestrates the flow:
        User Request -> Anonymizer -> Prompt Engine -> Local LLM (Ollama) -> De-anonymizer

    Default LLM is ``qwen2.5:7b`` running locally via Ollama. No API calls,
    no per-token billing, no data leaves the machine. RTX 3050 Ti 4GB GPU is
    sufficient (model runs in ~4.7GB with Ollama's auto GPU/CPU split).
    """

    def __init__(
        self,
        llm_model: str = DEFAULT_LLM_MODEL,
        ollama_url: str = DEFAULT_OLLAMA_URL,
        timeout: int = 180,
        anonymizer: Optional[LocalAnonymizer] = None,
        rag_engine = None,
    ):
        self.llm_model = llm_model
        self.ollama_url = ollama_url.rstrip("/")
        self.timeout = timeout
        self.anonymizer = anonymizer if anonymizer is not None else LocalAnonymizer(use_dummy=False)
        self.rag_engine = rag_engine

    def _ollama_health(self) -> bool:
        """Return True if the Ollama daemon is reachable."""
        try:
            requests.get(f"{self.ollama_url}/api/tags", timeout=5).raise_for_status()
            return True
        except requests.RequestException:
            return False

    def _call_local_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Run the prompt against the local Ollama daemon and return the text response.

        Replaces the original frontier-API call. If Ollama is not reachable,
        falls back to a clearly-marked mock so unit tests still work without
        the daemon running.
        """
        if not self._ollama_health():
            return (
                f"[MOCK {self.llm_model} RESPONSE — Ollama daemon ulaşılamadı] "
                f"Sistem prompt + masked text alındı (Ollama başlatın: `ollama serve`)."
            )

        payload = {
            "model": self.llm_model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()

    def analyze_and_rewrite(self, text: str, task: str = "summarize", rag_query: str = None) -> str:
        """Secure analysis loop: anonymize → RAG context → prompt → local LLM → de-anonymize."""
        # 1. Anonymize sensitive entities locally
        masked_text, mapping = self.anonymizer.anonymize(text)

        # 2. Add RAG Context if requested
        if rag_query and self.rag_engine:
            results = self.rag_engine.search(rag_query, top_k=2)
            context_str = "\n\n".join([f"KAYNAK ({r['metadata']['title']}): {r['text']}" for r in results])
            masked_text = f"Sorgu/Metin:\n{masked_text}\n\nYerel Veritabanı Bağlamı:\n{context_str}"

        # 3. Fetch the correct academic system prompt
        system_prompt = get_prompt_for_task(task)

        # 4. Call the local LLM (Ollama)
        llm_response = self._call_local_llm(system_prompt, masked_text)

        # 5. De-anonymize before returning to the user
        final_output = self.anonymizer.deanonymize(llm_response, mapping)

        return final_output

    def analyze_with_audit(self, text: str, task: str = "summarize") -> Tuple[str, dict]:
        """Like :meth:`analyze_and_rewrite` but also returns the masking
        mapping + masked LLM response for KVKK accountability / debugging."""
        masked_text, mapping = self.anonymizer.anonymize(text)
        system_prompt = get_prompt_for_task(task)
        llm_response_masked = self._call_local_llm(system_prompt, masked_text)
        final_output = self.anonymizer.deanonymize(llm_response_masked, mapping)
        return final_output, {
            "masked_text": masked_text,
            "mapping": mapping,
            "llm_response_masked": llm_response_masked,
            "task": task,
            "llm_model": self.llm_model,
        }


# Example usage
if __name__ == "__main__":
    pipeline = AcademicPipeline()
    text = "Prof. Dr. Ayşe Yılmaz'ın ODTÜ'de geliştirdiği model..."

    print("--- User Input ---")
    print(text)

    print("\n--- Pipeline Execution ---")
    result = pipeline.analyze_and_rewrite(text, task="summarize")

    print("\n--- Final Output ---")
    print(result)
