## TransChamberWebsite1 — GitHub and Linux VPS Deployment Guide

This README walks you through pushing this project to GitHub and deploying it on a Linux VPS using Python (Flask), MySQL, Gunicorn, systemd, and Nginx. All commands are copy-pasteable.

Key stack details from this repo:
- Flask app factory in `run.py` (`app = create_app()`)
- Config in `config.py` reads `.env` (SECRET_KEY, DB_*, MAIL_*, RECAPTCHA_*)
- MySQL via SQLAlchemy (`mysql+pymysql`)
- Migrations via Flask-Migrate (`migrations/` exists)
- Static CSS built with Tailwind CLI under `app/static`

### 1) Prepare your local repo and push to GitHub

Run these from your local machine in the project root `TransChamberWebsite1`.

```bash
# 1. Initialize git (if not already)
git init

# 2. Create a .gitignore if you don't have one yet (recommended)
printf "env/\n__pycache__/\n*.pyc\n*.pyo\n*.pyd\n*.sqlite3\n*.db\ninstance/\n.mypy_cache/\n.pytest_cache/\n.env\nnode_modules/\napp/static/css/output.css\n" > .gitignore

# 3. Commit current code
git add .
git commit -m "Initial commit: TransChamberWebsite1"

# 4. Create a new GitHub repo in your account (via UI) named TransChamberWebsite1
#    Then set the remote and push (replace <YOUR_GITHUB_USERNAME>)
git branch -M main
git remote add origin git@github.com:<YOUR_GITHUB_USERNAME>/TransChamberWebsite1.git
git push -u origin main
```

If you prefer HTTPS for the remote:

```bash
git remote set-url origin https://github.com/<YOUR_GITHUB_USERNAME>/TransChamberWebsite1.git
git push -u origin main
```

### 2) VPS: System packages and users

SSH into your VPS and run:

```bash
sudo apt update -y && sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-pip mysql-server nginx ufw

# Optional but recommended: create a deploy directory
sudo mkdir -p /var/www
sudo chown $USER:$USER /var/www
```

### 3) VPS: MySQL database and user

Adjust names and passwords as needed, then paste into your VPS shell:

```bash
sudo service mysql start || true
sudo mysql -e "CREATE DATABASE transchamber CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER 'trans_user'@'localhost' IDENTIFIED BY 'StrongPasswordHere';"
sudo mysql -e "GRANT ALL PRIVILEGES ON transchamber.* TO 'trans_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
```

### 4) VPS: Clone project and create Python virtualenv

```bash
cd /var/www
git clone https://github.com/<YOUR_GITHUB_USERNAME>/TransChamberWebsite1.git
cd TransChamberWebsite1

# Create and activate venv
python3 -m venv env
source env/bin/activate

# Install Python dependencies
pip install --upgrade pip wheel
pip install -r requirements.txt
```

### 5) VPS: Create .env configuration

Create a `.env` file in the project root with your production secrets and settings:

```bash
cat > .env << 'EOF'
SECRET_KEY=change_this_to_a_strong_random_key

# MySQL
DB_USER=trans_user
DB_PASSWORD=StrongPasswordHere
DB_HOST=localhost
DB_PORT=3306
DB_NAME=transchamber

# Mail (adjust for your SMTP provider)
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=no-reply@example.com
MAIL_PASSWORD=your_smtp_password
MAIL_DEFAULT_SENDER=no-reply@example.com

# reCAPTCHA (replace with your real keys)
RECAPTCHA_SITE_KEY=your_site_key
RECAPTCHA_SECRET_KEY=your_secret_key
EOF
```

Notes:
- In production, use HTTPS and set `SESSION_COOKIE_SECURE=true` in `config.py` if you modify the code accordingly.

### 6) VPS: Run database migrations

This project includes Flask-Migrate and a `migrations/` directory. Use the Flask CLI with the app factory in `run.py`:

```bash
export FLASK_APP=run.py
export FLASK_ENV=production

# Upgrade database to latest migration
flask db upgrade
```

If you ever need to generate migrations after changing models (during future updates):

