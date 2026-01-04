# Azerbaijani TTS Web Application

## 🎯 Project Overview

A production-ready web application for Azerbaijani text-to-speech synthesis featuring:
- **FastAPI Backend** with async endpoints
- **Modern UI** with Jinja2 templates and professional CSS design
- **Docker Support** for easy deployment
- **7.2M Parameter Model** optimized for CPU inference

## 🚀 Quick Start

### Option 1: Local Development (Fastest)

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Open in browser
open http://localhost:8000
```

### Option 2: Docker (Production)

```bash
# 1. Build and start
docker-compose up -d --build

# 2. View logs
docker-compose logs -f tts-app

# 3. Open in browser
open http://localhost:8000

# 4. Stop
docker-compose down
```

## 📁 Project Structure

```
text_to_speech/
├── app/
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application
│   ├── model.py                 # TTS model & inference
│   ├── templates/
│   │   └── index.html           # Frontend UI
│   └── static/
│       ├── css/style.css        # Professional styling
│       └── js/app.js            # Frontend logic
├── artifacts/
│   ├── best_model.pt            # Trained model (82MB) - NOT in git
│   ├── final_model.pt           # Final model (82MB) - NOT in git
│   └── char_encoder.pkl         # Character encoder
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Docker orchestration
├── DEPLOYMENT.md                 # Deployment guide
└── requirements.txt              # Dependencies
```

## ⚙️ Configuration

### Environment Variables

```bash
# Optional
export LOG_LEVEL=info
export HOST=0.0.0.0
export PORT=8000
```

### Model Files

**IMPORTANT**: Model files are large (82MB each) and NOT tracked in git:
- `artifacts/best_model.pt` (excluded)
- `artifacts/final_model.pt` (excluded)
- `artifacts/char_encoder.pkl` (tracked - only 1.4KB)

#### Option A: Download from Training

If you trained the model locally, the files are already in `artifacts/`.

#### Option B: Use Git LFS (if sharing via git)

```bash
# Install Git LFS
brew install git-lfs  # macOS
# or
apt-get install git-lfs  # Ubuntu

# Initialize
git lfs install

# Track large files
git lfs track "artifacts/*.pt"

# Add and commit
git add .gitattributes artifacts/best_model.pt
git commit -m "Add model files via LFS"
git push
```

#### Option C: External Storage

Upload to cloud storage (S3, Google Drive, etc.) and download manually:

```bash
# Download to artifacts directory
cd artifacts/
curl -L "YOUR_MODEL_URL" -o best_model.pt
```

## 🔌 API Endpoints

### Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "model_loaded": true,
  "vocab_size": 124
}
```

### Text Synthesis (JSON)
```bash
POST /api/synthesize
Content-Type: application/json

{
  "text": "Salam, necəsən?",
  "max_length": 300
}

Response:
{
  "success": true,
  "message": "Synthesis completed successfully",
  "mel_shape": [80, 300]
}
```

### Synthesis with Image
```bash
POST /api/synthesize/image
Content-Type: application/json

{
  "text": "Mən Python dilini öyrənirəm",
  "max_length": 300
}

Response: PNG image (mel spectrogram)
```

### Model Statistics
```bash
GET /api/stats

Response:
{
  "model_architecture": "Seq2Seq with Attention",
  "total_parameters": 7200209,
  "vocab_size": 124,
  "n_mels": 80,
  "device": "cpu"
}
```

## 🧪 Testing

### Manual Testing

```bash
# Health check
curl http://localhost:8000/health | jq

# Synthesis (using file for complex characters)
echo '{"text": "Salam, necəsən?", "max_length": 150}' > /tmp/test.json
curl -X POST http://localhost:8000/api/synthesize \
  -H "Content-Type: application/json" \
  -d @/tmp/test.json | jq

# Image generation
curl -X POST http://localhost:8000/api/synthesize/image \
  -H "Content-Type: application/json" \
  -d @/tmp/test.json \
  --output test_output.png
```

### Frontend Testing

1. Open `http://localhost:8000` in browser
2. Enter Azerbaijani text: "Salam, mən Python dilini öyrənirəm."
3. Click "Synthesize Speech"
4. View generated mel spectrogram

## 🐳 Docker Details

### Build Custom Image

```bash
docker build -t azerbaijani-tts:latest .
```

### Run with Custom Config

```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/artifacts:/app/artifacts:ro \
  -e LOG_LEVEL=debug \
  --name azerbaijani-tts \
  azerbaijani-tts:latest
```

### Multi-stage Build Benefits

- **Builder stage**: Compiles dependencies
- **Production stage**: Minimal runtime image
- **Security**: Runs as non-root user
- **Size**: Optimized layer caching

## 🚨 Troubleshooting

### Issue: Model not loading

```bash
# Check if model files exist
ls -lh artifacts/
# Should show:
#   best_model.pt (82MB)
#   char_encoder.pkl (1.4KB)

# If missing, see "Model Files" section above
```

