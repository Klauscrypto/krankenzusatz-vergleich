# Projekt: krankenzusatz-vergleich.de – Hetzner Server Setup

## ✅ Bereits erledigt (Stand 28.06.2026)
- Hetzner CPX22 Server läuft auf **167.233.195.51** (Ubuntu 26.04)
- SSH-Zugang funktioniert: `ssh root@167.233.195.51`
- Nginx installiert und konfiguriert (`/etc/nginx/sites-available/krankenzusatz-vergleich`)
- Node.js, npm, git, certbot installiert
- **SSL aktiv**: https://krankenzusatz-vergleich.de (Let's Encrypt, läuft bis 26.09.2026)
- DNS: A-Record @ und www zeigen auf 167.233.195.51
- GitHub Repo: https://github.com/Klauscrypto/krankenzusatz-vergleich
- GitHub Actions Deploy eingerichtet: `git push` → automatisch live
- GitHub Secrets gesetzt: `SERVER_HOST`, `SERVER_SSH_KEY`
- Web-Root auf Server: `/var/www/krankenzusatz-vergleich/`
- Erste index.html, style.css, main.js deployed

## Nächste Schritte (noch offen)

---

## Ziel
Vollautomatische SEO-Website für Krankenzusatzversicherungen auf einem Hetzner VPS.
- Landingpages DE + EN bereits fertig als HTML
- Tägliche automatische Blog-Artikel (3x/Tag) via Claude API + Cronjob
- Mehrere Domains auf demselben Server
- WordPress als CMS für den Blog-Bereich

## Server
- Anbieter: Hetzner Cloud
- Empfohlener Typ: CPX22 (3 vCPU, 4 GB RAM, ~6 €/Monat)
- OS: Ubuntu 24.04 LTS
- Stack: Nginx + PHP 8.3 + MariaDB + WordPress + SSL (Let's Encrypt)

## Domains auf diesem Server
- krankenzusatz-vergleich.de (Hauptdomain, DE)
- krankenzusatz-vergleich.de/en/ (Englische Expat-Version)
- [weitere Domains eintragen]

## Dateistruktur (geplant)
```
/var/www/
├── krankenzusatz-vergleich.de/
│   ├── public/
│   │   ├── index.html          ← Deutsche Landingpage (bereits fertig)
│   │   ├── en/
│   │   │   └── index.html      ← Englische Landingpage (bereits fertig)
│   │   └── blog/               ← WordPress Blog
│   └── logs/
├── [weitere-domain].de/
│   └── public/
└── scripts/
    ├── artikel-generator.py    ← Claude API Artikel-Generator
    └── publish-artikel.py      ← WordPress REST API Publisher
```

## Bereits fertige Dateien (im Projektordner)
- `krankenzusatz-vergleich.html` → Deutsche Landingpage, direkt deploybar
- `krankenzusatz-vergleich-en.html` → Englische Expat-Landingpage, direkt deploybar

## Automatischer Artikel-Generator
- Läuft via Cronjob: 3x täglich (08:00, 13:00, 18:00 Uhr)
- Sprachen: Deutsch + Englisch (je 1,5 Artikel pro Slot)
- Tool: Python-Script → Claude API (claude-sonnet-4-6) → WordPress REST API
- Themen-Pool: Krankenzusatzversicherung, Zahnzusatz, Krankenhaus, Heilpraktiker, GKV-Lücken, Expat-Guide
- SEO: Jeder Artikel bekommt automatisch Title, Meta Description, Slug, Kategorie, Tags

## Aufgaben für Claude Code (der Reihe nach)
1. Hetzner VPS einrichten (Nginx, PHP, MariaDB, WordPress)
2. SSL-Zertifikate für alle Domains (Let's Encrypt / Certbot)
3. Landingpages deployen (HTML-Dateien aus Projektordner)
4. WordPress für /blog/ konfigurieren
5. artikel-generator.py schreiben (Claude API Integration)
6. publish-artikel.py schreiben (WordPress REST API)
7. Cronjob einrichten (3x täglich)
8. Nginx Multi-Domain Konfiguration für weitere Domains

## WordPress Konfiguration
- Blog-URL: krankenzusatz-vergleich.de/blog/
- Sprachen: DE (Hauptsprache) + EN (/en/blog/)
- Plugin: WPML oder Polylang für Mehrsprachigkeit
- REST API: aktiviert für automatische Veröffentlichung
- Theme: Minimales Custom Theme das zum Landingpage-Design passt

## Design-System (aus den Landingpages)
- Primärfarbe DE: #0057ff
- Teal Akzent EN: #00a8b5
- Hintergrund: #f5f8fc
- Font: Inter / system-ui
- Border-radius: 12px
- Landingpage-Stil soll sich ins WordPress-Theme fortsetzen

## Claude API Artikel-Generator – Anforderungen
- Model: claude-sonnet-4-6
- Max tokens: 2000 pro Artikel
- Artikel-Länge: 800–1200 Wörter
- Format: WordPress-Block-Editor kompatibles HTML
- Automatische interne Verlinkung zur Landingpage
- Jeder Artikel endet mit CTA: "Jetzt kostenlos vergleichen →"
- Kein Duplicate Content: Themen-Log in SQLite damit kein Thema wiederholt wird

## Cronjob Schedule
```
0 8  * * * /usr/bin/python3 /var/www/scripts/artikel-generator.py --lang=de
30 8  * * * /usr/bin/python3 /var/www/scripts/artikel-generator.py --lang=en
0 13 * * * /usr/bin/python3 /var/www/scripts/artikel-generator.py --lang=de
30 13 * * * /usr/bin/python3 /var/www/scripts/artikel-generator.py --lang=en
0 18 * * * /usr/bin/python3 /var/www/scripts/artikel-generator.py --lang=de
30 18 * * * /usr/bin/python3 /var/www/scripts/artikel-generator.py --lang=en
```

## Umgebungsvariablen (.env)
```
ANTHROPIC_API_KEY=sk-ant-...
WP_URL=https://krankenzusatz-vergleich.de
WP_USER=admin
WP_APP_PASSWORD=...
DB_NAME=krankenzusatz_db
DB_USER=wp_user
DB_PASSWORD=...
```

## Wichtige Hinweise
- DSGVO: Server in Deutschland (Hetzner Nürnberg/Falkenstein)
- Backups: Hetzner Snapshot täglich aktivieren
- Monitoring: einfaches Uptime-Check via Hetzner oder UptimeRobot
- DNS: A-Records bei All-Inkl auf Hetzner-IP zeigen lassen
