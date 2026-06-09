# Free always-on deployment ($0/month)

The only realistic way to run **Flask + MongoDB + Ollama** 24/7 without paying monthly is **[Oracle Cloud Always Free](https://www.oracle.com/cloud/free/)** — an ARM VM with up to **4 CPUs and 24 GB RAM**, free forever (within Always Free limits).

> **No credit card?** Oracle requires card verification. Use **[DEPLOY-NO-CARD.md](DEPLOY-NO-CARD.md)** instead (Render.com + MongoDB Atlas — free, no card).

> **Credit card available:** Oracle may ask for a card to verify identity. Stay on **Always Free** shapes only — you are not charged if you do not upgrade to paid resources.

---

## What you get

| Item | Cost |
|------|------|
| Linux VM (ARM) | $0 |
| Docker: web + mongo + ollama | $0 |
| HTTPS via your domain (optional) | $0 (Caddy + Let’s Encrypt) |
| MongoDB Atlas M0 (optional instead of Docker mongo) | $0 |

**Shareable link:** `http://YOUR_VM_PUBLIC_IP` (port 80), or `https://yourdomain.com` if you add a domain later.

---

## Step 1 — Create Oracle Cloud account

1. Go to [oracle.com/cloud/free](https://www.oracle.com/cloud/free/) and sign up.
2. After login, open **Compute → Instances → Create instance**.

---

## Step 2 — Create the VM (Always Free)

Use these settings:

| Setting | Value |
|---------|--------|
| Name | `rec-bot` |
| Image | **Ubuntu 22.04** (or 24.04) |
| Shape | **Ampere** → **VM.Standard.A1.Flex** |
| OCPUs | **2** (you can use up to 4 free) |
| Memory (GB) | **12** (fits mongo + ollama + web) |
| Boot volume | 50 GB (default is fine) |
| SSH keys | Add your **public** key (or “Generate key pair” and download the private key) |

Click **Create**. Note the **public IP** when the instance is **Running**.

---

## Step 3 — Open firewall ports

**A) Oracle Security List (required)**

1. **Networking → Virtual cloud networks** → your VCN → **Security Lists** → Default.
2. **Add Ingress Rules:**
   - Source `0.0.0.0/0`, TCP, port **22** (SSH)
   - Source `0.0.0.0/0`, TCP, port **80** (HTTP)
   - Source `0.0.0.0/0`, TCP, port **443** (HTTPS, optional)

**B) Ubuntu firewall on the VM**

```bash
ssh ubuntu@YOUR_PUBLIC_IP
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

---

## Step 4 — Install the app on the VM

On your PC, copy `.env` to the server (do **not** commit `.env` to GitHub):

```bash
scp -i your-key.pem .env ubuntu@YOUR_PUBLIC_IP:~/
```

On the server:

```bash
ssh ubuntu@YOUR_PUBLIC_IP

sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/shahharsh2712/Personalized_Recommendation-Bot.git
cd Personalized_Recommendation-Bot
mv ~/.env .env
nano .env   # confirm values below
bash deploy/oracle-setup.sh
```

### `.env` on the server (minimum)

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
SMTP_PASSWORD=your_gmail_app_password_without_spaces
SENDER_EMAIL=your@gmail.com

PERPLEXITY_API_KEY=...
PRODUCT_HUNT_DEVELOPER_TOKEN=...
```

---

## Step 5 — Share the link

Open in a browser:

```text
http://YOUR_PUBLIC_IP
```

Anyone can sign up and use the app while the VM is running.

---

## Optional: free HTTPS without buying a domain

Use a **free Cloudflare account** + tunnel on the VM (stable subdomain):

```bash
# On the VM
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

cloudflared tunnel login
cloudflared tunnel create rec-bot
# In Cloudflare dashboard, route a hostname (e.g. rec-bot.yourdomain.com) to the tunnel
cloudflared tunnel run rec-bot
```

(If you do not own a domain, `http://PUBLIC_IP` is enough to share.)

---

## Optional: save RAM with MongoDB Atlas

If the VM feels tight on memory:

1. Create a free cluster at [mongodb.com/atlas](https://www.mongodb.com/atlas) (M0).
2. Allow network access: **0.0.0.0/0** (or the VM IP only, safer).
3. Put the connection string in `.env`:
   ```env
   MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=Majority
   ```
4. Redeploy without Docker mongo:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.atlas.yml -f docker-compose.oracle.yml -f docker-compose.prod.yml up -d --build ollama web caddy
   ```

---

## Useful commands (on the VM)

```bash
docker compose -f docker-compose.yml -f docker-compose.oracle.yml -f docker-compose.prod.yml ps
docker compose -f docker-compose.yml -f docker-compose.oracle.yml -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.yml -f docker-compose.oracle.yml -f docker-compose.prod.yml exec web python main.py --mode recommend --email user@example.com
```

---

## What is NOT free long-term

| Service | Notes |
|---------|--------|
| DigitalOcean / Hetzner | Paid after trial |
| Railway / Render free | Sleeps or very limited; poor fit for Ollama |
| Your PC + Cloudflare tunnel | Free URL but **not** always on unless PC is on 24/7 |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Site not loading | Check Security List ports 80/443 and `docker compose ps` |
| `ollama pull` slow | Normal first time; wait on VM |
| Out of memory | Use Atlas (`docker-compose.atlas.yml`) or set VM RAM to 12 GB |
| Email fails | Gmail **App Password**, no spaces in `SMTP_PASSWORD` |

---

## Quick comparison

| Method | Always on | Monthly cost |
|--------|-----------|--------------|
| **Oracle Always Free** | Yes | **$0** |
| `share.ps1` (your PC) | Only while PC + tunnel run | $0 |
| Paid VPS | Yes | ~$6–12 |

For a permanent shareable link at **$0**, use **Oracle + `deploy/oracle-setup.sh`**.
