# BarberShopBackend

FastAPI backend for a barbershop SaaS: business/barber accounts, schedules, bookings, reviews, and Stripe subscription billing.

## Local development (without Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then fill in real values

alembic upgrade head
uvicorn main:app --reload --port 8000
```

## Local development with Docker

```bash
cp .env.example .env   # then fill in real values (POSTGRES_URL is overridden by docker-compose)
docker compose up --build
```

This starts Postgres and the API together, runs migrations automatically on boot, and serves on `http://localhost:8000`.

## Deploying to an EC2 instance

1. **Launch an instance** — Ubuntu 22.04/24.04 LTS, `t3.small` is plenty to start. Open inbound ports 22 (SSH), 80 and 443 (HTTP/HTTPS) in the security group. Don't expose port 8000 publicly — it should only be reachable through the reverse proxy (step 4).

2. **Install Docker** on the instance:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   # log out and back in for the group change to apply
   ```

3. **Get the code onto the instance** and configure it:
   ```bash
   git clone https://github.com/EKorchevsky/BarberShopBackend.git
   cd BarberShopBackend
   cp .env.example .env
   nano .env   # fill in real SECRET_KEY, POSTGRES_URL, Stripe keys, FRONTEND_URL, ENVIRONMENT=production
   ```
   For the database, either point `POSTGRES_URL` at a managed **RDS Postgres** instance (recommended for anything beyond a demo — automatic backups, no DB data living on the same disk as the app), or run Postgres via `docker compose up -d db` on the same box for now.

4. **Put a reverse proxy with HTTPS in front of it.** This matters more than it looks: with `ENVIRONMENT=production` the backend marks its refresh-token cookie `secure=True`, so browsers will silently refuse to send it back over plain HTTP — logins would appear to work but refresh would break. Easiest option is [Caddy](https://caddyserver.com/) — it gets you a free Let's Encrypt certificate with zero config:
   ```bash
   sudo apt install -y caddy
   ```
   `/etc/caddy/Caddyfile`:
   ```
   api.yourdomain.com {
       reverse_proxy localhost:8000
   }
   ```
   Point the domain's DNS A record at the instance's IP first, then `sudo systemctl reload caddy`.

5. **Run the app:**
   ```bash
   docker compose up -d --build
   ```
   Migrations run automatically on container start (see `entrypoint.sh`). To redeploy after a `git pull`, just `docker compose up -d --build` again.

6. **Stripe webhook (production only):** in the Stripe Dashboard → Developers → Webhooks, add an endpoint pointing at `https://api.yourdomain.com/billing/webhook`, subscribe it to `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, and put the signing secret it gives you into `STRIPE_WEBHOOK_SECRET` in `.env` on the server (it's different from the one `stripe listen` gives you locally).

7. **CORS / frontend URL:** update `origins` in `main.py` and `FRONTEND_URL` in `.env` to your real frontend domain before going live — right now both only allow `localhost:3000`.
