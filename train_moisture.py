"""
Train EfficientNet-B0 moisture classifier on the Soil_Moisture_Dataset.

Usage:
    python train_moisture.py \
        --data "/path/to/Soil_Moisture_Dataset/Before Augmentation" \
        --out backend/moisture_model.pt \
        --epochs 15
"""
import argparse
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, models, transforms

CLASSES = ["dry", "moderate", "wet"]

TRAIN_TRANSFORM = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

VAL_TRANSFORM = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def build_model(num_classes: int) -> nn.Module:
    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to Before Augmentation folder")
    parser.add_argument("--out", default="backend/moisture_model.pt")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--val-split", type=float, default=0.15)
    args = parser.parse_args()

    device = (
        "mps" if torch.backends.mps.is_available()
        else "cuda" if torch.cuda.is_available()
        else "cpu"
    )
    print(f"Using device: {device}")

    full_dataset = datasets.ImageFolder(args.data, transform=TRAIN_TRANSFORM)
    # Verify class order matches CLASSES
    detected = [c.lower() for c in full_dataset.classes]
    for c in CLASSES:
        if c not in detected:
            raise ValueError(f"Expected class '{c}' not found. Found: {full_dataset.classes}")

    # Remap class_to_idx to enforce our canonical order
    full_dataset.class_to_idx = {c: i for i, c in enumerate(full_dataset.classes)}
    full_dataset.samples = [
        (path, full_dataset.class_to_idx[full_dataset.classes[label]])
        for path, label in full_dataset.samples
    ]

    n_val = int(len(full_dataset) * args.val_split)
    n_train = len(full_dataset) - n_val
    train_set, val_set = random_split(
        full_dataset, [n_train, n_val], generator=torch.Generator().manual_seed(42)
    )
    # Val set uses val transform
    val_set.dataset = datasets.ImageFolder(args.data, transform=VAL_TRANSFORM)
    val_set.dataset.class_to_idx = full_dataset.class_to_idx
    val_set.dataset.samples = full_dataset.samples

    train_loader = DataLoader(train_set, batch_size=args.batch, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_set, batch_size=args.batch, shuffle=False, num_workers=4)

    model = build_model(len(CLASSES)).to(device)

    # Freeze backbone, only train classifier head first
    for param in model.features.parameters():
        param.requires_grad = False

    optimizer = torch.optim.Adam(model.classifier.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val_acc = 0.0

    for epoch in range(1, args.epochs + 1):
        # Unfreeze backbone after epoch 5
        if epoch == 6:
            for param in model.features.parameters():
                param.requires_grad = True
            optimizer = torch.optim.Adam(model.parameters(), lr=args.lr / 10)
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer, T_max=args.epochs - epoch + 1
            )
            print("Unfreezing backbone for fine-tuning")

        model.train()
        train_loss, train_correct = 0.0, 0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(imgs), labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * imgs.size(0)
            train_correct += (model(imgs).argmax(1) == labels).sum().item()

        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                preds = model(imgs).argmax(1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

        val_acc = val_correct / val_total
        print(
            f"Epoch {epoch:02d}/{args.epochs}  "
            f"loss={train_loss/n_train:.4f}  "
            f"val_acc={val_acc:.4f}"
        )
        scheduler.step()

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({"classes": list(full_dataset.classes), "model_state": model.state_dict()}, args.out)
            print(f"  Saved best model (val_acc={val_acc:.4f}) → {args.out}")

    print(f"\nDone. Best val accuracy: {best_val_acc:.4f}")
    print(f"Model saved to: {args.out}")


if __name__ == "__main__":
    main()
