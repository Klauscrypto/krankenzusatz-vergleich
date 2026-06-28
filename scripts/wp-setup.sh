#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
#  wp-setup.sh – WordPress per WP-CLI konfigurieren
#  Aufgabe 4: Kategorien, Theme, REST API, App-Passwort, Plugins
#  Idempotent: mehrfach ausführbar
# ════════════════════════════════════════════════════════════════
set -euo pipefail

DOMAIN="${DOMAIN:-krankenzusatz-vergleich.de}"
BLOG_DIR="/var/www/krankenzusatz-vergleich/blog"
THEME_DIR="${BLOG_DIR}/wp-content/themes/krankenzusatz"
SCRIPTS_DIR="/var/www/scripts"

# ── FARBEN ──────────────────────────────────────────────────────
GREEN='\033[0;32m'; BLUE='\033[1;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
info() { echo -e "\n${BLUE}▶ $*${NC}"; }
ok()   { echo -e "  ${GREEN}✓${NC} $*"; }
skip() { echo -e "  → übersprungen: $*"; }
warn() { echo -e "  ${YELLOW}⚠${NC}  $*"; }

[[ $EUID -ne 0 ]] && { echo "Bitte als root ausführen."; exit 1; }

# ── WP-CLI INSTALLIEREN ─────────────────────────────────────────
info "WP-CLI prüfen / installieren..."
if ! command -v wp &>/dev/null; then
    curl -sL https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar \
        -o /usr/local/bin/wp
    chmod +x /usr/local/bin/wp
    ok "WP-CLI installiert ($(wp --version --allow-root))"
else
    skip "WP-CLI ($(wp --version --allow-root))"
fi

WP="wp --path=${BLOG_DIR} --allow-root"

# ── WORDPRESS FERTIG INSTALLIEREN ───────────────────────────────
info "WordPress-Core konfigurieren..."
if ! $WP core is-installed 2>/dev/null; then
    warn "WordPress noch nicht über Browser installiert."
    warn "Bitte WordPress-Setup über /blog/wp-admin/ abschließen und dann dieses Script nochmal starten."
    warn "ODER: automatische CLI-Installation:"
    echo ""
    echo "  wp core install \\"
    echo "    --path=${BLOG_DIR} \\"
    echo "    --url=https://${DOMAIN}/blog \\"
    echo "    --title='Krankenzusatzversicherung Blog' \\"
    echo "    --admin_user=admin \\"
    echo "    --admin_password=SICHERES_PASSWORT \\"
    echo "    --admin_email=info@pilsner-vertrieb.de \\"
    echo "    --allow-root"
    echo ""
    exit 0
fi
ok "WordPress ist installiert"

# ── SPRACHEN ────────────────────────────────────────────────────
info "Sprachpakete installieren..."
$WP language core install de_DE --activate 2>/dev/null || skip "de_DE bereits aktiv"
$WP language core install en_US 2>/dev/null || skip "en_US bereits vorhanden"

# ── PERMALINKS ──────────────────────────────────────────────────
info "Permalink-Struktur setzen..."
$WP rewrite structure '/%category%/%postname%/' --hard
$WP rewrite flush --hard
ok "Permalinks: /%category%/%postname%/"

# ── KATEGORIEN (DE) ─────────────────────────────────────────────
info "Blog-Kategorien einrichten..."
declare -A CATS_DE=(
    ["zahnzusatz"]="Zahnzusatzversicherung"
    ["krankenhaus"]="Krankenhausversicherung"
    ["auslandsreise"]="Auslandsreisekrankenversicherung"
    ["heilpraktiker"]="Heilpraktiker & Alternativmedizin"
    ["sehhilfen"]="Sehhilfen & Brillenversicherung"
    ["vorsorge"]="Vorsorge & Gesundheit"
    ["expat-guide"]="Expat Guide"
    ["gkv-ratgeber"]="GKV Ratgeber"
)

for slug in "${!CATS_DE[@]}"; do
    name="${CATS_DE[$slug]}"
    if ! $WP term get category --by=slug "${slug}" --field=term_id &>/dev/null; then
        $WP term create category "${name}" --slug="${slug}" --porcelain
        ok "Kategorie erstellt: ${name}"
    else
        skip "Kategorie: ${name}"
    fi
done

# Default-Kategorie umbenennen
$WP term update category 1 --name="Allgemein" --slug="allgemein" 2>/dev/null || true

# ── TAGS VORBEREITEN ────────────────────────────────────────────
info "Basis-Tags erstellen..."
TAGS=(
    "Krankenzusatzversicherung" "Zahnzusatz" "GKV" "Zusatzversicherung"
    "Krankenhaus" "Chefarzt" "Heilpraktiker" "Auslandsreise"
    "Zahnersatz" "Kieferorthopädie" "Brille" "Kontaktlinsen"
    "Expat" "Deutschland" "Versicherungsvergleich" "Tarife 2026"
)
for tag in "${TAGS[@]}"; do
    $WP term create post_tag "${tag}" --porcelain 2>/dev/null || true
done
ok "Tags erstellt"

# ── CUSTOM THEME DEPLOYEN ───────────────────────────────────────
info "Custom Theme deployen..."
REPO_THEME_SRC="/var/www/scripts/theme-src"  # Quelle wenn via SCP deployed

