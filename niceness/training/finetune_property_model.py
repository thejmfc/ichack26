import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from modeltest import NicenessModel
import pandas as pd
from PIL import Image
from tqdm import tqdm
import numpy as np

# =====================
# Configuration
# =====================
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 4
LEARNING_RATE = 1e-5  # Lower LR for fine-tuning
EPOCHS = 20
RATINGS_CSV = "property_ratings.csv"
CHECKPOINT_PATH = "final_model.pth"
FALLBACK_CHECKPOINT_PATH = "checkpoints/best_model.pth"
FINETUNED_PATH = "checkpoints/property_model.pth"
os.makedirs("checkpoints", exist_ok=True)

print(f"Device: {DEVICE}")

# =====================
# Property Dataset
# =====================
class PropertyDataset(Dataset):
    def __init__(self, csv_file, transform=None):
        self.df = pd.read_csv(csv_file)
        self.transform = transform
        
        # Verify all images exist
        valid_samples = []
        for _, row in self.df.iterrows():
            if os.path.exists(row['image_path']):
                valid_samples.append(row)
        
        self.samples = pd.DataFrame(valid_samples)
        print(f"Loaded {len(self.samples)} valid property images")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        row = self.samples.iloc[idx]
        image_path = row['image_path']
        score = float(row['property_score'])
        
        try:
            image = Image.open(image_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            return image, torch.tensor(score, dtype=torch.float32)
        except Exception as e:
            print(f"Error loading {image_path}: {e}")
            return None, None

# =====================
# Data Augmentation
# =====================
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
])

# =====================
# Training Functions
# =====================
def train_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    pbar = tqdm(dataloader, desc="Training")
    for images, scores in pbar:
        if images is None:
            continue
        
        images = images.to(device)
        scores = scores.to(device)
        
        # Forward pass through AVA head for property scoring
        preds = model.forward_ava(images)
        loss = criterion(preds, scores)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
        pbar.set_postfix({"loss": f"{loss.item():.4f}"})
    
    return total_loss / max(num_batches, 1)

def validate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0.0
    num_batches = 0
    
    with torch.no_grad():
        for images, scores in tqdm(dataloader, desc="Validating"):
            if images is None:
                continue
            
            images = images.to(device)
            scores = scores.to(device)
            
            preds = model.forward_ava(images)
            loss = criterion(preds, scores)
            
            total_loss += loss.item()
            num_batches += 1
    
    return total_loss / max(num_batches, 1)

# =====================
# Main Fine-tuning Loop
# =====================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("Property Model Fine-tuning")
    print("="*70)
    
    # Check if ratings file exists
    if not os.path.exists(RATINGS_CSV):
        print(f"ERROR: {RATINGS_CSV} not found!")
        print("Please run 'python rate_properties.py' first")
        exit(1)
    
    # Load dataset
    print("\nLoading property ratings...")
    dataset = PropertyDataset(RATINGS_CSV, transform=train_transform)
    
    if len(dataset) == 0:
        print("ERROR: No valid property images found!")
        exit(1)
    
    # Split into train/val
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size]
    )
    
    # Use same transform for val but apply val_transform
    val_dataset.dataset.transform = val_transform
    
    # Create dataloaders
    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0
    )
    val_loader = DataLoader(
        val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0
    )
    
    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples: {len(val_dataset)}")
    
    # Load pre-trained model
    print("\nLoading pre-trained model...")
    model = NicenessModel(embed_dim=1024).to(DEVICE)
    
    if os.path.exists(CHECKPOINT_PATH):
        state_dict = torch.load(CHECKPOINT_PATH, map_location=DEVICE)
        model.load_state_dict(state_dict)
        print(f"Loaded weights from {CHECKPOINT_PATH}")
    elif os.path.exists(FALLBACK_CHECKPOINT_PATH):
        state_dict = torch.load(FALLBACK_CHECKPOINT_PATH, map_location=DEVICE)
        model.load_state_dict(state_dict)
        print(f"Loaded weights from {FALLBACK_CHECKPOINT_PATH}")
    else:
        print(
            "WARNING: No pretrained checkpoint found (final_model.pth or checkpoints/best_model.pth). "
            "Using random initialization"
        )
    
    # Optimizer and loss
    # Fine-tune only the AVA head and encoder's last layers
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss()
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    
    # Fine-tuning loop
    print("\nStarting fine-tuning...\n")
    best_val_loss = float('inf')
    patience_counter = 0
    
    for epoch in range(1, EPOCHS + 1):
        print(f"\nEpoch {epoch}/{EPOCHS}")
        
        train_loss = train_epoch(model, train_loader, optimizer, criterion, DEVICE)
        val_loss = validate(model, val_loader, criterion, DEVICE)
        scheduler.step()
        
        print(f"Train Loss: {train_loss:.4f}")
        print(f"Val Loss: {val_loss:.4f}")
        
        # Save checkpoint
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), FINETUNED_PATH)
            print(f"✓ Saved best property model to {FINETUNED_PATH}")
        else:
            patience_counter += 1
            print(f"No improvement for {patience_counter} epoch(s)")
        
        # Early stopping
        if patience_counter >= 3:
            print(f"\nEarly stopping triggered after {epoch} epochs")
            break
    
    print("\n" + "="*70)
    print("Fine-tuning complete!")
    print(f"Best model saved to: {FINETUNED_PATH}")
    print("="*70)
    print("\nNext step: Update view_airbnb.py to use the property model")
