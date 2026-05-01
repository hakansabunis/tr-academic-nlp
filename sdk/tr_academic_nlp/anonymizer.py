import re
import os
from typing import Dict, Tuple

class LocalAnonymizer:
    """
    KVKK Shield: Locally anonymizes sensitive entities (Person, Organization, Location)
    in Turkish text before sending it to external LLM APIs.
    """
    
    def __init__(self, model_name: str = "trakad-ner-v1", use_dummy: bool = False):
        self.model_name = model_name
        self.use_dummy = use_dummy
        self.ner_pipeline = None
        
        if not self.use_dummy:
            try:
                from transformers import pipeline
                
                if model_name == "trakad-ner-v1":
                    # Determine the absolute path to the locally trained model
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    actual_model = os.path.join(base_dir, "models", "ner", "trakad-ner-v1")
                    if not os.path.exists(actual_model):
                        print(f"Local model not found at {actual_model}. Falling back to savasy/bert-base-turkish-ner-cased")
                        actual_model = "savasy/bert-base-turkish-ner-cased"
                else:
                    actual_model = model_name
                    
                self.ner_pipeline = pipeline("ner", model=actual_model, aggregation_strategy="simple")
            except ImportError:
                print("Warning: transformers library not found. Falling back to regex-based dummy anonymization.")
                self.use_dummy = True

    def _dummy_ner(self, text: str):
        """A very basic regex-based fallback for demonstration/testing."""
        entities = []
        # Match capitalized words as potential entities (highly naive)
        for match in re.finditer(r'\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\b', text):
            entities.append({
                "entity_group": "YAZAR", # Assume Person for dummy
                "word": match.group(),
                "start": match.start(),
                "end": match.end()
            })
        return entities

    def anonymize(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Masks entities in text and returns the masked text along with a mapping dictionary
        for de-anonymization.
        """
        if self.use_dummy:
            entities = self._dummy_ner(text)
        else:
            entities = self.ner_pipeline(text)
            
        mapping = {}
        # Support the new custom entity categories of trakad-ner-v1
        counters = {"YAZAR": 1, "KURUM": 1, "YIL": 1, "METODOLOJI": 1, "DATASET": 1, "METRİK": 1, "DERGİ": 1, "MISC": 1}
        
        # Sort entities in reverse order to replace without messing up indices
        sorted_entities = sorted(entities, key=lambda x: x['start'], reverse=True)
        
        masked_text = text
        for ent in sorted_entities:
            group = ent.get("entity_group", "MISC")
            if group not in counters:
                group = "MISC"
                
            placeholder = f"[{group}_{counters[group]}]"
            mapping[placeholder] = ent["word"]
            counters[group] += 1
            
            # Replace in text
            masked_text = masked_text[:ent['start']] + placeholder + masked_text[ent['end']:]
            
        return masked_text, mapping

    def deanonymize(self, text: str, mapping: Dict[str, str]) -> str:
        """
        Restores the original entities into the masked text using the mapping dictionary.
        """
        restored_text = text
        for placeholder, original_word in mapping.items():
            restored_text = restored_text.replace(placeholder, original_word)
        return restored_text

# Example usage
if __name__ == "__main__":
    anonymizer = LocalAnonymizer(use_dummy=False)
    sample_text = "Prof. Dr. Ahmet Yılmaz 2024 yılında Hacettepe Üniversitesi Eğitim Bilimleri Bölümü'nde SPSS kullanarak bir çalışma yaptı."
    
    masked, mapping = anonymizer.anonymize(sample_text)
    print(f"Original: {sample_text}")
    print(f"Masked:   {masked}")
    print(f"Mapping:  {mapping}")
    
    restored = anonymizer.deanonymize(masked, mapping)
    print(f"Restored: {restored}")
