# Azerbaijani TTS Training Guide

Train a VITS model on your Azerbaijani ASR dataset to produce natural-sounding speech from text.

---

## Infrastructure

**GPU:** A100 40GB or 80GB  
**Where:** RunPod or Lambda Labs (~$1.50-2/hr)  
**Time estimate:** 2-4 days of training for decent quality, up to a week for polished results  
**Storage:** ~100GB (40GB dataset + preprocessed files + checkpoints)

---

## Step 1: Data Preparation

Your dataset is ASR format, so you need to flip it for TTS.

**What you have:**
```
audio file → transcript
```

**What you need (LJSpeech-style):**
```
metadata.csv:
wav_filename|transcript|transcript
audio_001.wav|Salam dünya|Salam dünya
audio_002.wav|Necəsən|Necəsən
```

**Audio requirements:**
- Sample rate: 22050 Hz (resample if different)
- Format: WAV, mono
- Trim silence from start/end
- Normalize loudness to -23 LUFS (optional but helps)

**Script to convert your HF dataset:**

```python
from datasets import load_dataset
import soundfile as sf
import librosa
import os
from tqdm import tqdm

ds = load_dataset("LocalDoc/azerbaijani_asr", split="train")

os.makedirs("wavs", exist_ok=True)
metadata = []

for i, sample in enumerate(tqdm(ds)):
    audio = sample["audio"]["array"]
    sr = sample["audio"]["sampling_rate"]
    text = sample["sentence"].strip()
    
    # skip bad samples
    if len(text) < 2 or len(audio) < sr * 0.5:  # less than 0.5s
        continue
    
    # resample to 22050
    if sr != 22050:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=22050)
    
    filename = f"audio_{i:06d}.wav"
    sf.write(f"wavs/{filename}", audio, 22050)
    metadata.append(f"{filename}|{text}|{text}")

with open("metadata.csv", "w", encoding="utf-8") as f:
    f.write("\n".join(metadata))

print(f"Processed {len(metadata)} samples")
```

**Data filtering (important):**

ASR datasets are messy. Filter out:
- Very short clips (<0.5s) — not enough to learn from
- Very long clips (>15s) — memory issues during training
- Clips with music/noise/multiple speakers if possible

If your dataset has speaker IDs, consider training single-speaker first (cleaner) or multi-speaker with speaker embeddings.

---

## Step 2: Environment Setup

```bash
# On your GPU instance
git clone https://github.com/coqui-ai/TTS
cd TTS
pip install -e .

# Dependencies for audio processing
pip install librosa soundfile tqdm datasets
```

---

## Step 3: Configure VITS Training

Create a config file `config_az.json`:

```json
{
    "run_name": "vits-azerbaijani",
    "run_description": "VITS trained on Azerbaijani speech",
    
    "audio": {
        "sample_rate": 22050,
        "win_length": 1024,
        "hop_length": 256,
        "num_mels": 80,
        "mel_fmin": 0,
        "mel_fmax": null
    },
    
    "model": "vits",
    "batch_size": 32,
    "eval_batch_size": 8,
    "num_loader_workers": 4,
    "num_eval_loader_workers": 2,
    "run_eval": true,
    "test_delay_epochs": 10,
    "epochs": 1000,
    "save_step": 5000,
    "print_step": 100,
    "mixed_precision": true,
    
    "text_cleaner": "basic_cleaners",
    "use_phonemes": false,
    "characters": {
        "characters": "abcçdeəfgğhxıijkqlmnoöprsştuüvyzABCÇDEƏFGĞHXIİJKQLMNOÖPRSŞTUÜVYZ",
        "punctuations": "!\"'(),-.:;? ",
        "pad": "<PAD>",
        "eos": "<EOS>",
        "bos": "<BOS>",
        "blank": "<BLANK>"
    },
    
    "datasets": [
        {
            "name": "azerbaijani",
            "path": "/path/to/your/data/",
            "meta_file_train": "metadata.csv",
            "meta_file_val": "metadata_val.csv"
        }
    ]
}
```

**Key decisions:**

- `use_phonemes: false` — Using characters directly. Azerbaijani Latin is phonetic enough that this works. Avoids G2P headaches.
- `characters` — Includes Azerbaijani-specific letters (ə, ğ, ı, ö, ü, ş, ç). Double-check this covers your dataset.
- `batch_size: 32` — Adjust based on GPU memory. A100 40GB should handle 32, maybe 48.
- `mixed_precision: true` — Faster training, less memory.

---

## Step 4: Split Train/Val

```python
import random

with open("metadata.csv", "r", encoding="utf-8") as f:
    lines = f.readlines()

random.shuffle(lines)
split = int(len(lines) * 0.95)

with open("metadata_train.csv", "w", encoding="utf-8") as f:
    f.writelines(lines[:split])

with open("metadata_val.csv", "w", encoding="utf-8") as f:
    f.writelines(lines[split:])
```

---

## Step 5: Train

```bash
python TTS/bin/train_tts.py --config_path config_az.json
```

**What to monitor:**

- Loss should decrease steadily
- After ~50k steps, start listening to validation samples
- Checkpoints saved every 5000 steps

**If it crashes:**

- OOM → reduce batch_size
- NaN losses → check for bad audio files (corrupt, silent, or weird sample rates)
- Slow → make sure you're on GPU (`nvidia-smi` to verify)

---

## Step 6: Inference

Once trained:

```python
from TTS.api import TTS

tts = TTS(model_path="path/to/checkpoint.pth", 
          config_path="config_az.json")

tts.tts_to_file(text="Salam, mənim adım Claude.", 
                file_path="output.wav")
```

---

## Step 7: Iterate and Improve

**If quality is mediocre after first training:**

1. **Data cleaning** — Listen to random samples, remove bad ones
2. **Longer training** — VITS keeps improving up to ~500k-1M steps
3. **Try phonemes** — If character-based hits a ceiling, add espeak-ng Azerbaijani phonemization
4. **Fine-tune hyperparameters** — Learning rate, batch size

**Troubleshooting:**

| Problem | Fix |
|---------|-----|
| Mispronunciations | Add phoneme input or text normalization rules |
| Robotic sound | More training, check data quality |
| Skipping/repeating words | Usually data issue — misaligned transcripts |
| One speaker sounds bad | Filter to best speaker or add speaker embeddings |

---

## Directory Structure

```
project/
├── wavs/
│   ├── audio_000001.wav
│   ├── audio_000002.wav
│   └── ...
├── metadata_train.csv
├── metadata_val.csv
├── config_az.json
└── outputs/
    └── vits-azerbaijani/
        ├── checkpoint_50000.pth
        └── ...
```

---

## Timeline Estimate

| Phase | Time |
|-------|------|
| Data download + preprocessing | 2-4 hours |
| Environment setup | 30 min |
| Training to "sounds like speech" | 12-24 hours |
| Training to "actually good" | 2-4 days |
| Fine-tuning and iteration | Ongoing |

---

## Budget

- A100 for 4 days: ~$150-200
- If tight on budget: Use A40 or RTX 4090, slower but works
