"""
FINRES ML Pipeline Runner.
Executes the full training pipeline and saves model artifacts.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src_py.ai.trainer import train_all_models
from src_py.ai.registry import get_registry, get_all_models


def main():
    print("Starting FINRES ML Training Pipeline with real-world data...\n")

    meta = train_all_models()

    print("\n" + "=" * 60)
    print("Verifying loaded models...")
    print("=" * 60)

    registry = get_registry()
    models = get_all_models()

    for m in models:
        print(f"  {m['name']}: AUC={m['auc']:.3f}, F1={m['f1']:.3f}, Status={m['status']}")

    print(f"\nBest model: {meta['best_model']}")
    print(f"Artifacts saved to: {os.path.join(os.path.dirname(__file__), 'model_artifacts')}")
    print("Pipeline complete!")


if __name__ == "__main__":
    main()
