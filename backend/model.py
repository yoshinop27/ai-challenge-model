import os
import io
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms, models

# Default to soil_model.pt sitting next to this file
_DEFAULT_WEIGHTS = os.path.join(os.path.dirname(__file__), "soil_model.pt")
_WEIGHTS_PATH = os.environ.get("SOIL_MODEL_WEIGHTS", _DEFAULT_WEIGHTS)

_TRANSFORM = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


class SoilClassifier:
    def __init__(self):
        checkpoint = torch.load(_WEIGHTS_PATH, map_location="cpu")
        self._labels = checkpoint["classes"]

        self._model = models.efficientnet_b0(weights=None)
        self._model.classifier[1] = nn.Linear(
            self._model.classifier[1].in_features, len(self._labels)
        )
        self._model.load_state_dict(checkpoint["model_state"])
        self._model.eval()

    def forward_logits(self, image_bytes: bytes) -> torch.Tensor:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = _TRANSFORM(img).unsqueeze(0)
        with torch.no_grad():
            return self._model(tensor)

    def predict(self, image_bytes: bytes) -> dict:
        logits = self.forward_logits(image_bytes)
        probs = torch.softmax(logits, dim=1).squeeze(0)
        label_idx = int(probs.argmax())
        return {
            "label": self._labels[label_idx],
            "confidence": {label: round(float(probs[i]), 6) for i, label in enumerate(self._labels)},
        }
