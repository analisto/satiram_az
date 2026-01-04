# Azerbaijani TTS - Deployment Guide

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Build and start the application
docker-compose up -d --build

# View logs
docker-compose logs -f

# Access the application
open http://localhost:8000
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Access the application
open http://localhost:8000
```

## Project Structure

```
text_to_speech/
├── app/
│   ├── __init__.py           # App initialization
│   ├── main.py               # FastAPI application
│   ├── model.py              # TTS model definition
│   ├── templates/
│   │   └── index.html        # Frontend template
│   └── static/
│       ├── css/
│       │   └── style.css     # Styles
│       └── js/
│           └── app.js        # Frontend logic
├── artifacts/
│   ├── best_model.pt         # Trained model (82MB)
│   └── char_encoder.pkl      # Character encoder
├── Dockerfile                # Container definition
├── docker-compose.yml        # Orchestration
└── requirements.txt          # Python dependencies
```

## API Endpoints

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

### Synthesize (JSON)
```bash
POST /api/synthesize

Request:
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

### Synthesize (Image)
```bash
POST /api/synthesize/image

Request:
{
  "text": "Salam, necəsən?",
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
  "device": "cpu",
  "max_text_length": 200
}
```

## Docker Commands

### Build Image
```bash
docker build -t azerbaijani-tts:latest .
```

### Run Container
```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/artifacts:/app/artifacts:ro \
  --name azerbaijani-tts \
  azerbaijani-tts:latest
```

### View Logs
```bash
docker logs -f azerbaijani-tts
```

### Stop Container
```bash
docker stop azerbaijani-tts
docker rm azerbaijani-tts
```

## Production Deployment

### Environment Variables

```bash
# Optional configuration
export LOG_LEVEL=info
export WORKERS=4
export HOST=0.0.0.0
export PORT=8000
```

### Multi-worker Deployment

```bash
# Using Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Resource Requirements

### Minimum
- CPU: 2 cores
- RAM: 2GB
- Disk: 500MB

### Recommended
- CPU: 4 cores
- RAM: 4GB
- Disk: 1GB

## Performance Tuning

### CPU Optimization
The model is optimized for CPU inference. For better performance:

```python
# Set thread count
import torch
torch.set_num_threads(4)
```

### Caching
Implement Redis for caching frequently synthesized phrases:

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="tts-cache")
```

## Monitoring

### Health Checks
```bash
# Check if service is healthy
curl http://localhost:8000/health

# Check model stats
curl http://localhost:8000/api/stats
```

### Metrics
- Response time: ~1-3 seconds per synthesis
- Throughput: ~10-20 requests/minute (single worker)
- Memory usage: ~1.5-2GB

## Troubleshooting

### Model not loading
```bash
# Check artifacts directory
ls -lh artifacts/

# Should see:
# best_model.pt (82MB)
# char_encoder.pkl (< 1MB)
```

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use port 8001 instead
```

### Memory issues
```bash
# Reduce max_length parameter
# Or increase Docker memory limit in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 6G
```

## Security

### Production Checklist
- [ ] Use HTTPS (SSL/TLS certificates)
- [ ] Implement rate limiting
- [ ] Add authentication for API endpoints
- [ ] Enable CORS appropriately
- [ ] Use secrets for sensitive config
- [ ] Run as non-root user (already configured in Dockerfile)

## Scaling

### Horizontal Scaling
Deploy multiple instances behind a load balancer:

```yaml
# docker-compose with load balancing
version: '3.8'
services:
  tts-app:
    deploy:
      replicas: 3
```

### Load Balancer (HAProxy)
```
backend tts_backend
    balance roundrobin
    server tts1 localhost:8001 check
    server tts2 localhost:8002 check
    server tts3 localhost:8003 check
```

## License

This deployment uses the Azerbaijani ASR dataset from HuggingFace (LocalDoc/azerbaijani_asr) under CC-BY-NC-4.0 license.

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review health: `curl http://localhost:8000/health`
- Verify artifacts: `ls -lh artifacts/`
