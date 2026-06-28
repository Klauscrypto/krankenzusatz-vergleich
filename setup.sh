#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
#  setup.sh – krankenzusatz-vergleich.de
#  Hetzner Ubuntu 24.04 · Nginx · PHP 8.3 · MariaDB · WordPress
#  Idempotent: mehrfach ausführbar ohne Fehler
#
#  Verwendung:
#    bash setup.sh
#    REPO_URL=https://github.com/USER/REPO.git bash setup.sh
# ════════════════════════════════════════════════════════════════
set -euo pipefail

# ── KONFIGURATION ────────────────────────────────────────────────
DOMAIN="${DOMAIN:-krankenzusatz-vergleich.de}"
EMAIL="${EMAIL:-info@pilsner-vertrieb.de}"
REPO_URL="${REPO_URL:-}"          # optional: GitHub-Repo-URL für direktes Deployment
PHP_VER="8.3"

# Pfade (webroot muss mit deploy.yml übereinstimmen: target="/var/www/krankenzusatz-vergleich")
WEBROOT="/var/www/krankenzusatz-vergleich"
BLOG_DIR="${WEBROOT}/blog"
SCRIPTS_DIR="/var/www/scripts"
LOGS_DIR="/var/log/krankenzusatz"
CREDS_FILE="/root/.${DOMAIN}.env"
NGINX_CONF="/etc/nginx/sites-available/${DOMAIN}"
# ─────────────────────────────────────────────────────────────────

# ── FARBEN & HELPER ──────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[1;34m'; BOLD='\033[1m'; NC='\033[0m'
info()  { echo -e "\n${BLUE}${BOLD}▶ $*${NC}"; }
ok()    { echo -e "  ${GREEN}✓${NC} $*"; }
warn()  { echo -e "  ${YELLOW}⚠${NC}  $*"; }
skip()  { echo -e "  → übersprungen: $*"; }
die()   { echo -e "${RED}FEHLER: $*${NC}" >&2; exit 1; }
# ─────────────────────────────────────────────────────────────────

# ── VORAUSSETZUNGEN ──────────────────────────────────────────────
[[ $EUID -ne 0 ]] && die "Bitte als root ausführen: sudo bash setup.sh"
grep -q 'Ubuntu 24' /etc/os-release 2>/dev/null || warn "Nicht Ubuntu 24.04 – fortfahren auf eigene Gefahr"

echo -e "\n${BOLD}════════════════════════════════════════════${NC}"
echo -e "${BOLD}  krankenzusatz-vergleich.de · Server-Setup${NC}"
echo -e "${BOLD}════════════════════════════════════════════${NC}"
echo "  Domain:  ${DOMAIN}"
echo "  E-Mail:  ${EMAIL}"
echo "  PHP:     ${PHP_VER}"
echo "  Repo:    ${REPO_URL:-nicht gesetzt (GitHub Actions übernimmt Deployment)}"
echo ""

