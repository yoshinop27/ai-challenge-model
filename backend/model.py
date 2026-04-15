import os
import io
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms, models

_WEIGHTS_PATH = os.environ.get(
    "SOIL_MODEL_WEIGHTS", os.path.join(os.path.dirname(__file__), "soil_model.pt")
)
_MOISTURE_WEIGHTS_PATH = os.environ.get(
    "MOISTURE_MODEL_WEIGHTS", os.path.join(os.path.dirname(__file__), "moisture_model.pt")
)

_TRANSFORM = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def _load_efficientnet(weights_path: str) -> tuple[nn.Module, list[str]]:
    checkpoint = torch.load(weights_path, map_location="cpu")
    labels = checkpoint["classes"]
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(labels))
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model, labels


def _decode_image(image_bytes: bytes) -> torch.Tensor:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return _TRANSFORM(img).unsqueeze(0)


def _run(model: nn.Module, tensor: torch.Tensor, labels: list[str]) -> dict:
    with torch.no_grad():
        logits = model(tensor)
    probs = torch.softmax(logits, dim=1).squeeze(0)
    label_idx = int(probs.argmax())
    return {
        "label": labels[label_idx],
        "confidence": {label: round(float(probs[i]), 6) for i, label in enumerate(labels)},
    }


class DualClassifier:
    def __init__(self):
        self._soil = _load_efficientnet(_WEIGHTS_PATH)
        self._moisture = _load_efficientnet(_MOISTURE_WEIGHTS_PATH)

    def predict(self, image_bytes: bytes) -> dict:
        tensor = _decode_image(image_bytes)
        soil_model, soil_labels = self._soil
        moist_model, moist_labels = self._moisture
        return {
            "soil": _run(soil_model, tensor, soil_labels),
            "moisture": _run(moist_model, tensor, moist_labels),
        }
