# Deploy without a credit card

Oracle, AWS, Google Cloud, and Azure almost always ask for a card—even when you stay on “free” tiers. If you do not have a card, use one of the options below.

---

## Option 1 — Render.com (recommended, $0, no card)

**[Render](https://render.com)** lets you deploy from GitHub with **no credit card**. You get a permanent URL like `https://your-app.onrender.com`.

### Trade-offs (important)

| | |
|--|--|
| ✅ Free forever on Hobby plan | ❌ Not a full VPS (no Ollama on the server) |
| ✅ HTTPS link to share | ❌ App **sleeps after ~15 min** with no visitors (first visit wakes it, ~30–60 s) |
| ✅ MongoDB Atlas works (free, no card) | ❌ Signups live in JSON on the server — **reset if you redeploy** |

Search still works using your **pre-built product index** (`data_store` + `vector_store.pkl`) and keyword matching.

### Steps

**1. MongoDB Atlas (free database, no card)**

1. Sign up at [mongodb.com/atlas](https://www.mongodb.com/cloud/atlas/register).
2. Create a **free M0** cluster.
3. **Database Access** → add user + password.
4. **Network Access** → **Allow access from anywhere** (`0.0.0.0/0`) for Render.
5. **Connect** → copy the connection string, e.g.  
   `mongodb+srv://USER:PASS@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=Majority`

**2. Push code to GitHub**

- Do **not** commit `.env`.
- Ensure `data_store/*.json` and `src/data/vector_store.pkl` are in the repo (or run `reembed_with_ollama.py` locally first so products are indexed).

**3. Deploy on Render**

1. [dashboard.render.com](https://dashboard.render.com) → sign up with **GitHub** (no card).
2. **New +** → **Blueprint** → connect your repo.
3. Render reads `render.yaml`. Add **Environment** secrets in the dashboard:

   | Variable | Value |
   |----------|--------|
   | `MONGODB_URI` | Atlas connection string |
   | `SMTP_USER` | Gmail address |
   | `SMTP_PASSWORD` | Gmail app password (no spaces) |
   | `SENDER_EMAIL` | Same Gmail |
   | `PERPLEXITY_API_KEY` | optional |
   | `PRODUCT_HUNT_DEVELOPER_TOKEN` | optional |

4. Deploy. When finished, open the URL Render shows (e.g. `https://personalized-rec-bot.onrender.com`).

**4. First visit**

The free instance may be asleep. Wait up to a minute on first load.

### Keep it awake longer (optional)

Free Render is meant to sleep. Some people use a free monitor (e.g. [UptimeRobot](https://uptimerobot.com)) to ping the site every 14 minutes. That can reduce sleep but may conflict with Render’s terms—use for demos only.

---

## Option 2 — Share from your PC (no card, no signup beyond Cloudflare)

You already have this:

```powershell
.\deploy.ps1 -Up
.\deploy.ps1 -Share
```

Share the `https://….trycloudflare.com` link.

| | |
|--|--|
| ✅ No card | ❌ Link dies when your PC sleeps or tunnel stops |
| ✅ Full app (Ollama + Mongo) | ❌ Not “always on” unless the PC runs 24/7 |

---

## Option 3 — Old laptop / PC at home as “server” (no card)

1. Leave a spare computer on at home.
2. Run Docker: `.\deploy.ps1 -Up`
3. Create a **free [Cloudflare](https://dash.cloudflare.com/sign-up)** account (no card for basic account).
4. Install a **named tunnel** so you get a stable hostname (see [Cloudflare Tunnel docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)).

Cost: electricity only. Always-on if the machine stays on.

---

## Option 4 — Try Alibaba Cloud (sometimes no card)

Some regions let you sign up **without a credit card** for a small free trial. Quality and signup rules vary by country.

- [Alibaba Cloud Free Trial](https://www.alibabacloud.com/campaign/free-trial)
- If signup works, use the same steps as `DEPLOY-FREE.md` but on that VM.

Treat unknown “free VPS” sites with caution—many are unreliable or unsafe.

---

## Option 5 — When you eventually have a card

**Oracle Cloud Always Free** remains the best **$0 always-on** full stack (Mongo + Ollama + Flask). See [DEPLOY-FREE.md](DEPLOY-FREE.md).

A normal **debit card** (including many bank cards in India) is often enough for verification; Oracle usually does not charge if you only use Always Free resources.

---

## Quick comparison

| Method | Credit card | Always on | Full Ollama | Shareable HTTPS |
|--------|-------------|-----------|-------------|-----------------|
| **Render + Atlas** | No | Mostly* | No (keyword + index) | Yes |
| **PC + share.ps1** | No | No | Yes | Yes |
| **Home PC + Cloudflare** | No | If PC on 24/7 | Yes | Yes |
| **Oracle Always Free** | Yes (verify) | Yes | Yes | Yes (with IP/domain) |

\*Render free tier sleeps after inactivity.

---

## Recommended path for you now

1. **MongoDB Atlas** (5 min, no card)  
2. **Render** + `render.yaml` (15 min, no card)  
3. Share `https://….onrender.com`

If you want help on a specific step (Atlas connection string, Render env vars, or GitHub push), say which step you are on.