# ── CREDENTIALS LADEN / GENERIEREN ──────────────────────────────
info "Credentials prüfen..."
if [[ -f "$CREDS_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$CREDS_FILE"
    skip "Credentials geladen aus $CREDS_FILE"
else
    DB_NAME="krankenzusatz_db"
    DB_USER="wp_user"
    DB_PASS="$(openssl rand -base64 32 | tr -d '/+=')"
    DB_ROOT_PASS="$(openssl rand -base64 32 | tr -d '/+=')"
    install -m 600 /dev/null "$CREDS_FILE"
    cat > "$CREDS_FILE" <<EOF
# Generiert von setup.sh am $(date)
DB_NAME="${DB_NAME}"
DB_USER="${DB_USER}"
DB_PASS="${DB_PASS}"
DB_ROOT_PASS="${DB_ROOT_PASS}"
EOF
    ok "Neue Credentials generiert → $CREDS_FILE"
fi
# ─────────────────────────────────────────────────────────────────

# ── SYSTEM-UPDATE ────────────────────────────────────────────────
info "System aktualisieren..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    curl wget gnupg2 ca-certificates apt-transport-https \
    software-properties-common unzip git ufw fail2ban \
    lsb-release python3 python3-pip rsync
ok "Systempakete aktualisiert"
# ─────────────────────────────────────────────────────────────────

# ── NGINX ────────────────────────────────────────────────────────
info "Nginx prüfen / installieren..."
if ! command -v nginx &>/dev/null; then
    apt-get install -y -qq nginx
    systemctl enable nginx
    ok "Nginx installiert"
else
    skip "Nginx ($(nginx -v 2>&1 | cut -d/ -f2))"
fi
# ─────────────────────────────────────────────────────────────────

# ── PHP 8.3 ──────────────────────────────────────────────────────
info "PHP ${PHP_VER} prüfen / installieren..."
if ! command -v "php${PHP_VER}" &>/dev/null; then
    LC_ALL=C.UTF-8 add-apt-repository -y ppa:ondrej/php
    apt-get update -qq
    apt-get install -y -qq \
        "php${PHP_VER}-fpm"     \
        "php${PHP_VER}-mysql"   \
        "php${PHP_VER}-xml"     \
        "php${PHP_VER}-xmlrpc"  \
        "php${PHP_VER}-curl"    \
        "php${PHP_VER}-mbstring"\
        "php${PHP_VER}-zip"     \
        "php${PHP_VER}-gd"      \
        "php${PHP_VER}-intl"    \
        "php${PHP_VER}-bcmath"  \
        "php${PHP_VER}-opcache"
    systemctl enable "php${PHP_VER}-fpm"
    ok "PHP ${PHP_VER} installiert"
else
    skip "PHP ${PHP_VER}"
fi

# php.ini optimieren (sed ist idempotent)
PHP_INI="/etc/php/${PHP_VER}/fpm/php.ini"
sed -i 's/^upload_max_filesize\s*=.*/upload_max_filesize = 64M/'  "$PHP_INI"
sed -i 's/^post_max_size\s*=.*/post_max_size = 64M/'             "$PHP_INI"
sed -i 's/^memory_limit\s*=.*/memory_limit = 256M/'             "$PHP_INI"
sed -i 's/^max_execution_time\s*=.*/max_execution_time = 120/'   "$PHP_INI"
ok "PHP-Konfiguration optimiert"
# ─────────────────────────────────────────────────────────────────

# ── MARIADB ──────────────────────────────────────────────────────
info "MariaDB prüfen / installieren..."
if ! command -v mariadb &>/dev/null && ! command -v mysql &>/dev/null; then
    apt-get install -y -qq mariadb-server mariadb-client
    systemctl enable mariadb
    ok "MariaDB installiert"
else
    skip "MariaDB ($(mariadb --version 2>&1 | awk '{print $5}' | tr -d ','))"
fi

# Helper: SQL als root ausführen (socket-auth oder passwort-auth)
mysql_root() {
    if mysql -u root -p"${DB_ROOT_PASS}" -e "SELECT 1" &>/dev/null 2>&1; then
        mysql -u root -p"${DB_ROOT_PASS}" "$@"
    else
        mysql -u root "$@"
    fi
}

info "Datenbank einrichten..."
# Root-Passwort setzen wenn noch socket-auth aktiv
if ! mysql -u root -p"${DB_ROOT_PASS}" -e "SELECT 1" &>/dev/null 2>&1; then
    mysql -u root <<SQL 2>/dev/null || true
ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_ROOT_PASS}';
FLUSH PRIVILEGES;
SQL
    ok "MariaDB root-Passwort gesetzt"
fi

# Datenbank + User anlegen (IF NOT EXISTS = idempotent)
mysql_root <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost'
    IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
SQL
ok "Datenbank '${DB_NAME}' + User '${DB_USER}' konfiguriert"
# ─────────────────────────────────────────────────────────────────

# ── VERZEICHNISSTRUKTUR ──────────────────────────────────────────
info "Verzeichnisse anlegen..."
mkdir -p "${WEBROOT}/en"
mkdir -p "${BLOG_DIR}"
mkdir -p "${SCRIPTS_DIR}"
mkdir -p "${LOGS_DIR}"
chown -R www-data:www-data "${WEBROOT}"
ok "Webroot: ${WEBROOT}"
ok "Scripts: ${SCRIPTS_DIR}"
# ─────────────────────────────────────────────────────────────────

# ── LANDING PAGES DEPLOYEN ───────────────────────────────────────
info "Landing Pages deployen..."
if [[ -n "${REPO_URL}" ]]; then
    TMP_REPO="$(mktemp -d)"
    git clone --depth=1 "${REPO_URL}" "${TMP_REPO}"

    # Deutsche Startseite
    if [[ -f "${TMP_REPO}/public/index.html" ]]; then
        cp "${TMP_REPO}/public/index.html" "${WEBROOT}/index.html"
        ok "DE Landing Page → ${WEBROOT}/index.html"
    else
        warn "public/index.html nicht im Repo gefunden"
    fi

    # Englische Seite
    if [[ -f "${TMP_REPO}/public/en/index.html" ]]; then
        mkdir -p "${WEBROOT}/en"
        cp "${TMP_REPO}/public/en/index.html" "${WEBROOT}/en/index.html"
        ok "EN Landing Page → ${WEBROOT}/en/index.html"
    fi

    # CSS / JS Assets
    for asset in css js; do
        [[ -d "${TMP_REPO}/public/${asset}" ]] && \
            cp -r "${TMP_REPO}/public/${asset}" "${WEBROOT}/"
    done

    # Scripts deployen
    if [[ -d "${TMP_REPO}/scripts" ]]; then
        rsync -a "${TMP_REPO}/scripts/" "${SCRIPTS_DIR}/"
        chmod +x "${SCRIPTS_DIR}"/*.sh 2>/dev/null || true
        ok "Python-Scripts → ${SCRIPTS_DIR}"
    fi

    # WordPress-Theme deployen
    THEME_DEST="${BLOG_DIR}/wp-content/themes/krankenzusatz"
    if [[ -d "${TMP_REPO}/src/themes/krankenzusatz" ]]; then
        mkdir -p "${THEME_DEST}"
        rsync -a --delete "${TMP_REPO}/src/themes/krankenzusatz/" "${THEME_DEST}/"
        ok "WordPress-Theme → ${THEME_DEST}"
    fi

    rm -rf "${TMP_REPO}"
elif [[ -f "${WEBROOT}/index.html" ]]; then
    skip "Landing Pages (vorhanden – wird via GitHub Actions aktuell gehalten)"

    # Scripts + Theme mit deployen wenn im Repo-Kontext
    if [[ -d "${REPO_URL:-}" ]] || command -v git &>/dev/null; then : ; fi
else
    warn "REPO_URL nicht gesetzt – Platzhalter wird erstellt"
    cat > "${WEBROOT}/index.html" <<'HTML'
<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><title>krankenzusatz-vergleich.de</title></head>
<body>
  <h1>krankenzusatz-vergleich.de</h1>
  <p>Deployment via GitHub Actions folgt in Kürze.</p>
</body>
</html>
HTML
    mkdir -p "${WEBROOT}/en"
    sed 's/lang="de"/lang="en"/' "${WEBROOT}/index.html" > "${WEBROOT}/en/index.html"
fi
# ─────────────────────────────────────────────────────────────────

# ── WORDPRESS ────────────────────────────────────────────────────
info "WordPress prüfen / installieren..."
if [[ ! -f "${BLOG_DIR}/wp-includes/version.php" ]]; then
    curl -sL https://wordpress.org/latest.tar.gz | tar -xz -C /tmp
    rsync -a --delete /tmp/wordpress/ "${BLOG_DIR}/"
    rm -rf /tmp/wordpress

    # wp-config.php generieren
    cp "${BLOG_DIR}/wp-config-sample.php" "${BLOG_DIR}/wp-config.php"

    # Datenbank-Credentials
    sed -i "s/database_name_here/${DB_NAME}/"   "${BLOG_DIR}/wp-config.php"
    sed -i "s/username_here/${DB_USER}/"         "${BLOG_DIR}/wp-config.php"
    sed -i "s/password_here/${DB_PASS}/"         "${BLOG_DIR}/wp-config.php"

    # WordPress-URL für Subdirectory /blog/
    # Muss VOR dem "That's all, stop editing" Block stehen
    sed -i "/That's all, stop editing/i \\
\\
define('WP_HOME',           'https://${DOMAIN}/blog');\\
define('WP_SITEURL',        'https://${DOMAIN}/blog');\\
define('DISALLOW_FILE_EDIT', true);\\
define('WP_DEBUG',           false);\\
define('WP_DEBUG_LOG',       false);" \
        "${BLOG_DIR}/wp-config.php"

    # WordPress Security-Salts via API holen und einsetzen
    SALTS="$(curl -sL --max-time 10 https://api.wordpress.org/secret-key/1.1/salt/ 2>/dev/null || true)"
    if [[ -n "$SALTS" ]]; then
        python3 - "${BLOG_DIR}/wp-config.php" <<PYEOF
import sys, re
path = sys.argv[1]
with open(path) as f:
    content = f.read()
salts = """${SALTS}"""
content = re.sub(
    r"define\('AUTH_KEY'.*?define\('NONCE_SALT'[^\n]*\n",
    salts + "\n",
    content, flags=re.DOTALL
)
with open(path, 'w') as f:
    f.write(content)
PYEOF
        ok "WordPress Salts gesetzt"
    fi

    chown -R www-data:www-data "${BLOG_DIR}"
    chmod 640 "${BLOG_DIR}/wp-config.php"
    ok "WordPress installiert in ${BLOG_DIR}"
else
    skip "WordPress (bereits installiert)"
fi
# ─────────────────────────────────────────────────────────────────

# ── .ENV TEMPLATE FÜR ARTIKEL-GENERATOR ─────────────────────────
info "Python-Dependencies installieren..."
if [[ -f "${SCRIPTS_DIR}/requirements.txt" ]]; then
    pip3 install -q -r "${SCRIPTS_DIR}/requirements.txt"
    ok "Python-Packages installiert"
else
    pip3 install -q anthropic python-dotenv requests 2>/dev/null && ok "Python-Packages installiert" || \
        warn "pip3 install fehlgeschlagen – manuell ausführen"
fi

info "Artikel-Generator .env prüfen..."
ENV_FILE="${SCRIPTS_DIR}/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    install -m 600 /dev/null "$ENV_FILE"
    cat > "$ENV_FILE" <<EOF
# Artikel-Generator Umgebungsvariablen
# Ausgefüllt werden müssen: ANTHROPIC_API_KEY, WP_APP_PASSWORD
ANTHROPIC_API_KEY=sk-ant-...
WP_URL=https://${DOMAIN}
WP_USER=admin
WP_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASS=${DB_PASS}
EOF
    ok ".env Template erstellt → ${ENV_FILE}"
    warn "ANTHROPIC_API_KEY + WP_APP_PASSWORD noch eintragen!"
else
    skip ".env (bereits vorhanden)"
fi
# ─────────────────────────────────────────────────────────────────

# ── NGINX VHOST ──────────────────────────────────────────────────
info "Nginx-Konfiguration schreiben..."

# Rate-Limit Zone in nginx.conf (idempotent)
if ! grep -q 'wp_login' /etc/nginx/nginx.conf; then
    sed -i '/http {/a \\n\t# WordPress brute-force protection\n\tlimit_req_zone $binary_remote_addr zone=wp_login:10m rate=5r\/m;\n' \
        /etc/nginx/nginx.conf
fi

cat > "${NGINX_CONF}" <<NGINX
# krankenzusatz-vergleich.de
# Generiert von setup.sh – nicht manuell bearbeiten
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

    root   ${WEBROOT};
    index  index.html index.php;
    charset utf-8;

    # ── Logs ──────────────────────────────────────────────────
    access_log ${LOGS_DIR}/access.log;
    error_log  ${LOGS_DIR}/error.log warn;

    # ── Security Headers ──────────────────────────────────────
    add_header X-Frame-Options          "SAMEORIGIN"                      always;
    add_header X-Content-Type-Options   "nosniff"                         always;
    add_header Referrer-Policy          "strict-origin-when-cross-origin" always;
    add_header X-XSS-Protection         "1; mode=block"                   always;

    # ── Gzip ──────────────────────────────────────────────────
    gzip            on;
    gzip_vary       on;
    gzip_min_length 1024;
    gzip_types      text/plain text/css application/json
                    application/javascript text/xml application/xml
                    image/svg+xml application/font-woff2;

    # ── Statische Assets mit langem Cache ─────────────────────
    location ~* \.(css|js|ico|png|jpg|jpeg|gif|webp|svg|woff2?|ttf|eot)$ {
        expires    30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # ── Deutsche Startseite & statische Seiten ────────────────
    location / {
        try_files \$uri \$uri/ =404;
    }

    # ── Englische Expat-Version ───────────────────────────────
    location /en/ {
        try_files \$uri \$uri/index.html =404;
    }

    # ── WordPress /blog/ ──────────────────────────────────────
    location ^~ /blog {
        index index.php;
        try_files \$uri \$uri/ /blog/index.php?\$args;
    }

    location ~ ^/blog/.*\.php$ {
        fastcgi_pass         unix:/run/php/php${PHP_VER}-fpm.sock;
        fastcgi_index        index.php;
        include              fastcgi_params;
        fastcgi_param        SCRIPT_FILENAME \${document_root}\$fastcgi_script_name;
        fastcgi_read_timeout 120;
    }

    # wp-login Brute-Force-Schutz
    location = /blog/wp-login.php {
        limit_req zone=wp_login burst=5 nodelay;
        fastcgi_pass  unix:/run/php/php${PHP_VER}-fpm.sock;
        include       fastcgi_params;
        fastcgi_param SCRIPT_FILENAME \${document_root}\$fastcgi_script_name;
    }

    # ── Sicherheits-Sperren ───────────────────────────────────
    location ~ /\.                          { deny all; access_log off; }
    location = /blog/wp-config.php          { deny all; }
    location ~* /(?:uploads|files)/.*\.php$ { deny all; }
    location ~* \.(sql|bak|log|sh|env)$    { deny all; }
}
NGINX

# Site aktivieren + default deaktivieren
ln -sf "${NGINX_CONF}" "/etc/nginx/sites-enabled/${DOMAIN}"
rm -f /etc/nginx/sites-enabled/default

# Config validieren
nginx -t
ok "Nginx-Konfiguration geschrieben und validiert"
# ─────────────────────────────────────────────────────────────────

# ── CERTBOT / SSL ────────────────────────────────────────────────
info "SSL-Zertifikat prüfen / ausstellen..."
if ! command -v certbot &>/dev/null; then
    apt-get install -y -qq certbot python3-certbot-nginx
    ok "Certbot installiert"
else
    skip "Certbot"
fi

if [[ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]]; then
    warn "DNS muss auf diese Server-IP zeigen bevor Certbot läuft!"
    certbot --nginx               \
        --non-interactive         \
        --agree-tos               \
        --email "${EMAIL}"        \
        -d "${DOMAIN}"            \
        -d "www.${DOMAIN}"        \
        --redirect                \
        --staple-ocsp
    ok "SSL-Zertifikat ausgestellt + HTTP→HTTPS Redirect aktiv"
else
    certbot renew --quiet --nginx
    skip "SSL-Zertifikat (vorhanden, Renewal geprüft)"
fi

# Auto-Renewal Cron (idempotent: alte Einträge erst entfernen)
CRON_JOB="0 3 * * * /usr/bin/certbot renew --quiet --nginx"
( crontab -l 2>/dev/null | grep -v 'certbot renew'; echo "$CRON_JOB" ) | crontab -
ok "Certbot Auto-Renewal Cron gesetzt (täglich 03:00 Uhr)"
# ─────────────────────────────────────────────────────────────────

# ── CRONJOBS ARTIKEL-GENERATOR ───────────────────────────────────
info "Artikel-Generator Cronjobs einrichten..."
CRON_GENERATOR_DE="/usr/bin/python3 ${SCRIPTS_DIR}/artikel-generator.py --lang=de 2>>${LOGS_DIR}/generator.log"
CRON_GENERATOR_EN="/usr/bin/python3 ${SCRIPTS_DIR}/artikel-generator.py --lang=en 2>>${LOGS_DIR}/generator.log"

if [[ ! -f "${SCRIPTS_DIR}/artikel-generator.py" ]]; then
    warn "artikel-generator.py existiert noch nicht – Cronjobs werden vorbereitet aber erst nach Aufgabe 5 aktiv"
fi

# Cron-Einträge (idempotent: erst entfernen, dann neu setzen)
( crontab -l 2>/dev/null | grep -v 'artikel-generator'; \
  echo "0  8  * * * ${CRON_GENERATOR_DE}"; \
  echo "30 8  * * * ${CRON_GENERATOR_EN}"; \
  echo "0  13 * * * ${CRON_GENERATOR_DE}"; \
  echo "30 13 * * * ${CRON_GENERATOR_EN}"; \
  echo "0  18 * * * ${CRON_GENERATOR_DE}"; \
  echo "30 18 * * * ${CRON_GENERATOR_EN}" \
) | crontab -
ok "6 Cronjobs eingetragen (08:00, 13:00, 18:00 · DE + EN)"
# ─────────────────────────────────────────────────────────────────

# ── UFW FIREWALL ─────────────────────────────────────────────────
info "Firewall konfigurieren..."
ufw --force enable
ufw allow ssh
ufw allow 'Nginx Full'
ufw delete allow 'Nginx HTTP' 2>/dev/null || true
ok "UFW aktiv: SSH + HTTP/HTTPS freigegeben"
# ─────────────────────────────────────────────────────────────────

# ── DATEIRECHTE ──────────────────────────────────────────────────
info "Dateirechte setzen..."
chown -R www-data:www-data "${WEBROOT}"
find "${WEBROOT}" -type d -exec chmod 755 {} \;
find "${WEBROOT}" -type f -exec chmod 644 {} \;
# wp-config.php extra restriktiv
[[ -f "${BLOG_DIR}/wp-config.php" ]] && chmod 640 "${BLOG_DIR}/wp-config.php"
ok "Rechte: 755 Verzeichnisse · 644 Dateien · 640 wp-config.php"
# ─────────────────────────────────────────────────────────────────

# ── DIENSTE NEU STARTEN ──────────────────────────────────────────
info "Alle Dienste neu starten..."
systemctl restart mariadb "php${PHP_VER}-fpm" nginx
ok "MariaDB, PHP ${PHP_VER}-FPM, Nginx – alle gestartet"
# ─────────────────────────────────────────────────────────────────

# ── FAIL2BAN ─────────────────────────────────────────────────────
info "Fail2Ban konfigurieren..."
if [[ ! -f /etc/fail2ban/jail.d/nginx-wp.conf ]]; then
    cat > /etc/fail2ban/jail.d/nginx-wp.conf <<'F2B'
[nginx-http-auth]
enabled = true

[wordpress]
enabled  = true
filter   = wordpress
logpath  = /var/log/krankenzusatz/access.log
maxretry = 5
bantime  = 3600
F2B
    systemctl restart fail2ban
    ok "Fail2Ban konfiguriert"
else
    skip "Fail2Ban (bereits konfiguriert)"
fi
# ─────────────────────────────────────────────────────────────────

# ── STATUS-CHECK ─────────────────────────────────────────────────
info "Service-Status prüfen..."
for svc in nginx mariadb "php${PHP_VER}-fpm" fail2ban; do
    if systemctl is-active --quiet "$svc"; then
        ok "$svc läuft"
    else
        warn "$svc ist NICHT aktiv – prüfe: systemctl status $svc"
    fi
done
# ─────────────────────────────────────────────────────────────────

# ── ABSCHLUSS-REPORT ─────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Setup erfolgreich abgeschlossen!${NC}"
echo -e "${GREEN}${BOLD}════════════════════════════════════════════${NC}"
echo ""
echo "  URLs:"
echo "    DE-Seite   → https://${DOMAIN}/"
echo "    EN-Seite   → https://${DOMAIN}/en/"
echo "    WP-Admin   → https://${DOMAIN}/blog/wp-admin/"
echo ""
echo "  Credentials:  sudo cat ${CREDS_FILE}"
echo "  Generator:    ${SCRIPTS_DIR}/.env  (ANTHROPIC_API_KEY eintragen!)"
echo "  Logs:         ${LOGS_DIR}/"
echo ""
echo "  Nächste Schritte:"
echo "    1. GitHub Secrets setzen: SERVER_HOST + SERVER_SSH_KEY"
echo "    2. WordPress einrichten:  https://${DOMAIN}/blog/wp-admin/"
echo "    3. ANTHROPIC_API_KEY in  ${SCRIPTS_DIR}/.env eintragen"
echo "    4. Aufgabe 5: artikel-generator.py schreiben"
echo "    5. Aufgabe 6: publish-artikel.py schreiben"
echo ""
