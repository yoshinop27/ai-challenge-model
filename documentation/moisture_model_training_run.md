# Moisture Model Training Run

**Date:** 2026-04-11  
**Model:** EfficientNet-B0 (fine-tuned)  
**Task:** Soil moisture classification — `dry / moderate / wet`  
**Final Val Accuracy:** 95.45%

---

## Dataset

| Source | Path |
|--------|------|
| Soil Moisture Dataset | `Soil_Moisture_Dataset/Before Augmentation/` |

| Class | Images |
|-------|--------|
| dry | 387 |
| moderate | 384 |
| wet | 406 |
| **Total** | **1,177** |

Train/val split: 85% / 15% (stratified random, seed 42)

---

## Training Configuration

| Hyperparameter | Value |
|----------------|-------|
| Base model | EfficientNet-B0 (ImageNet pretrained) |
| Optimizer | Adam |
| Loss | CrossEntropyLoss |
| Batch size | 32 |
| Initial LR (head only) | 1e-3 |
| Fine-tune LR (full network) | 1e-4 |
| Scheduler | CosineAnnealingLR |
| Epochs | 15 |
| Device | MPS (Apple Silicon) |

### Augmentation (train)
- RandomResizedCrop(224, scale=(0.7, 1.0))
- RandomHorizontalFlip
- RandomVerticalFlip
- ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2)
- ImageNet normalize

### Augmentation (val)
- Resize(256) → CenterCrop(224)
- ImageNet normalize

---

## Training Strategy

Two-phase fine-tuning:

1. **Epochs 1–5 — head only:** Backbone frozen, only the classifier head trained. Stabilizes the head before full fine-tuning.
2. **Epoch 6–15 — full fine-tuning:** Entire network unfrozen, LR reduced to 1e-4.

---

## Epoch Log

| Epoch | Train Loss | Val Accuracy | Best |
|-------|-----------|--------------|------|
| 01 | 0.9193 | 80.11% | ✓ |
| 02 | 0.7053 | 81.82% | ✓ |
| 03 | 0.6170 | 82.39% | ✓ |
| 04 | 0.6044 | 83.52% | ✓ |
| 05 | 0.5744 | 83.52% | — |
| 06 *(unfreeze)* | 0.4870 | 89.20% | ✓ |
| 07 | 0.3246 | 90.34% | ✓ |
| 08 | 0.2531 | 94.32% | ✓ |
| 09 | 0.2071 | 93.18% | — |
| 10 | 0.1947 | 93.75% | — |
| 11 | 0.1558 | 93.75% | — |
| 12 | 0.1371 | 94.32% | — |
| 13 | 0.1484 | 94.89% | ✓ |
| 14 | 0.1365 | **95.45%** | ✓ |
| 15 | 0.1138 | 95.45% | — |

Best checkpoint saved at epoch 14: `backend/moisture_model.pt`

---

## Integration

The trained model is loaded by `MoistureClassifier` in `backend/model.py` and combined with the existing soil condition model (`soil_model.pt`) via `DualClassifier`. Both classifiers run over a single decoded image tensor per request.

API response shape:
```json
{
  "soil":     { "label": "good",     "confidence": { "bad": 0.04, "average": 0.09, "good": 0.87 } },
  "moisture": { "label": "dry",      "confidence": { "dry": 0.71, "moderate": 0.18, "wet": 0.11 } },
  "recommendations": { ... }
}
```

The moisture label is passed to the LLM alongside the soil condition label for combined crop recommendations.

---

## Reproducing

```bash
backend/venv/bin/python train_moisture.py \
    --data "/path/to/Soil_Moisture_Dataset/Before Augmentation" \
    --out backend/moisture_model.pt \
    --epochs 15
```
