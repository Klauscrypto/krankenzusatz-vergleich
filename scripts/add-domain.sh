#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
#  add-domain.sh – Aufgabe 8: Neue Domain auf Hetzner-Server hinzufügen
#  Erstellt Nginx-Vhost, Webroot, SSL-Zertifikat
#  Idempotent: mehrfach ausführbar
#
#  Verwendung:
#    bash add-domain.sh neue-domain.de admin@example.com
#    bash add-domain.sh neue-domain.de admin@example.com --with-wp
# ════════════════════════════════════════════════════════════════
set -euo pipefail

# ── ARGUMENTE ────────────────────────────────────────────────────
DOMAIN="${1:-}"
EMAIL="${2:-info@pilsner-vertrieb.de}"
WITH_WP="${3:-}"          # "--with-wp" für WordPress-Installation
PHP_VER="8.3"

if [[ -z "$DOMAIN" ]]; then
    echo "Verwendung: bash add-domain.sh DOMAIN [EMAIL] [--with-wp]"
    echo "Beispiel:   bash add-domain.sh meine-neue-domain.de info@beispiel.de"
    exit 1
fi

[[ $EUID -ne 0 ]] && { echo "Bitte als root ausführen."; exit 1; }

# ── KONFIGURATION ────────────────────────────────────────────────
WEBROOT="/var/www/${DOMAIN}"
BLOG_DIR="${WEBROOT}/blog"
NGINX_CONF="/etc/nginx/sites-available/${DOMAIN}"
CREDS_FILE="/root/.${DOMAIN}.env"
LOGS_DIR="/var/log/${DOMAIN}"

GREEN='\033[0;32m'; BLUE='\033[1;34m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
info() { echo -e "\n${BLUE}${BOLD}▶ $*${NC}"; }
ok()   { echo -e "  ${GREEN}✓${NC} $*"; }
skip() { echo -e "  → übersprungen: $*"; }
warn() { echo -e "  ${YELLOW}⚠${NC}  $*"; }

echo -e "\n${BOLD}Neue Domain: ${DOMAIN}${NC}"
echo "  Webroot: ${WEBROOT}"
echo "  SSL:     Let's Encrypt · ${EMAIL}"
[[ "$WITH_WP" == "--with-wp" ]] && echo "  WordPress: wird installiert"
echo ""

# ── CREDENTIALS ──────────────────────────────────────────────────
info "Credentials..."
if [[ -f "$CREDS_FILE" ]]; then
    source "$CREDS_FILE"
    skip "Credentials ($CREDS_FILE)"
else
    DB_NAME="$(echo "${DOMAIN}" | tr '.-' '_')"
    DB_USER="${DB_NAME}_user"
    DB_PASS="$(openssl rand -base64 24 | tr -d '/+=')"
    DB_ROOT_PASS="$(cat /root/.krankenzusatz-vergleich.de.env 2>/dev/null | grep DB_ROOT_PASS | cut -d= -f2 || openssl rand -base64 24)"

    install -m 600 /dev/null "$CREDS_FILE"
    cat > "$CREDS_FILE" <<EOF
DB_NAME="${DB_NAME}"
DB_USER="${DB_USER}"
DB_PASS="${DB_PASS}"
DB_ROOT_PASS="${DB_ROOT_PASS}"
EOF
    ok "Credentials → $CREDS_FILE"
fi

# ── VERZEICHNISSE ────────────────────────────────────────────────
info "Verzeichnisse anlegen..."
mkdir -p "${WEBROOT}" "${LOGS_DIR}"
[[ "$WITH_WP" == "--with-wp" ]] && mkdir -p "${BLOG_DIR}"
chown -R www-data:www-data "${WEBROOT}"
ok "Webroot: ${WEBROOT}"

