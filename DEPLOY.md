# Deployment Guide

Deploy the full stack: **Flask UI + MongoDB + Ollama embeddings + email pipeline**.

> **Want always-on hosting at $0/month?** See **[DEPLOY-FREE.md](DEPLOY-FREE.md)** (Oracle Cloud — needs card for verification).  
> **No credit card?** See **[DEPLOY-NO-CARD.md](DEPLOY-NO-CARD.md)** (Render + MongoDB Atlas).

---

## Share a link today (from your PC, ~2 minutes)

Use this when you want a **public HTTPS URL** to send to friends **without buying a server**. Your PC must stay on and Docker must be running.

```powershell
.\deploy.ps1 -Up          # if not already running
.\deploy.ps1 -Share       # or: .\share.ps1
```

Copy the URL that looks like `https://something-random.trycloudflare.com` and share it.

**Limits:** link stops when you close the tunnel or shut down your PC; URL changes each time you restart the tunnel (unless you set up a named Cloudflare tunnel with an account).

---

## Permanent link (VPS — recommended for a real “deployed” app)

Buy a small Linux server (~$6–12/mo), then on the server:

```bash
git clone https://github.com/shahharsh2712/Personalized_Recommendation-Bot.git
cd Personalized_Recommendation-Bot
cp .env.example .env && nano .env   # paste your secrets
bash deploy/server-setup.sh
```

Open **http://YOUR_SERVER_IP** (port 80). For **https://yourdomain.com**, edit `deploy/Caddyfile` with your domain, point DNS A record to the server IP, and run:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## Recommended: VPS + Docker (DigitalOcean, Hetzner, AWS EC2, etc.)

Works with Ollama (free local embeddings) and Gmail SMTP.

### Server requirements

- **2 GB+ RAM** (4 GB recommended if Ollama runs on same machine)
- Ubuntu 22.04+ or similar
- Docker + Docker Compose installed

### Step 1 — Get a server

Examples:

- [DigitalOcean Droplet](https://www.digitalocean.com/) — $6–12/mo
- [Hetzner Cloud](https://www.hetzner.com/cloud) — low cost
- [AWS EC2](https://aws.amazon.com/ec2/) — t3.small or larger

### Step 2 — Install Docker on the server

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in
```

### Step 3 — Clone your project

```bash
git clone https://github.com/shahharsh2712/Personalized_Recommendation-Bot.git
cd Personalized_Recommendation-Bot
```

### Step 4 — Configure environment

```bash
cp .env.example .env
nano .env
```

Required settings:

```env
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
MONGODB_URI=mongodb://mongo:27017/
RECOMMENDATION_DB_NAME=app_recommendations

EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SENDER_EMAIL=your@gmail.com

OPENAI_API_KEY=...          # optional (chat only)
PERPLEXITY_API_KEY=...      # for product collection
PRODUCT_HUNT_DEVELOPER_TOKEN=...
```

### Step 5 — Start services

```bash
docker compose up -d --build
```

**Windows (already have Ollama installed):** faster local option — skip 3GB Docker Ollama image:

```powershell
# Stop any in-progress compose pull first (Ctrl+C), then:
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
ollama pull nomic-embed-text   # on your PC, not in Docker
.\deploy.ps1 -PullModel        # only if using Docker ollama service
```

Pull the embedding model (first time only, ~5 min):

```bash
docker exec -it $(docker compose ps -q ollama) ollama pull nomic-embed-text
# Or on host: ollama pull nomic-embed-text
```

### Step 6 — Load product data (first deploy)

Copy your `data_store/` to the server, or run on server:

```bash
docker compose exec web python reembed_with_ollama.py
```

### Step 7 — Open the app

- **http://YOUR_SERVER_IP:5000**
- Sign up → profile setup → dashboard

### Step 8 — HTTPS with a domain (recommended)

1. Point domain A record to server IP
2. Install Caddy or Nginx reverse proxy to `localhost:5000`
3. Example with Caddy (`/etc/caddy/Caddyfile`):

```
yourdomain.com {
    reverse_proxy localhost:5000
}
```

### Daily emails (cron on server)

```bash
crontab -e
```

Add:

```
0 8 * * * cd /path/to/Personalized_Recommendation-Bot && docker compose exec -T web python main.py --mode workflow >> /var/log/rec-bot.log 2>&1
```

---

## MongoDB Atlas (optional cloud DB)

If you prefer managed MongoDB instead of Docker `mongo`:

1. Create free cluster at [mongodb.com/atlas](https://www.mongodb.com/atlas)
2. Get connection string → set in `.env`:
   ```env
   MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=Majority
   ```
3. Remove `mongo` service from `docker-compose.yml` or don't start it

---

## What runs where

| Service | Role |
|---------|------|
| `web` | Flask UI + API (port 5000) |
| `mongo` | User profiles, products, recommendations |
| `ollama` | Free embeddings (`nomic-embed-text`) |

---

## Useful commands

```bash
docker compose logs -f web
docker compose restart web
docker compose exec web python main.py --mode recommend --email user@example.com
docker compose exec web python main.py --mode email --email user@example.com
docker compose down
```

---

## Security checklist

- [ ] Never commit `.env` to GitHub
- [ ] Use Gmail **App Password**, not main password
- [ ] Open only ports 80/443 (and 22 for SSH); block 27017 publicly
- [ ] Rotate API keys if they were ever exposed