```bash
flask db migrate -m "Describe your change"
flask db upgrade
```

### 7) VPS: Build Tailwind CSS (static assets)

This repo uses Tailwind CLI inside `app/package.json`. For a one-time build on the VPS:

```bash
sudo apt install -y nodejs npm

# Build CSS into app/static/css/output.css
npx @tailwindcss/cli -i app/static/src/input.css -o app/static/css/output.css
```

If you need to re-build automatically during development, there is a script with `--watch` in `app/package.json`, but for production a one-time build is enough.

### 8) VPS: Test run with Gunicorn (temporary)

```bash
source env/bin/activate
gunicorn -w 3 -b 127.0.0.1:8000 run:app
```

Visit the server’s IP on port 8000 (if exposed) or proceed to Nginx setup below to serve on ports 80/443.

### 9) VPS: systemd service for Gunicorn

Create a service so the app runs on boot and restarts automatically:

```bash
sudo tee /etc/systemd/system/transchamber.service > /dev/null << 'EOF'
[Unit]
Description=Gunicorn instance for TransChamberWebsite1
After=network.target

[Service]
User=%i
Group=www-data
WorkingDirectory=/var/www/TransChamberWebsite1
Environment="PATH=/var/www/TransChamberWebsite1/env/bin"
Environment="FLASK_APP=run.py"
Environment="FLASK_ENV=production"
ExecStart=/var/www/TransChamberWebsite1/env/bin/gunicorn -w 3 -b 127.0.0.1:8000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# If your deploy user is, for example, 'ubuntu', replace %i with ubuntu in the file above
sudo sed -i "s/User=%i/User=$(whoami)/" /etc/systemd/system/transchamber.service

sudo systemctl daemon-reload
sudo systemctl enable transchamber
sudo systemctl start transchamber
sudo systemctl status --no-pager transchamber | cat
```

### 10) VPS: Nginx reverse proxy

```bash
sudo tee /etc/nginx/sites-available/transchamber > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 16M;

    location /static/ {
        alias /var/www/TransChamberWebsite1/app/static/;
        access_log off;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/transchamber /etc/nginx/sites-enabled/transchamber
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

Optional: enable firewall for Nginx HTTP/HTTPS (if UFW is used):

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
sudo ufw status
```

### 11) Environment updates and restarts

If you update `.env` or pull new code:

```bash
cd /var/www/TransChamberWebsite1
git pull origin main
source env/bin/activate
pip install -r requirements.txt

# Rebuild CSS if static styles changed
npx @tailwindcss/cli -i app/static/src/input.css -o app/static/css/output.css

# Run migrations if models changed
export FLASK_APP=run.py
flask db upgrade

# Restart app
sudo systemctl restart transchamber
sudo systemctl status --no-pager transchamber | cat
```

### 12) Quick troubleshooting

```bash
# Check Gunicorn logs via systemd
sudo journalctl -u transchamber -e --no-pager | cat

# Check Nginx status and error logs
sudo systemctl status --no-pager nginx | cat
sudo tail -n 200 /var/log/nginx/error.log

# Verify Python deps and Python path
source /var/www/TransChamberWebsite1/env/bin/activate
python -V
pip list
```

### 13) Running locally for development

```bash
# From project root
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
pip install -r requirements.txt

# Set env for Flask CLI
export FLASK_APP=run.py
export FLASK_ENV=development

# Create .env (see production example but with local DB)

# Initialize DB (if needed) and run server
flask db upgrade
python run.py  # runs on http://127.0.0.1:5001

# Build CSS during development (watch mode optional)
npx @tailwindcss/cli -i app/static/src/input.css -o app/static/css/output.css --watch
```

### 14) What this deployment uses

- `Gunicorn` to serve `run:app` on `127.0.0.1:8000`
- `systemd` to keep the app running
- `Nginx` as reverse proxy and to serve static files from `app/static`
- `Flask-Migrate` to manage DB schema
- `Tailwind CLI` to compile CSS to `app/static/css/output.css`

Your site should now be available at your VPS IP or domain.


