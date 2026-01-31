import torch
import torch.nn as nn
import torchvision.models as models


# -----------------------------
# Image Encoder
# -----------------------------
class ImageEncoder(nn.Module):
    def __init__(self, embed_dim=1024):
        super().__init__()
        backbone = models.efficientnet_b3(weights="IMAGENET1K_V1")
        self.features = backbone.features
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(1536, embed_dim)

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x).flatten(1)
        x = self.fc(x)
        return x


# -----------------------------
# Niceness Model
# -----------------------------
class NicenessModel(nn.Module):
    def __init__(self, embed_dim=1024):
        super().__init__()
        self.encoder = ImageEncoder(embed_dim)

        # AVA aesthetic head
        self.ava_head = nn.Sequential(
            nn.Linear(embed_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 1)
        )

        # Airbnb niceness head
        self.airbnb_head = nn.Sequential(
            nn.Linear(embed_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 1)
        )

    def forward_ava(self, images):
        emb = self.encoder(images)
        return self.ava_head(emb).squeeze(1)

    def forward_airbnb(self, images):
        """
        images: Tensor [N, C, H, W]
        """
        emb = self.encoder(images)               # [N, D]
        pooled = emb.mean(dim=0, keepdim=True)   # [1, D]
        return self.airbnb_head(pooled).squeeze(1)


# -----------------------------
# AVA Training
# -----------------------------
def train_ava_epoch(model, dataloader, optimizer, device):
    model.train()
    criterion = nn.HuberLoss()
    total_loss = 0.0

    for images, scores in dataloader:
        images = images.to(device)
        scores = scores.to(device)

        preds = model.forward_ava(images)
        loss = criterion(preds, scores)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(dataloader)


# -----------------------------
# Airbnb Pairwise Ranking Loss
# -----------------------------
def ranking_loss(score_a, score_b, margin=1.0):
    return torch.clamp(margin - (score_a - score_b), min=0)


# -----------------------------
# Airbnb Training
# -----------------------------
def train_airbnb_epoch(model, dataloader, optimizer, device):
    model.train()
    total_loss = 0.0

    for images_a, images_b in dataloader:
        images_a = images_a.to(device)
        images_b = images_b.to(device)

        score_a = model.forward_airbnb(images_a)
        score_b = model.forward_airbnb(images_b)

        loss = ranking_loss(score_a, score_b)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(dataloader)


# -----------------------------
# Freeze Encoder (before Airbnb fine-tuning)
# -----------------------------
def freeze_encoder(model):
    for param in model.encoder.parameters():
        param.requires_grad = False


# -----------------------------
# Inference Helper
# -----------------------------
@torch.no_grad()
def score_listing(model, images, device):
    """
    images: Tensor [N, C, H, W]
    """
    model.eval()
    images = images.to(device)
    score = model.forward_airbnb(images)
    return torch.sigmoid(score).item()


# -----------------------------
# Testing
# -----------------------------
if __name__ == "__main__":
    print("Testing NicenessModel...")
    
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Initialize model
    model = NicenessModel(embed_dim=1024)
    model = model.to(device)
    print("✓ Model initialized successfully")
    
    # Test with random data
    batch_size = 4
    test_images = torch.randn(batch_size, 3, 224, 224).to(device)
    print(f"✓ Created test batch: {test_images.shape}")
    
    # Test encoder
    print("\nTesting ImageEncoder...")
    embeddings = model.encoder(test_images)
    print(f"✓ Encoder output shape: {embeddings.shape}")
    assert embeddings.shape == (batch_size, 1024), "Encoder output shape mismatch"
    
    # Test AVA head
    print("\nTesting AVA head...")
    ava_scores = model.forward_ava(test_images)
    print(f"✓ AVA scores shape: {ava_scores.shape}")
    print(f"  AVA scores: {ava_scores.detach().cpu().numpy()}")
    assert ava_scores.shape == (batch_size,), "AVA output shape mismatch"
    
    # Test Airbnb head
    print("\nTesting Airbnb head...")
    airbnb_score = model.forward_airbnb(test_images)
    print(f"✓ Airbnb score shape: {airbnb_score.shape}")
    print(f"  Airbnb score: {airbnb_score.item():.4f}")
    assert airbnb_score.shape[0] == 1, "Airbnb output should be single value"
    
    # Test score_listing helper
    print("\nTesting score_listing helper...")
    final_score = score_listing(model, test_images, device)
    print(f"✓ Final listing score: {final_score:.4f}")
    assert 0 <= final_score <= 1, "Score should be between 0 and 1"
    
    # Test ranking loss
    print("\nTesting ranking loss...")
    images_a = torch.randn(3, 3, 224, 224).to(device)
    images_b = torch.randn(3, 3, 224, 224).to(device)
    score_a = model.forward_airbnb(images_a)
    score_b = model.forward_airbnb(images_b)
    loss = ranking_loss(score_a, score_b)
    print(f"✓ Ranking loss: {loss.item():.4f}")
    
    # Test freeze_encoder
    print("\nTesting freeze_encoder...")
    freeze_encoder(model)
    encoder_frozen = all(not p.requires_grad for p in model.encoder.parameters())
    heads_trainable = any(p.requires_grad for p in model.ava_head.parameters())
    print(f"✓ Encoder frozen: {encoder_frozen}")
    print(f"✓ Heads trainable: {heads_trainable}")
    assert encoder_frozen, "Encoder should be frozen"
    assert heads_trainable, "Heads should still be trainable"
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)