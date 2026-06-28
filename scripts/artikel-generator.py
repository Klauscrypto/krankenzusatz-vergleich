#!/usr/bin/env python3
"""
artikel-generator.py – Aufgabe 5
Generiert Blogartikel zu Krankenzusatzversicherungen via Claude API
und veröffentlicht sie direkt in WordPress.

Verwendung:
  python3 artikel-generator.py --lang=de
  python3 artikel-generator.py --lang=en
"""

import argparse
import sqlite3
import os
import sys
import json
import random
import hashlib
import logging
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from publish_artikel import publish_to_wordpress

# ── KONFIGURATION ────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
ENV_FILE   = BASE_DIR / '.env'
DB_FILE    = BASE_DIR / 'topics.db'
LOG_FILE   = Path('/var/log/krankenzusatz/generator.log')
MODEL      = 'claude-sonnet-4-6'
MAX_TOKENS = 3000
# ─────────────────────────────────────────────────────────────────

load_dotenv(ENV_FILE)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
    ]
)
log = logging.getLogger(__name__)

# ── THEMEN-POOL ──────────────────────────────────────────────────
TOPICS = {
    'de': [
        # Zahnzusatzversicherung
        ("zahnzusatz", "Zahnersatz 2026: Was zahlt die GKV – und was nicht?"),
        ("zahnzusatz", "Zahnzusatzversicherung ohne Wartezeit: Die besten Tarife im Vergleich"),
        ("zahnzusatz", "Implantat oder Brücke: Was übernimmt die Zahnzusatzversicherung?"),
        ("zahnzusatz", "Kieferorthopädie für Erwachsene: Welche Tarife zahlen?"),
        ("zahnzusatz", "Zahnreinigung versichern: Professionelle Zahnreinigung und Zusatzversicherung"),
        ("zahnzusatz", "Zahnzusatzversicherung mit Vorerkrankung: So geht's"),
        ("zahnzusatz", "Zahnzusatzversicherung Vergleich: DKV, Allianz, AXA 2026"),
        ("zahnzusatz", "Festzuschüsse der GKV erklärt: Lücken clever schließen"),
        # Krankenhaus
        ("krankenhaus", "Chefarztbehandlung ohne Zuzahlung: So funktioniert die Krankenhauspolice"),
        ("krankenhaus", "Einbettzimmer im Krankenhaus: Lohnt sich die Zusatzversicherung?"),
        ("krankenhaus", "Krankenhaustagegeld: Wie viel brauche ich wirklich?"),
        ("krankenhaus", "Privatpatient als GKV-Versicherter – geht das?"),
        ("krankenhaus", "Krankenhaus-Zusatzversicherung für Kinder: Was Eltern wissen müssen"),
        ("krankenhaus", "Operation mit Wahlleistungen: Kosten und Erstattung im Überblick"),
        # Auslandsreise
        ("auslandsreise", "Auslandsreisekrankenversicherung 2026: Was ist wirklich wichtig?"),
        ("auslandsreise", "Weltweiter Schutz ab 8 Euro im Jahr: Die besten Reisepolicen"),
        ("auslandsreise", "Rücktransport aus dem Ausland: Wer zahlt, wenn es teuer wird?"),
        ("auslandsreise", "Reisekrankenversicherung für Senioren über 70"),
        ("auslandsreise", "Jahrespolice vs. Einzelreise: Was lohnt sich mehr?"),
        # Heilpraktiker
        ("heilpraktiker", "Heilpraktiker-Zusatzversicherung: Akupunktur, Osteopathie & Co."),
        ("heilpraktiker", "Osteopathie-Kosten: GKV zahlt kaum – was die Zusatzversicherung übernimmt"),
        ("heilpraktiker", "Homöopathie auf Krankenschein: Realität vs. Zusatzversicherung"),
        ("heilpraktiker", "Naturheilkunde absichern: Die besten Tarife 2026"),
        # Sehhilfen
        ("sehhilfen", "Brillenversicherung 2026: Wann lohnt sie sich wirklich?"),
        ("sehhilfen", "Kontaktlinsen-Versicherung: Kosten und Erstattung"),
        ("sehhilfen", "Lasik-OP versichern: Augenlaser und Zusatzversicherung"),
        # Vorsorge
        ("vorsorge", "Vorsorgeversicherung: Was zahlt die GKV – was die Zusatzversicherung?"),
        ("vorsorge", "Gesundheitskurse auf Krankenschein: Yoga, Sport und Ernährungsberatung"),
        # GKV-Ratgeber
        ("gkv-ratgeber", "GKV-Leistungen 2026: Was hat sich geändert?"),
        ("gkv-ratgeber", "Eigenanteil bei Medikamenten senken: Tipps und Zusatzversicherungen"),
        ("gkv-ratgeber", "GKV-Zusatzversicherung kombinieren: So sparst du am meisten"),
        ("gkv-ratgeber", "Krankenkassenwechsel 2026: Beste GKV und sinnvolle Zusatzleistungen"),
        ("gkv-ratgeber", "Bonus-Programme der Krankenkassen: Lohnt es sich wirklich?"),
    ],
    'en': [
        ("expat-guide", "German health insurance explained: GKV, PKV and Zusatzversicherung"),
        ("expat-guide", "Moving to Germany: Your complete health insurance checklist"),
        ("expat-guide", "How to get supplemental health insurance in Germany as a foreigner"),
        ("expat-guide", "Dental costs in Germany 2026: What GKV pays — and what it doesn't"),
        ("expat-guide", "Germany's public health insurance gaps: What every expat should know"),
        ("expat-guide", "Private hospital room in Germany: Is it worth the extra cost?"),
        ("expat-guide", "Travel health insurance for expats living in Germany"),
        ("expat-guide", "Alternative medicine in Germany: Acupuncture, osteopathy and GKV limits"),
        ("expat-guide", "Glasses and contact lenses in Germany: Coverage guide for expats"),
        ("expat-guide", "How to cancel German health insurance when you leave"),
        ("expat-guide", "English-speaking doctors in Germany: How supplemental insurance helps"),
        ("expat-guide", "Freelancer health insurance in Germany: GKV vs supplemental plans"),
        ("expat-guide", "Specialist appointments in Germany: Skip the 6-week wait"),
        ("expat-guide", "German dental implants: Cost, GKV coverage and supplemental plans"),
        ("expat-guide", "Health insurance for families in Germany: What expat parents need to know"),
    ],
}

