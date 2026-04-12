import os
import io
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms, models

# Canonical label lists
LABELS = ["bad", "average", "good"]
MOISTURE_LABELS = ["dry", "moderate", "wet"]

_DEFAULT_WEIGHTS = os.path.join(os.path.dirname(__file__), "soil_model.pt")
_WEIGHTS_PATH = os.environ.get("SOIL_MODEL_WEIGHTS", _DEFAULT_WEIGHTS)

_DEFAULT_MOISTURE_WEIGHTS = os.path.join(os.path.dirname(__file__), "moisture_model.pt")
_MOISTURE_WEIGHTS_PATH = os.environ.get("MOISTURE_MODEL_WEIGHTS", _DEFAULT_MOISTURE_WEIGHTS)

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


class SoilClassifier:
    def __init__(self):
        self._model, self._labels = _load_efficientnet(_WEIGHTS_PATH)

    def forward_logits(self, image_bytes: bytes) -> torch.Tensor:
        tensor = _decode_image(image_bytes)
        with torch.no_grad():
            return self._model(tensor)

    def predict(self, image_bytes: bytes) -> dict:
        tensor = _decode_image(image_bytes)
        return _run(self._model, tensor, self._labels)


class MoistureClassifier:
    def __init__(self):
        self._model, self._labels = _load_efficientnet(_MOISTURE_WEIGHTS_PATH)

    def predict(self, image_bytes: bytes) -> dict:
        tensor = _decode_image(image_bytes)
        return _run(self._model, tensor, self._labels)


class DualClassifier:
    """Runs soil-type and moisture classifiers over a single decoded image tensor."""

    def __init__(self):
        self._type_model, self._type_labels = _load_efficientnet(_WEIGHTS_PATH)
        self._moisture_model, self._moisture_labels = _load_efficientnet(_MOISTURE_WEIGHTS_PATH)

    def predict(self, image_bytes: bytes) -> dict:
        tensor = _decode_image(image_bytes)
        soil = _run(self._type_model, tensor, self._type_labels)
        moisture = _run(self._moisture_model, tensor, self._moisture_labels)
        return {"soil": soil, "moisture": moisture}
