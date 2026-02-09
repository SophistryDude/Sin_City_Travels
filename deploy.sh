#!/usr/bin/env bash
set -euo pipefail

# ─── Sin City Travels — EC2 Deployment Script ───────────────────────────────
#
# Prerequisites:
#   - Ubuntu/Debian EC2 with Nginx and PostgreSQL already installed
#   - SSH access and sudo privileges
#
# Usage:
#   1. Clone the repo on your EC2:
#        git clone https://github.com/SophistryDude/Sin_City_Travels.git
#        cd Sin_City_Travels
#
#   2. Run this script:
#        chmod +x deploy.sh
#        sudo ./deploy.sh
#
# After running, the app will be available at http://<your-ec2-ip>:8888/
# ─────────────────────────────────────────────────────────────────────────────

APP_DIR="/opt/sincitytravels"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_NAME="sincitytravels"
DB_USER="scapp"
DB_PASS="$(openssl rand -base64 18)"
APP_PORT=5050
NGINX_PORT=8888

echo "══════════════════════════════════════════════════"
echo "  Sin City Travels — EC2 Deployment"
echo "══════════════════════════════════════════════════"

# ─── 1. Install PostGIS ──────────────────────────────────────────────────────
echo ""
echo "► Step 1: Installing PostGIS..."
PG_VERSION=$(pg_config --version | grep -oP '\d+' | head -1)
apt-get update -qq
apt-get install -y -qq "postgresql-${PG_VERSION}-postgis-3" postgis python3-venv python3-pip > /dev/null

echo "  PostGIS installed for PostgreSQL ${PG_VERSION}"

# ─── 2. Create database and user ─────────────────────────────────────────────
echo ""
echo "► Step 2: Setting up database..."

# Create user if it doesn't exist
sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"

# Update password either way
sudo -u postgres psql -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"

# Create database if it doesn't exist
sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 || \
    sudo -u postgres createdb -O "${DB_USER}" "${DB_NAME}"

echo "  Database '${DB_NAME}' ready, user '${DB_USER}' configured"

# ─── 3. Initialize schema ────────────────────────────────────────────────────
echo ""
echo "► Step 3: Initializing schema..."
sudo -u postgres psql -d "${DB_NAME}" -f "${REPO_DIR}/k8s/init-db.sql"

echo "  Schema initialized with tables, indexes, and functions"

# ─── 4. Import POI data ──────────────────────────────────────────────────────
echo ""
echo "► Step 4: Importing POI data..."

# Temporarily set env vars for the import scripts
export DB_HOST=localhost
export DB_NAME="${DB_NAME}"
export DB_USER="${DB_USER}"
export DB_PASSWORD="${DB_PASS}"

cd "${REPO_DIR}"
pip3 install -q psycopg2-binary
python3 scripts/import_pois.py

echo ""
echo "► Step 4b: Generating synthetic navigation data..."
pip3 install -q numpy
python3 scripts/generate_synthetic_routes.py

# ─── 5. Set up application directory ─────────────────────────────────────────
echo ""
echo "► Step 5: Setting up application..."

mkdir -p "${APP_DIR}"
cp -r "${REPO_DIR}/demo/"* "${APP_DIR}/"

# Create virtual environment
python3 -m venv "${APP_DIR}/venv"
"${APP_DIR}/venv/bin/pip" install -q -r "${APP_DIR}/requirements.txt"

# ─── 6. Create environment file ──────────────────────────────────────────────
cat > "${APP_DIR}/.env" <<ENVEOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASS}
GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY:-}
ENVEOF

chmod 600 "${APP_DIR}/.env"
echo "  Environment file created at ${APP_DIR}/.env"

# ─── 7. Create log directory and logrotate ───────────────────────────────────
echo ""
echo "► Step 6: Setting up logging..."

mkdir -p /var/log/sincitytravels
chown www-data:www-data /var/log/sincitytravels

cat > /etc/logrotate.d/sincitytravels <<LOGEOF
/var/log/sincitytravels/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
LOGEOF

echo "  Log directory created, logrotate configured (14-day retention)"