SYSTEM_PROMPT_DE = """Du bist ein erfahrener Redakteur für ein unabhängiges deutsches Versicherungsvergleichsportal.
Schreibe sachliche, nützliche Ratgeber-Artikel über Krankenzusatzversicherungen.

Regeln:
- Länge: 900–1200 Wörter
- Ton: sachlich, vertrauenswürdig, leserfreundlich – kein Werbesprech
- Format: semantisches HTML (h2, h3, p, ul, strong) – KEIN Markdown
- Interne Verlinkung: Erste Erwähnung von "Krankenzusatzversicherung" mit
  <a href="https://krankenzusatz-vergleich.de/">Krankenzusatzversicherung</a> verlinken
- Am Ende: KEIN CTA-Block (wird automatisch vom Theme angehängt)
- Zahlen und Preise: aktuelle Beispielwerte 2026 verwenden
- Keine Finanzberatung: immer auf individuelle Beratung hinweisen
- Kein Duplicate Content: jeder Artikel muss einzigartigen Mehrwert liefern
- SEO: H1-Titel wird vom WordPress-Theme gesetzt, beginne mit H2

Ausgabe: Nur HTML-Inhalt ohne <html>, <head>, <body> Tags."""

SYSTEM_PROMPT_EN = """You are an experienced editor for an independent German insurance comparison portal,
writing for expats and internationals living in Germany.

Rules:
- Length: 900–1200 words
- Tone: clear, factual, helpful — no jargon, no sales language
- Format: semantic HTML (h2, h3, p, ul, strong) — NO Markdown
- Internal link: First mention of "supplemental health insurance" with
  <a href="https://krankenzusatz-vergleich.de/en/">supplemental health insurance</a>
- No CTA block at the end (added automatically by the theme)
- Numbers: use 2026 figures where relevant
- Disclaimer: remind readers this is general information, not financial advice
- Start with H2, not H1 (title is set by WordPress theme)

Output: HTML content only, no <html>, <head>, <body> tags."""

