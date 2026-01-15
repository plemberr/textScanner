import joblib
import os
from typing import Dict
import sys

# MODEL_PATH = "../../data/doc3_classifier.pkl"

def resource_path(rel):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel)
    return os.path.abspath(rel)

MODEL_PATH = resource_path("data/doc3_classifier.pkl")


_pipeline = None

def _load_resources():
    global _pipeline
    if _pipeline is None:
        if os.path.exists(MODEL_PATH):
            _pipeline = joblib.load(MODEL_PATH)
        else:
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

_load_resources()

def classify_document(text: str) -> Dict:
    """
    Классификация документа только через ML.
    Возвращает словарь:
    {
      "label": str | None,
      "prob": float,       # вероятность (0..1) для ML
      "method": "ml"
    }
    """
    try:
        probs = _pipeline.predict_proba([text])[0]
        pred = _pipeline.predict([text])[0]
        classes = _pipeline.classes_
        prob = float(probs[list(classes).index(pred)])

        # Приводим первую букву к заглавной
        pred = pred.capitalize()

        return {"label": pred, "prob": prob, "method": "ml"}
    except Exception as e:
        return {"label": None, "prob": 0.0, "method": "unknown"}