# Theme aus Repo (wenn scripts/theme/ vorhanden ist)
if [[ -d "${SCRIPTS_DIR}/theme" ]]; then
    rsync -a --delete "${SCRIPTS_DIR}/theme/" "${THEME_DIR}/"
    ok "Theme aus Scripts-Verzeichnis kopiert"
fi

# Theme aktivieren wenn vorhanden
if [[ -d "${THEME_DIR}" ]]; then
    $WP theme activate krankenzusatz 2>/dev/null && ok "Custom Theme 'krankenzusatz' aktiviert" || \
        warn "Theme noch nicht vorhanden – bitte src/themes/krankenzusatz/ deployen"
else
    warn "Custom Theme noch nicht deployt – Twenty Twenty-Four wird verwendet"
    $WP theme install twentytwentyfour --activate 2>/dev/null || true
fi

# ── PLUGINS ─────────────────────────────────────────────────────
info "Empfohlene Plugins installieren..."

declare -A PLUGINS=(
    ["wordpress-seo"]="Yoast SEO"
    ["polylang"]="Polylang (Mehrsprachigkeit)"
    ["wordfence"]="Wordfence Security"
    ["wp-super-cache"]="WP Super Cache"
    ["cookie-notice"]="Cookie Notice (DSGVO)"
    ["classic-editor"]="Classic Editor (für REST API Kompatibilität)"
)

for plugin_slug in "${!PLUGINS[@]}"; do
    plugin_name="${PLUGINS[$plugin_slug]}"
    if ! $WP plugin is-installed "${plugin_slug}" 2>/dev/null; then
        $WP plugin install "${plugin_slug}" --activate 2>/dev/null && \
            ok "Plugin installiert: ${plugin_name}" || \
            warn "Plugin nicht gefunden: ${plugin_name} (manuell installieren)"
    else
        $WP plugin activate "${plugin_slug}" 2>/dev/null || true
        skip "Plugin: ${plugin_name}"
    fi
done

# ── APPLICATION PASSWORD FÜR REST API ───────────────────────────
info "Application Password für Artikel-Generator erstellen..."
APP_PASS_NAME="Artikel-Generator"
ENV_FILE="${SCRIPTS_DIR}/.env"

# Prüfen ob App-Passwort schon in .env eingetragen
if grep -q 'WP_APP_PASSWORD=xxxx' "${ENV_FILE}" 2>/dev/null; then
    # Neues App-Passwort generieren
    APP_PASS=$($WP user application-password create admin "${APP_PASS_NAME}" \
        --porcelain 2>/dev/null || echo "")

    if [[ -n "$APP_PASS" ]]; then
        # In .env eintragen
        sed -i "s/WP_APP_PASSWORD=.*/WP_APP_PASSWORD=${APP_PASS}/" "${ENV_FILE}"
        ok "App-Passwort generiert und in .env gespeichert"
    else
        warn "Kein App-Passwort generiert – manuell in WordPress Admin → Benutzer → Profil"
    fi
else
    skip "App-Passwort (bereits in .env eingetragen)"
fi

# ── WORDPRESS EINSTELLUNGEN ─────────────────────────────────────
info "WordPress-Optionen konfigurieren..."
$WP option update blogname "Krankenzusatzversicherung Blog"
$WP option update blogdescription "Täglich neue Ratgeber zu Krankenzusatzversicherungen"
$WP option update timezone_string "Europe/Berlin"
$WP option update date_format "d. F Y"
$WP option update time_format "H:i"
$WP option update default_comment_status "closed"
$WP option update comment_registration "1"
$WP option update default_pingback_flag "0"
$WP option update ping_sites ""
ok "WordPress-Optionen gesetzt"

# REST API für Artikel-Generator freischalten
$WP option update rest_api_enabled "1" 2>/dev/null || true

# ── STATISCHE SEITEN ERSTELLEN ──────────────────────────────────
info "Pflichtseiten erstellen..."

create_page_if_missing() {
    local title="$1"
    local slug="$2"
    local content="$3"
    if ! $WP post list --post_type=page --post_name="${slug}" --field=ID 2>/dev/null | grep -q .; then
        $WP post create \
            --post_type=page \
            --post_title="${title}" \
            --post_name="${slug}" \
            --post_status=publish \
            --post_content="${content}" \
            --porcelain
        ok "Seite erstellt: ${title}"
    else
        skip "Seite: ${title}"
    fi
}

create_page_if_missing "Impressum" "impressum" \
    "<p><strong>Angaben gemäß § 5 TMG:</strong></p><p>Klaus Pilsner<br>E-Mail: info@pilsner-vertrieb.de</p>"

create_page_if_missing "Datenschutz" "datenschutz" \
    "<p>Datenschutzerklärung gemäß DSGVO. Diese Seite bitte vollständig ausfüllen.</p>"

create_page_if_missing "Über uns" "ueber-uns" \
    "<p>krankenzusatz-vergleich.de ist ein unabhängiges Vergleichsportal für Krankenzusatzversicherungen.</p>"

# ── ABSCHLUSS ───────────────────────────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  WordPress-Setup abgeschlossen!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "  Admin:   https://${DOMAIN}/blog/wp-admin/"
echo "  Blog:    https://${DOMAIN}/blog/"
echo ""
echo "  Nächste Schritte:"
echo "    - Polylang: Sprachen DE + EN konfigurieren"
echo "    - Yoast SEO: Site-Konfiguration abschließen"
echo "    - App-Passwort in ${SCRIPTS_DIR}/.env prüfen"
echo ""