# ── PLATZHALTER-INDEX ────────────────────────────────────────────
if [[ ! -f "${WEBROOT}/index.html" ]]; then
    cat > "${WEBROOT}/index.html" <<HTML
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${DOMAIN} – Coming Soon</title>
  <style>
    body { font-family: system-ui, sans-serif; display:flex; align-items:center;
           justify-content:center; min-height:100vh; margin:0; background:#f7f9fc; }
    .box { text-align:center; padding:40px; }
    h1 { color:#0057ff; font-size:2rem; }
    p  { color:#6b7f94; }
  </style>
</head>
<body>
  <div class="box">
    <h1>${DOMAIN}</h1>
    <p>Website in Kürze verfügbar.</p>
  </div>
</body>
</html>
HTML
    ok "Platzhalter-Index erstellt"
fi

# ── DATENBANK (optional für WordPress) ───────────────────────────
if [[ "$WITH_WP" == "--with-wp" ]]; then
    info "Datenbank für WordPress..."
    mysql_root() {
        if mysql -u root -p"${DB_ROOT_PASS}" -e "SELECT 1" &>/dev/null 2>&1; then
            mysql -u root -p"${DB_ROOT_PASS}" "$@"
        else
            mysql -u root "$@"
        fi
    }
    mysql_root <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost'
    IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
SQL
    ok "Datenbank '${DB_NAME}' eingerichtet"

    # WordPress installieren
    if [[ ! -f "${BLOG_DIR}/wp-includes/version.php" ]]; then
        curl -sL https://wordpress.org/latest.tar.gz | tar -xz -C /tmp
        rsync -a --delete /tmp/wordpress/ "${BLOG_DIR}/"
        rm -rf /tmp/wordpress

        cp "${BLOG_DIR}/wp-config-sample.php" "${BLOG_DIR}/wp-config.php"
        sed -i "s/database_name_here/${DB_NAME}/" "${BLOG_DIR}/wp-config.php"
        sed -i "s/username_here/${DB_USER}/"      "${BLOG_DIR}/wp-config.php"
        sed -i "s/password_here/${DB_PASS}/"      "${BLOG_DIR}/wp-config.php"
        sed -i "/That's all, stop editing/i define('WP_HOME','https://${DOMAIN}/blog');\ndefine('WP_SITEURL','https://${DOMAIN}/blog');" \
            "${BLOG_DIR}/wp-config.php"

        chown -R www-data:www-data "${BLOG_DIR}"
        chmod 640 "${BLOG_DIR}/wp-config.php"
        ok "WordPress installiert"
    else
        skip "WordPress (bereits vorhanden)"
    fi
fi

# ── NGINX VHOST ──────────────────────────────────────────────────
info "Nginx-Konfiguration..."
cat > "${NGINX_CONF}" <<NGINX
# ${DOMAIN} – generiert von add-domain.sh
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

    root   ${WEBROOT};
    index  index.html index.php;
    charset utf-8;

    access_log ${LOGS_DIR}/access.log;
    error_log  ${LOGS_DIR}/error.log warn;

    add_header X-Frame-Options        "SAMEORIGIN"                      always;
    add_header X-Content-Type-Options "nosniff"                         always;
    add_header Referrer-Policy        "strict-origin-when-cross-origin" always;

    gzip on; gzip_vary on; gzip_min_length 1024;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;

    location ~* \.(css|js|ico|png|jpg|jpeg|gif|webp|svg|woff2?)$ {
        expires 30d; add_header Cache-Control "public, immutable"; access_log off;
    }

    location / {
        try_files \$uri \$uri/ =404;
    }

$(if [[ "$WITH_WP" == "--with-wp" ]]; then cat <<WP
    location ^~ /blog {
        index index.php;
        try_files \$uri \$uri/ /blog/index.php?\$args;
    }

    location ~ ^/blog/.*\.php$ {
        fastcgi_pass  unix:/run/php/php${PHP_VER}-fpm.sock;
        fastcgi_index index.php;
        include       fastcgi_params;
        fastcgi_param SCRIPT_FILENAME \${document_root}\$fastcgi_script_name;
        fastcgi_read_timeout 120;
    }

    location = /blog/wp-login.php {
        limit_req zone=wp_login burst=5 nodelay;
        fastcgi_pass  unix:/run/php/php${PHP_VER}-fpm.sock;
        include       fastcgi_params;
        fastcgi_param SCRIPT_FILENAME \${document_root}\$fastcgi_script_name;
    }
WP
fi)
    location ~ /\.                { deny all; }
    location ~* \.(sql|bak|env)$ { deny all; }
}
NGINX

ln -sf "${NGINX_CONF}" "/etc/nginx/sites-enabled/${DOMAIN}"
nginx -t
systemctl reload nginx
ok "Nginx-Vhost aktiviert"

# ── CERTBOT SSL ──────────────────────────────────────────────────
info "SSL-Zertifikat..."
if [[ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]]; then
    warn "DNS muss auf diese IP zeigen!"
    certbot --nginx --non-interactive --agree-tos \
        --email "${EMAIL}" \
        -d "${DOMAIN}" -d "www.${DOMAIN}" \
        --redirect
    ok "SSL-Zertifikat ausgestellt"
else
    skip "SSL-Zertifikat (bereits vorhanden)"
fi

# ── DATEIRECHTE ──────────────────────────────────────────────────
chown -R www-data:www-data "${WEBROOT}"
find "${WEBROOT}" -type d -exec chmod 755 {} \;
find "${WEBROOT}" -type f -exec chmod 644 {} \;
[[ -f "${BLOG_DIR}/wp-config.php" ]] && chmod 640 "${BLOG_DIR}/wp-config.php"

# ── ABSCHLUSS ────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Domain ${DOMAIN} eingerichtet!${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════${NC}"
echo ""
echo "  Website:   https://${DOMAIN}/"
[[ "$WITH_WP" == "--with-wp" ]] && echo "  WordPress: https://${DOMAIN}/blog/wp-admin/"
echo "  Webroot:   ${WEBROOT}"
echo "  Logs:      ${LOGS_DIR}/"
echo ""
echo "  Nächste Schritte:"
echo "    1. DNS A-Record → $(curl -s ifconfig.me 2>/dev/null || echo 'DEINE-SERVER-IP')"
echo "    2. Inhalte nach ${WEBROOT}/ deployen"
[[ "$WITH_WP" == "--with-wp" ]] && echo "    3. WordPress: https://${DOMAIN}/blog/wp-admin/ einrichten"
echo ""
