# Deployment Guide

This guide covers deploying the MAMA Rankings Tracker to production.

## Recommended Platform: Railway

Railway is the easiest option with SQLite support and background workers.

### Deploy to Railway (Free Tier Available)

1. **Create a Railway account**: Visit [railway.app](https://railway.app)

2. **Install Railway CLI** (optional):
   ```bash
   npm install -g @railway/cli
   ```

3. **Deploy via GitHub**:
   - Push your code to GitHub
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect and deploy

4. **Add a volume for persistent storage**:
   - In Railway dashboard, go to your service
   - Click "Variables" tab
   - Add volume: Mount path = `/app/data`
   - This keeps your SQLite database persistent

5. **Add background worker** (for automatic updates):
   - Click "New Service"
   - Select same repo
   - In "Settings" → "Start Command", enter:
     ```
     python3 -m src.scheduler --interval 60
     ```
   - Attach same volume `/app/data`

6. **Get your URL**:
   - Railway will provide a public URL like `https://yourapp.railway.app`

### Cost
- **Free tier**: $5/month credit (enough for this app)
- **Pro**: $20/month for unlimited usage

---

## Alternative 1: Render

### Deploy to Render

1. **Create account**: Visit [render.com](https://render.com)

2. **Create Web Service**:
   - Connect GitHub repository
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT src.app:APP`

3. **Add Disk for SQLite**:
   - In service settings, add disk
   - Mount path: `/opt/render/project/src/data`
   - Size: 1GB (free)

4. **Add Background Worker**:
   - Create new "Background Worker" service
   - Start Command: `python3 -m src.scheduler --interval 60`
   - Use same disk

### Cost
- **Free tier**: Available with 750 hours/month
- Disk storage is free up to 1GB

---

## Alternative 2: Fly.io

### Deploy to Fly.io

1. **Install Fly CLI**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login**:
   ```bash
   fly auth login
   ```

3. **Launch app**:
   ```bash
   fly launch
   ```
   - Choose app name
   - Select region
   - Don't deploy yet

4. **Add volume for SQLite**:
   ```bash
   fly volumes create mama_data --size 1
   ```

5. **Update fly.toml**:
   ```toml
   [mounts]
     source = "mama_data"
     destination = "/app/data"
   ```

6. **Deploy**:
   ```bash
   fly deploy
   ```

7. **Add scheduler as separate process** (in fly.toml):
   ```toml
   [processes]
     app = "gunicorn --bind 0.0.0.0:8080 src.app:APP"
     worker = "python3 -m src.scheduler --interval 60"
   ```

### Cost
- **Free tier**: 3 shared VMs
- Volume: $0.15/GB/month

---

## Alternative 3: DigitalOcean App Platform

1. **Create account**: [digitalocean.com](https://digitalocean.com)

2. **Create App**:
   - Connect GitHub
   - Choose "Web Service"
   - Build: `pip install -r requirements.txt`
   - Run: `gunicorn --bind 0.0.0.0:8080 src.app:APP`

3. **Add Worker**:
   - Add component → Worker
   - Run: `python3 -m src.scheduler --interval 60`

4. **Note**: DigitalOcean doesn't have persistent storage in free tier
   - Consider upgrading to use volumes
   - Or use managed database (PostgreSQL) instead of SQLite

### Cost
- **Starter**: $5/month
- Includes 1 web service + 1 worker

---

## Alternative 4: Traditional VPS (Cheaper for Long-term)

If you want full control and cheaper long-term hosting:

### Deploy to VPS (DigitalOcean, Linode, Vultr, etc.)

1. **Create a $4-6/month VPS**

2. **SSH into server and setup**:
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Python
   sudo apt install python3 python3-pip python3-venv -y

   # Clone repository
   git clone https://github.com/yourusername/mnet-mama-rankings.git
   cd mnet-mama-rankings

   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Setup systemd services**:

   Create `/etc/systemd/system/mama-web.service`:
   ```ini
   [Unit]
   Description=MAMA Rankings Web App
   After=network.target

   [Service]
   User=youruser
   WorkingDirectory=/home/youruser/mnet-mama-rankings
   Environment="PATH=/home/youruser/mnet-mama-rankings/.venv/bin"
   ExecStart=/home/youruser/mnet-mama-rankings/.venv/bin/gunicorn --bind 0.0.0.0:5000 src.app:APP
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Create `/etc/systemd/system/mama-scheduler.service`:
   ```ini
   [Unit]
   Description=MAMA Rankings Scheduler
   After=network.target

   [Service]
   User=youruser
   WorkingDirectory=/home/youruser/mnet-mama-rankings
   Environment="PATH=/home/youruser/mnet-mama-rankings/.venv/bin"
   ExecStart=/home/youruser/mnet-mama-rankings/.venv/bin/python3 -m src.scheduler --interval 60
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

4. **Start services**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable mama-web mama-scheduler
   sudo systemctl start mama-web mama-scheduler
   ```

5. **Setup Nginx reverse proxy**:
   ```bash
   sudo apt install nginx -y
   ```

   Create `/etc/nginx/sites-available/mama`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

   Enable and restart:
   ```bash
   sudo ln -s /etc/nginx/sites-available/mama /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. **Add SSL with Let's Encrypt**:
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d your-domain.com
   ```

### Cost
- VPS: $4-6/month
- Domain: $10-15/year (optional)

---

## Important Notes for Production

### Database Considerations

If you expect high traffic or want better reliability, consider switching from SQLite to PostgreSQL:

1. Update `requirements.txt`:
   ```
   psycopg2-binary>=2.9.0
   ```

2. Modify `storage.py` to use PostgreSQL connection string from environment variable

3. Most platforms offer free managed PostgreSQL (Railway, Render, etc.)

### Environment Variables

Set these in your platform's settings:
- `PORT` - Usually auto-set by platform
- `DB_PATH` - Path to SQLite or PostgreSQL connection string
- `FETCH_INTERVAL` - Minutes between updates (default 60)

### Monitoring

Add basic monitoring:
- Railway/Render have built-in logs
- Consider adding Sentry for error tracking
- Use UptimeRobot (free) to monitor uptime

---

## My Recommendation

**For you: Use Railway**

Why?
- ✅ Free tier available ($5/month credit)
- ✅ SQLite works perfectly with volumes
- ✅ Easy GitHub integration
- ✅ Background workers supported
- ✅ Zero DevOps knowledge needed
- ✅ SSL certificates automatic
- ✅ Takes 5 minutes to deploy

Just push to GitHub and deploy - done! 🚀
