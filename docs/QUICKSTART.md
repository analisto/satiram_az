# Azerbaijani TTS - Quick Start Guide

Get the Azerbaijani Text-to-Speech application running in under 5 minutes using Docker.

## Prerequisites

- **Docker Desktop** installed and running ([Download here](https://www.docker.com/products/docker-desktop))
- **Docker Compose** (included with Docker Desktop)
- At least **4GB RAM** available
- **500MB** free disk space

### Verify Docker Installation

```bash
docker --version
docker-compose --version
```

Expected output:
```
Docker version 20.10.x or higher
Docker Compose version 2.x or higher
```

---

## Quick Start (Docker Compose)

The fastest way to run the application:

### 1. Clone or Navigate to Project

```bash
cd /path/to/text_to_speech
```

### 2. Start the Application

```bash
docker-compose up -d --build
```

This command will:
- Build the Docker image (~2-3 minutes first time)
- Start the container in detached mode
- Expose the app on `http://localhost:8000`

### 3. Verify It's Running

Check the health status:

```bash
docker-compose ps
```

You should see:
```
NAME                  STATUS              PORTS
azerbaijani-tts       Up (healthy)        0.0.0.0:8000->8000/tcp
```

Or check the health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "vocab_size": 124
}
```

### 4. Access the Application

Open your browser and navigate to:

```
http://localhost:8000
```

You should see the Azerbaijani TTS web interface!

---

## Common Docker Commands

### View Logs

Watch the application logs in real-time:

```bash
docker-compose logs -f
```

Press `Ctrl+C` to exit log viewing.

### Stop the Application

```bash
docker-compose down
```

### Restart the Application

```bash
docker-compose restart
```

### Rebuild After Code Changes

```bash
docker-compose up -d --build --force-recreate
```

### Check Container Status

```bash
docker-compose ps
```

### Execute Commands Inside Container

```bash
docker-compose exec tts-app bash
```

---

## Alternative: Docker Run (Without Compose)

If you prefer using plain Docker commands:

### Build the Image

```bash
docker build -t azerbaijani-tts:latest .
```

### Run the Container

```bash
docker run -d \
  --name azerbaijani-tts \
  -p 8000:8000 \
  -v $(pwd)/artifacts:/app/artifacts:ro \
  azerbaijani-tts:latest
```

### View Logs

```bash
docker logs -f azerbaijani-tts
```

### Stop and Remove Container

```bash
docker stop azerbaijani-tts
docker rm azerbaijani-tts
```

---

## Testing the API

Once the application is running, test the synthesis endpoints:

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Get Model Statistics

```bash
curl http://localhost:8000/api/stats
```

### 3. Synthesize Text (JSON Response)

```bash
curl -X POST http://localhost:8000/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Salam, necəsən?", "max_length": 300}'
```

### 4. Generate Mel Spectrogram Image

```bash
curl -X POST http://localhost:8000/api/synthesize/image \
  -H "Content-Type: application/json" \
  -d '{"text": "Salam dünya", "max_length": 300}' \
  --output spectrogram.png
```

### 5. Generate Audio (WAV)

```bash
curl -X POST http://localhost:8000/api/synthesize/audio \
  -H "Content-Type: application/json" \
  -d '{"text": "Bu gözəl bir gündür", "max_length": 300}' \
  --output output.wav
```

---

## Troubleshooting

### Docker Daemon Not Running

**Error:** `Cannot connect to the Docker daemon`

**Solution:**
- Open Docker Desktop application
- Wait for Docker to fully start (whale icon in system tray should be steady)
- Retry the command

### Port 8000 Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:** Change the port in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

Then access the app at `http://localhost:8001`

### Model Files Missing

**Error:** `Model not loaded` or `FileNotFoundError`

**Solution:** Ensure the `artifacts/` directory contains:
- `best_model.pt` (82-86 MB)
- `char_encoder.pkl` (1-2 KB)

Check with:
```bash
ls -lh artifacts/
```

If files are missing, you need to train the model first using the Jupyter notebook.

### Container Stuck in "Starting" State

**Solution:** Check the logs for errors:

```bash
docker-compose logs -f
```

Common issues:
- Insufficient memory (increase Docker memory limit to 4GB+)
- Corrupted model files (re-download or retrain)
- Port conflicts

### Container Exits Immediately

**Solution:** Check the exit code and logs:

```bash
docker-compose ps
docker-compose logs
```

Look for Python errors in the startup sequence.

---

## Resource Configuration

### Adjust Memory Limits

Edit `docker-compose.yml` if you need to change resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Increase CPU limit
      memory: 8G       # Increase memory limit
    reservations:
      cpus: '2.0'
      memory: 4G
```

### Development Mode

To enable hot-reload for development, uncomment this line in `docker-compose.yml`:

```yaml
volumes:
  - ./artifacts:/app/artifacts:ro
  - ./app:/app/app  # Uncomment this for development
```

Then restart:
```bash
docker-compose up -d --build
```

---

## Next Steps

Once you have the application running:

1. **Use the Web Interface**: Open `http://localhost:8000` and try synthesizing Azerbaijani text
2. **Explore the API**: Use the endpoints to integrate TTS into your applications
3. **Read Full Documentation**: Check `docs/DEPLOYMENT.md` for production deployment
4. **Review Architecture**: See `docs/WEB_APP_README.md` for technical details

---

## Quick Reference Card

```bash
# Start
docker-compose up -d --build

# Stop
docker-compose down

# Logs
docker-compose logs -f

# Restart
docker-compose restart

# Status
docker-compose ps

# Health check
curl http://localhost:8000/health

# Web interface
open http://localhost:8000
```

---

## Support

Having issues? Check:

1. **Logs**: `docker-compose logs -f`
2. **Health**: `curl http://localhost:8000/health`
3. **Artifacts**: `ls -lh artifacts/`
4. **Docker**: Make sure Docker Desktop is running
5. **Memory**: Ensure at least 4GB RAM is available

For detailed deployment options, see [DEPLOYMENT.md](DEPLOYMENT.md).