# ── DATENBANK ────────────────────────────────────────────────────
def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS published (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            topic     TEXT NOT NULL,
            lang      TEXT NOT NULL,
            published_at TEXT NOT NULL,
            wp_post_id   INTEGER,
            UNIQUE(topic, lang)
        )
    """)
    conn.commit()
    return conn


def pick_topic(conn: sqlite3.Connection, lang: str) -> tuple[str, str]:
    """Wählt ein noch nicht veröffentlichtes Thema aus."""
    published = {
        row[0]
        for row in conn.execute("SELECT topic FROM published WHERE lang = ?", (lang,))
    }
    pool = TOPICS[lang]
    available = [(cat, t) for cat, t in pool if t not in published]

    if not available:
        log.warning("Alle Themen für '%s' bereits veröffentlicht – Topic-Pool zurücksetzen", lang)
        conn.execute("DELETE FROM published WHERE lang = ?", (lang,))
        conn.commit()
        available = pool

    return random.choice(available)


def mark_published(conn: sqlite3.Connection, topic: str, lang: str, wp_post_id: int | None):
    conn.execute(
        "INSERT OR REPLACE INTO published (topic, lang, published_at, wp_post_id) VALUES (?, ?, ?, ?)",
        (topic, lang, datetime.utcnow().isoformat(), wp_post_id),
    )
    conn.commit()

# ── ARTIKEL GENERIEREN ───────────────────────────────────────────
def generate_article(category: str, title: str, lang: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    system = SYSTEM_PROMPT_DE if lang == 'de' else SYSTEM_PROMPT_EN

    user_prompt = (
        f'Schreibe einen ausführlichen Ratgeber-Artikel mit dem Titel:\n"{title}"\n\n'
        f'Kategorie: {category}\n'
        f'Liefere nur den HTML-Artikelinhalt (ab H2), ohne Einleitung oder Erklärungen.'
        if lang == 'de' else
        f'Write a detailed guide article with the title:\n"{title}"\n\n'
        f'Category: {category}\n'
        f'Return only the HTML article content (starting with H2), no preamble.'
    )

    log.info("Generiere Artikel: '%s' [%s]", title, lang.upper())

    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{'role': 'user', 'content': user_prompt}],
    )

    content = message.content[0].text.strip()
    log.info("Artikel generiert: %d Zeichen | Tokens: %s",
             len(content), message.usage.output_tokens)
    return content


def build_meta(title: str, content: str, lang: str) -> dict:
    """Erstellt SEO-Meta-Daten für den Artikel."""
    # Einfache Slug-Generierung
    slug = title.lower()
    for ch in ' äöüß!?:,.()/–—"\'':
        slug = slug.replace(ch, '-' if ch == ' ' else '')
    slug = slug.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    slug = '-'.join(filter(None, slug.split('-')))[:80]

    word_count = len(content.split())
    excerpt = ' '.join(content.replace('<', ' <').split()[:35])
    # Tags aus Titel ableiten
    keyword_map = {
        'de': ['Krankenzusatzversicherung', 'Versicherungsvergleich', 'GKV', 'Tarife 2026'],
        'en': ['supplemental health insurance Germany', 'expat insurance Germany', 'GKV', '2026'],
    }
    tags = keyword_map[lang][:]
    for word in title.split():
        if len(word) > 6 and word not in tags:
            tags.append(word)

    return {
        'slug':      slug,
        'excerpt':   excerpt,
        'tags':      tags[:8],
        'word_count': word_count,
    }

# ── MAIN ─────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Artikel-Generator für krankenzusatz-vergleich.de')
    parser.add_argument('--lang', choices=['de', 'en'], required=True,
                        help='Artikelsprache: de oder en')
    parser.add_argument('--dry-run', action='store_true',
                        help='Artikel generieren aber NICHT veröffentlichen')
    parser.add_argument('--topic', type=str, default=None,
                        help='Bestimmtes Thema erzwingen (exakter Titeltext)')
    args = parser.parse_args()

    # Env-Validierung
    required_vars = ['ANTHROPIC_API_KEY', 'WP_URL', 'WP_USER', 'WP_APP_PASSWORD']
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        log.error("Fehlende Umgebungsvariablen: %s", ', '.join(missing))
        log.error("Bitte /var/www/scripts/.env ausfüllen")
        sys.exit(1)

    conn = init_db()

    # Thema wählen
    if args.topic:
        # Manuell angegebenes Thema suchen
        pool = TOPICS[args.lang]
        match = [(c, t) for c, t in pool if args.topic.lower() in t.lower()]
        if not match:
            log.error("Thema nicht gefunden: %s", args.topic)
            sys.exit(1)
        category, title = match[0]
    else:
        category, title = pick_topic(conn, args.lang)

    log.info("── Starte Artikel-Generator ──────────────────────")
    log.info("Sprache:   %s", args.lang.upper())
    log.info("Kategorie: %s", category)
    log.info("Titel:     %s", title)

    # Artikel generieren
    try:
        content = generate_article(category, title, args.lang)
    except anthropic.APIError as e:
        log.error("Claude API Fehler: %s", e)
        sys.exit(1)

    meta = build_meta(title, content, args.lang)

    if args.dry_run:
        log.info("DRY-RUN: Artikel nicht veröffentlicht")
        print(f"\n{'='*60}")
        print(f"Titel: {title}")
        print(f"Slug:  {meta['slug']}")
        print(f"Wörter: {meta['word_count']}")
        print(f"Tags:  {', '.join(meta['tags'])}")
        print(f"{'='*60}\n")
        print(content[:500] + '...')
        return

    # In WordPress veröffentlichen
    try:
        wp_post_id = publish_to_wordpress(
            title=title,
            content=content,
            category_slug=category,
            tags=meta['tags'],
            excerpt=meta['excerpt'],
            slug=meta['slug'],
            lang=args.lang,
        )
        mark_published(conn, title, args.lang, wp_post_id)
        log.info("✓ Veröffentlicht: WP Post ID %d", wp_post_id)
        log.info("  URL: %s/%s/%s", os.environ['WP_URL'], category, meta['slug'])
    except Exception as e:
        log.error("WordPress-Fehler: %s", e)
        sys.exit(1)

    log.info("── Artikel-Generator fertig ───────────────────────")


if __name__ == '__main__':
    main()
