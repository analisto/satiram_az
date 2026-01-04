"""Deep analysis of synthesis pipeline"""
import torch
import pickle
import numpy as np
from app.model import SimpleTTS, synthesize_speech, CharacterEncoder
from pathlib import Path
import matplotlib.pyplot as plt

# Load model
BASE_DIR = Path(__file__).parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
device = torch.device('cpu')

# Load encoder
import sys
import app.model
sys.modules['__main__'].CharacterEncoder = CharacterEncoder

with open(ARTIFACTS_DIR / "char_encoder.pkl", 'rb') as f:
    char_encoder = pickle.load(f)

# Load model
model = SimpleTTS(vocab_size=char_encoder.vocab_size, n_mels=80)
checkpoint = torch.load(ARTIFACTS_DIR / "best_model.pt", map_location=device)
model.load_state_dict(checkpoint['model_state_dict'])
model.to(device)
model.eval()

# Test with different inputs
test_texts = [
    "Salam",
    "Necəsən",
    "Bu gözəl bir gündür"
]

print("=" * 80)
print("TESTING IF MODEL PRODUCES DIFFERENT OUTPUTS FOR DIFFERENT INPUTS")
print("=" * 80)

mels = []
for text in test_texts:
    mel = synthesize_speech(text, model, char_encoder, device, max_len=150)
    mels.append(mel)

    print(f"\nText: '{text}'")
    print(f"  Shape: {mel.shape}")
    print(f"  Min: {mel.min():.4f}, Max: {mel.max():.4f}")
    print(f"  Mean: {mel.mean():.4f}, Std: {mel.std():.4f}")
    print(f"  First 5 values of first channel: {mel[0, :5]}")

# Compare spectrograms
print("\n" + "=" * 80)
print("COMPARING SPECTROGRAMS")
print("=" * 80)

for i in range(len(mels)):
    for j in range(i+1, len(mels)):
        diff = np.abs(mels[i][:, :min(mels[i].shape[1], mels[j].shape[1])] -
                     mels[j][:, :min(mels[i].shape[1], mels[j].shape[1])])
        print(f"\nDifference between '{test_texts[i]}' and '{test_texts[j]}':")
        print(f"  Mean absolute difference: {diff.mean():.4f}")
        print(f"  Max absolute difference: {diff.max():.4f}")
        print(f"  Are they identical? {np.allclose(mels[i][:, :min(mels[i].shape[1], mels[j].shape[1])], mels[j][:, :min(mels[i].shape[1], mels[j].shape[1])], atol=0.001)}")

# Visualize
fig, axes = plt.subplots(len(test_texts), 1, figsize=(12, 4*len(test_texts)))
for i, (mel, text) in enumerate(zip(mels, test_texts)):
    ax = axes[i] if len(test_texts) > 1 else axes
    im = ax.imshow(mel, aspect='auto', origin='lower', cmap='viridis')
    ax.set_title(f"'{text}' - Shape: {mel.shape}")
    ax.set_xlabel('Time Frames')
    ax.set_ylabel('Mel Bands')
    plt.colorbar(im, ax=ax)

plt.tight_layout()
plt.savefig('debug_spectrograms.png', dpi=150)
print(f"\n✓ Saved visualization to debug_spectrograms.png")

# Check if model is stuck
print("\n" + "=" * 80)
print("CHECKING MODEL WEIGHTS")
print("=" * 80)
print(f"Total parameters: {sum(p.numel() for p in model.parameters()):,}")
print(f"Trainable parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

# Check if weights are reasonable
for name, param in model.named_parameters():
    if 'weight' in name:
        print(f"\n{name}:")
        print(f"  Mean: {param.data.mean():.6f}, Std: {param.data.std():.6f}")
        print(f"  Min: {param.data.min():.6f}, Max: {param.data.max():.6f}")