### Issue: Port 8000 already in use

```bash
# Option 1: Use different port
uvicorn app.main:app --port 8001

# Option 2: Kill existing process
lsof -ti:8000 | xargs kill -9
```

### Issue: Import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or use fresh virtual environment
python -m venv venv_new
source venv_new/bin/activate
pip install -r requirements.txt
```

### Issue: Git push timeout (large files)

```bash
# Remove large files from git
git rm --cached artifacts/*.pt

# Update .gitignore (already done)
# Commit changes
git add .gitignore
git commit -m "Exclude large model files"
git push

# Use Git LFS or external storage for model files
```

### Issue: Shell errors (rbenv, google-cloud-sdk)

The errors:
```
/Users/ismatsamadov/.zprofile:10: command not found: rbenv
/Users/ismatsamadov/.zshrc:source:25: no such file or directory: /Users/ismatsamadov/google-cloud-sdk/path.zsh.inc
```

These are just **warnings** - they won't affect the TTS app. To fix:

**Option 1: Comment them out**
```bash
# Edit .zprofile
code ~/.zprofile
# Comment out line 10 (rbenv)

# Edit .zshrc
code ~/.zshrc
# Comment out line 25 (google-cloud-sdk)
```

**Option 2: Install missing tools**
```bash
# For rbenv
brew install rbenv

# For Google Cloud SDK
# Download from: https://cloud.google.com/sdk/docs/install
```

**Option 3: Ignore them**
They're just warnings and don't affect the TTS application.

## 📊 Performance

### Benchmarks

| Metric | Value |
|--------|-------|
| **Cold Start** | ~5 seconds (model loading) |
| **Synthesis Time** | 1-3 seconds (300 frames) |
| **Memory Usage** | ~1.5-2GB |
| **Throughput** | 10-20 requests/minute (single worker) |
| **Image Generation** | +500ms (matplotlib rendering) |

### Optimization Tips

```python
# 1. Use multiple workers (Gunicorn)
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

# 2. Enable caching (Redis)
# See DEPLOYMENT.md for Redis integration

# 3. Optimize Docker
# Use --build-arg PYTHON_VERSION=3.10-slim
```

## 🔐 Security

### Production Checklist

- ✅ Run as non-root user (configured in Dockerfile)
- ⚠️ Add HTTPS/SSL (use nginx + certbot)
- ⚠️ Implement rate limiting
- ⚠️ Add authentication (JWT tokens)
- ⚠️ Configure CORS properly
- ⚠️ Use environment variables for secrets

### Example: Add Rate Limiting

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.post("/api/synthesize", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def synthesize(...):
    ...
```

## 📈 Monitoring

### Health Monitoring

```bash
# Continuous health check
watch -n 5 'curl -s http://localhost:8000/health | jq'
```

### Docker Stats

```bash
# View resource usage
docker stats azerbaijani-tts

# View logs
docker logs -f --tail 100 azerbaijani-tts
```

### Application Metrics

Add Prometheus metrics:

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

## 🌐 Deployment Examples

### Deploy to Cloud

See `DEPLOYMENT.md` for detailed guides:
- AWS EC2
- Google Cloud Run
- Azure Container Instances
- DigitalOcean Droplets

### Quick Deploy (DigitalOcean)

```bash
# 1. Build and push to Docker Hub
docker build -t your-username/azerbaijani-tts:latest .
docker push your-username/azerbaijani-tts:latest

# 2. On server
docker pull your-username/azerbaijani-tts:latest
docker run -d -p 80:8000 your-username/azerbaijani-tts:latest
```

## 📝 Development

### Adding New Features

1. **New Endpoint**:
   ```python
   # app/main.py
   @app.post("/api/new-endpoint")
   async def new_feature(...):
       pass
   ```

2. **Update Frontend**:
   ```javascript
   // app/static/js/app.js
   async function newFeature() {
       const response = await fetch('/api/new-endpoint', ...);
   }
   ```

3. **Test Locally**:
   ```bash
   uvicorn app.main:app --reload
   ```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit: `git commit -m "Add feature"`
5. Push: `git push origin feature-name`
6. Create Pull Request

## 📜 License

This project uses the Azerbaijani ASR dataset from HuggingFace (LocalDoc/azerbaijani_asr) under CC-BY-NC-4.0 license.

## 🙏 Acknowledgments

- **Dataset**: LocalDoc/azerbaijani_asr (351k samples, 334 hours)
- **Framework**: FastAPI, PyTorch
- **Model**: Custom Seq2Seq with Attention (7.2M params)

## 📞 Support

- **Documentation**: See `DEPLOYMENT.md` for detailed deployment guide
- **Issues**: Check logs first (`docker logs` or `uvicorn` output)
- **Performance**: See benchmarks and optimization sections above

---

**Status**: ✅ Production Ready
**Version**: 1.0.0
**Last Updated**: 2026-01-04