# ─── 8. Create systemd service ───────────────────────────────────────────────
echo ""
echo "► Step 7: Creating systemd service..."

cat > /etc/systemd/system/sincitytravels.service <<SVCEOF
[Unit]
Description=Sin City Travels Demo
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/gunicorn \
    --bind 127.0.0.1:${APP_PORT} \
    --workers 2 \
    --threads 2 \
    --timeout 30 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile /var/log/sincitytravels/access.log \
    --error-logfile /var/log/sincitytravels/error.log \
    --access-logformat '%%(h)s %%(l)s %%(u)s %%(t)s "%%(r)s" %%(s)s %%(b)s "%%(f)s" "%%(a)s" %%(D)s' \
    app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

chown -R www-data:www-data "${APP_DIR}"

systemctl daemon-reload
systemctl enable sincitytravels
systemctl restart sincitytravels

echo "  Service 'sincitytravels' enabled and started on port ${APP_PORT}"

# ─── 9. Configure Nginx ──────────────────────────────────────────────────────
echo ""
echo "► Step 8: Configuring Nginx..."

cat > /etc/nginx/sites-available/sincitytravels <<NGXEOF
server {
    listen ${NGINX_PORT};
    server_name _;
    server_tokens off;

    # ─── Security headers ─────────────────────────────────────
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=(self)" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com; style-src 'self' 'unsafe-inline' https://unpkg.com https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://*.tile.openstreetmap.org https://unpkg.com; connect-src 'self';" always;

    # ─── Gzip compression ─────────────────────────────────────
    gzip on;
    gzip_types application/json application/javascript text/css text/plain;
    gzip_min_length 256;

    # ─── Request limits ───────────────────────────────────────
    client_max_body_size 16k;

    # ─── Proxy timeouts ──────────────────────────────────────
    proxy_connect_timeout 10;
    proxy_read_timeout 30;
    proxy_send_timeout 30;

    # ─── Block common attack paths ────────────────────────────
    location ~ /\.(env|git|htaccess|htpasswd) {
        return 404;
    }
    location ~ /(wp-admin|wp-login|phpmyadmin|admin|xmlrpc) {
        return 404;
    }

    # Sin City Travels demo
    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Static files served directly by Nginx
    location /static/ {
        alias ${APP_DIR}/static/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
NGXEOF

# Enable the site
ln -sf /etc/nginx/sites-available/sincitytravels /etc/nginx/sites-enabled/sincitytravels

# Disable default site if it exists (would conflict on port 80)
# Comment out the next line if you want to keep the default site
# rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl reload nginx

echo "  Nginx configured and reloaded"

# ─── 10. Database backup cron ─────────────────────────────────────────────────
echo ""
echo "► Step 9: Setting up database backups..."

cp "${REPO_DIR}/scripts/backup_db.sh" "${APP_DIR}/backup_db.sh"
chmod +x "${APP_DIR}/backup_db.sh"
mkdir -p /var/backups/sincitytravels

# Install cron job (daily at 3 AM UTC) — idempotent
CRON_JOB="0 3 * * * ${APP_DIR}/backup_db.sh"
( crontab -l 2>/dev/null | grep -v "backup_db.sh" ; echo "${CRON_JOB}" ) | crontab -

echo "  Backup script installed, cron job set for 3 AM UTC daily"

# ─── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════"
echo "  Deployment complete!"
echo ""
echo "  App URL:     http://$(curl -s ifconfig.me 2>/dev/null || echo '<your-ec2-ip>'):${NGINX_PORT}/"
echo "  DB Password: ${DB_PASS}"
echo "  Service:     sudo systemctl status sincitytravels"
echo "  Logs:        sudo journalctl -u sincitytravels -f"
echo "  Access log:  /var/log/sincitytravels/access.log"
echo "  Error log:   /var/log/sincitytravels/error.log"
echo "  Backups:     /var/backups/sincitytravels/"
echo ""
echo "  IMPORTANT: Save the DB password above!"
echo "  IMPORTANT: Make sure port ${NGINX_PORT} is open in your"
echo "             EC2 security group."
echo "══════════════════════════════════════════════════"
