#!/usr/bin/env python3
"""
artikel-generator.py
Generiert hochwertige Blogartikel (1500–2500 Wörter) via Claude API
und veröffentlicht sie in WordPress. 1× täglich, nur DE.

Verwendung:
  python3 artikel-generator.py --lang=de
  python3 artikel-generator.py --dry-run
"""

import argparse
import sqlite3
import os
import sys
import json
import random
import logging
from datetime import datetime, timezone
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from publish_artikel import publish_to_wordpress

# ── KONFIGURATION ────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
ENV_FILE   = BASE_DIR / '.env'
DB_FILE    = BASE_DIR / 'topics.db'
LOG_FILE   = Path('/var/log/krankenzusatz/generator.log')
MODEL      = 'claude-sonnet-4-6'
MAX_TOKENS = 6000  # erhöht für 1500-2500 Wörter

AUTOR_NAME   = "Klaus Blömecke"
AUTOR_TITLE  = "Versicherungsexperte, Inhaber Blömecke &amp; Partner"
AUTOR_BIO    = (
    "Klaus Blömecke ist zugelassener Versicherungsvermittler (IHK München, "
    "Nr. D-6ULZ-YVLWB-50) und Inhaber von Blömecke &amp; Partner in Plattling. "
    "Seit über 20 Jahren berät er GKV-Versicherte in Bayern und deutschlandweit "
    "zu Kranken-Zusatzversicherungen – persönlich, kostenlos und unverbindlich."
)
# ─────────────────────────────────────────────────────────────────────────────

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

# ── INTERNE VERLINKUNG ───────────────────────────────────────────────────────
# Keyword → interne URL die verlinkt werden soll (erste Erwähnung)
INTERNAL_LINKS = {
    "Zahnzusatzversicherung":     "https://krankenzusatz-vergleich.de/zahnzusatz/",
    "Zahnzusatz":                  "https://krankenzusatz-vergleich.de/zahnzusatz/",
    "Krankenhauszusatzversicherung": "https://krankenzusatz-vergleich.de/krankenhaus/",
    "Krankenhauszusatz":           "https://krankenzusatz-vergleich.de/krankenhaus/",
    "DKV":                         "https://krankenzusatz-vergleich.de/dkv/",
    "Signal Iduna":                "https://krankenzusatz-vergleich.de/signal-iduna/",
    "Hanse Merkur":                "https://krankenzusatz-vergleich.de/hanse-merkur/",
    "Krankenzusatzversicherung":   "https://krankenzusatz-vergleich.de/",
}

# Stadt → Stadtseiten-URL für lokale Erwähnungen
CITY_LINKS = {
    "München":      "https://krankenzusatz-vergleich.de/zahnzusatz-muenchen/",
    "Berlin":       "https://krankenzusatz-vergleich.de/zahnzusatz-berlin/",
    "Hamburg":      "https://krankenzusatz-vergleich.de/zahnzusatz-hamburg/",
    "Frankfurt":    "https://krankenzusatz-vergleich.de/zahnzusatz-frankfurt/",
    "Köln":         "https://krankenzusatz-vergleich.de/zahnzusatz-koeln/",
    "Stuttgart":    "https://krankenzusatz-vergleich.de/zahnzusatz-stuttgart/",
    "Düsseldorf":   "https://krankenzusatz-vergleich.de/zahnzusatz-duesseldorf/",
    "Nürnberg":     "https://krankenzusatz-vergleich.de/zahnzusatz-nuernberg/",
    "Augsburg":     "https://krankenzusatz-vergleich.de/zahnzusatz-augsburg/",
    "Regensburg":   "https://krankenzusatz-vergleich.de/zahnzusatz-regensburg/",
}

# ── THEMEN-POOL (DE) ─────────────────────────────────────────────────────────
TOPICS = {
    'de': [
        # Zahnzusatzversicherung
        ("zahnzusatz", "Zahnersatz 2026: Was zahlt die GKV – und was bleibt an Ihnen hängen?"),
        ("zahnzusatz", "Zahnzusatzversicherung ohne Wartezeit: Die besten Tarife 2026 im Vergleich"),
        ("zahnzusatz", "Implantat oder Brücke: Was leistet die Zahnzusatzversicherung wirklich?"),
        ("zahnzusatz", "Kieferorthopädie für Erwachsene: Welche Tarife übernehmen die Kosten?"),
        ("zahnzusatz", "Professionelle Zahnreinigung: Warum die GKV kaum zahlt und Zusatztarife helfen"),
        ("zahnzusatz", "Zahnzusatzversicherung trotz Vorerkrankung: So finden Sie den richtigen Tarif"),
        ("zahnzusatz", "DKV, Signal Iduna oder Hanse Merkur: Welche Zahnzusatz passt zu mir?"),
        ("zahnzusatz", "GKV-Festzuschüsse erklärt: Wie Sie mit einer Zusatzversicherung klug kombinieren"),
        ("zahnzusatz", "Zahnzusatzversicherung für Kinder: Was Eltern wirklich wissen müssen"),
        ("zahnzusatz", "Zahnzusatz ab wann sinnvoll? Das richtige Einstiegsalter für maximale Ersparnis"),
        ("zahnzusatz", "Inlays, Veneers, Keramikzähne: Was zahlt welche Zusatzversicherung?"),
        ("zahnzusatz", "Bonusheft richtig führen: So steigern Sie Ihren GKV-Zuschuss auf bis zu 65 %"),
        # Krankenhaus
        ("krankenhaus", "Chefarztbehandlung im Krankenhaus: Wie funktioniert die Zusatzversicherung wirklich?"),
        ("krankenhaus", "Einbettzimmer im Krankenhaus: Für wen lohnt sich die Zusatzversicherung?"),
        ("krankenhaus", "Krankenhauszusatz für Selbstständige: Warum schnelle Genesung entscheidend ist"),
        ("krankenhaus", "Privatpatient als GKV-Versicherter: So geht es mit der richtigen Zusatzpolice"),
        ("krankenhaus", "Wahlleistungen im Krankenhaus: Kosten, Nutzen und die besten Tarife 2026"),
        ("krankenhaus", "Krankenhaus-Tagegeld: Wieviel brauche ich wirklich und wann zahlt es sich aus?"),
        ("krankenhaus", "Rooming-In: Warum Eltern eine Krankenhauszusatz für ihre Kinder brauchen"),
        ("krankenhaus", "Freie Krankenhauswahl: Warum Spezialisten oft nur über Privatpatienten erreichbar sind"),
        # GKV-Ratgeber
        ("gkv-ratgeber", "GKV-Leistungen 2026: Was hat sich verändert und wo sind die größten Lücken?"),
        ("gkv-ratgeber", "Eigenanteil bei Medikamenten: Tipps um die Zuzahlung zu senken"),
        ("gkv-ratgeber", "Krankenkasse wechseln 2026: Wann es sich lohnt und worauf Sie achten müssen"),
        ("gkv-ratgeber", "GKV-Zusatzleistungen: Was Ihre Krankenkasse extra bietet – und was nicht"),
        ("gkv-ratgeber", "Zusatzversicherung kombinieren: So maximieren Sie Schutz bei minimalem Beitrag"),
        ("gkv-ratgeber", "Bonus-Programme der Krankenkassen: Wirklicher Mehrwert oder Marketing-Gag?"),
        # Heilpraktiker
        ("heilpraktiker", "Heilpraktiker-Zusatzversicherung 2026: Akupunktur, Osteopathie und mehr"),
        ("heilpraktiker", "Osteopathie-Kosten: Was die GKV zahlt – und warum eine Zusatzversicherung sinnvoll ist"),
        ("heilpraktiker", "Naturheilkunde richtig absichern: Die besten Heilpraktiker-Tarife im Überblick"),
        # Vorsorge & Sehhilfen
        ("vorsorge", "Vorsorgeuntersuchungen: Was die GKV zahlt und wo Zusatztarife sinnvoll sind"),
        ("sehhilfen", "Brillenversicherung 2026: Wann lohnt sie sich – und wann nicht?"),
        # Ratgeber Abschluss
        ("gkv-ratgeber", "Versicherungsantrag ausfüllen: Gesundheitsfragen richtig beantworten"),
        ("gkv-ratgeber", "Kündigung und Wechsel: So wechseln Sie Ihre Zusatzversicherung ohne Lücken"),
        ("gkv-ratgeber", "Zusatzversicherung im Alter: Wann ist es noch sinnvoll abzuschließen?"),
    ],
}

# ── SYSTEM-PROMPT ────────────────────────────────────────────────────────────
SYSTEM_PROMPT_DE = f"""Du bist Klaus Blömecke, erfahrener Versicherungsexperte und Inhaber von Blömecke & Partner in Plattling, Bayern. Du schreibst Ratgeber-Artikel für den Blog krankenzusatz-vergleich.de.

WICHTIGE REGELN:

Länge & Qualität:
- Mindestens 1.500 Wörter, idealerweise 1.800–2.200 Wörter
- Kein generischer Fülltext – jeder Abschnitt muss echten Mehrwert bieten
- Konkrete Zahlen, Beispiele und Vergleiche einbauen
- Wo sinnvoll: eine Tabelle mit Vergleich (HTML <table>)

Ton & Stil:
- Sachlich, vertrauenswürdig, auf Augenhöhe mit dem Leser
- Kein Werbesprech, keine übertriebenen Versprechen
- Persönliche Formulierungen erlaubt: "In meiner Beratungspraxis erlebe ich häufig..."

Format (semantisches HTML, KEIN Markdown):
- Nur h2 und h3 (kein h1 – wird vom WordPress-Theme gesetzt)
- p, ul, ol, li, strong, em, table, thead, tbody, tr, th, td
- Abschnittsstruktur: Einleitung → Hauptteil (3–5 Abschnitte) → Fazit

Interne Verlinkung (PFLICHT – genau einmal pro Keyword):
- Erste Erwähnung "Zahnzusatzversicherung" → <a href="https://krankenzusatz-vergleich.de/zahnzusatz/">Zahnzusatzversicherung</a>
- Erste Erwähnung "Krankenhauszusatz" → <a href="https://krankenzusatz-vergleich.de/krankenhaus/">Krankenhauszusatz</a>
- Erste Erwähnung "DKV" → <a href="https://krankenzusatz-vergleich.de/dkv/">DKV</a>
- Erste Erwähnung "Signal Iduna" → <a href="https://krankenzusatz-vergleich.de/signal-iduna/">Signal Iduna</a>
- Erste Erwähnung "Hanse Merkur" → <a href="https://krankenzusatz-vergleich.de/hanse-merkur/">Hanse Merkur</a>
- Erste Erwähnung "Krankenzusatzversicherung" (allgemein) → <a href="https://krankenzusatz-vergleich.de/">Krankenzusatzversicherung</a>

Versicherer: Nur DKV, Signal Iduna und Hanse Merkur nennen – keine anderen.

Haftungshinweis: Am Ende jedes Artikels EINEN Satz einfügen:
<p><em>Hinweis: Dieser Artikel dient der allgemeinen Information und ersetzt keine individuelle Versicherungsberatung.</em></p>

Ausgabe: Nur HTML-Artikelinhalt ohne <html>, <head>, <body> Tags. Beginne direkt mit dem ersten <h2>."""

# ── DATENBANK ────────────────────────────────────────────────────────────────
def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS published (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            topic        TEXT NOT NULL,
            lang         TEXT NOT NULL,
            published_at TEXT NOT NULL,
            wp_post_id   INTEGER,
            UNIQUE(topic, lang)
        )
    """)
    conn.commit()
    return conn


def pick_topic(conn: sqlite3.Connection, lang: str) -> tuple[str, str]:
    published = {
        row[0]
        for row in conn.execute("SELECT topic FROM published WHERE lang = ?", (lang,))
    }
    pool = TOPICS[lang]
    available = [(cat, t) for cat, t in pool if t not in published]

    if not available:
        log.warning("Alle Themen für '%s' veröffentlicht – Pool zurücksetzen", lang)
        conn.execute("DELETE FROM published WHERE lang = ?", (lang,))
        conn.commit()
        available = pool

    return random.choice(available)


def mark_published(conn: sqlite3.Connection, topic: str, lang: str, wp_post_id: int | None):
    conn.execute(
        "INSERT OR REPLACE INTO published (topic, lang, published_at, wp_post_id) VALUES (?, ?, ?, ?)",
        (topic, lang, datetime.now(timezone.utc).isoformat(), wp_post_id),
    )
    conn.commit()


# ── ARTIKEL GENERIEREN ───────────────────────────────────────────────────────
def generate_article(category: str, title: str, lang: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    user_prompt = (
        f'Schreibe einen ausführlichen, hochwertigen Ratgeber-Artikel mit dem Titel:\n'
        f'"{title}"\n\n'
        f'Kategorie: {category}\n\n'
        f'Anforderungen:\n'
        f'- Mindestens 1.500 Wörter echten Inhalt\n'
        f'- Mindestens 3 aussagekräftige H2-Abschnitte\n'
        f'- Eine Vergleichstabelle (wenn zum Thema passend)\n'
        f'- Konkrete Zahlen und Beispiele (Preise, Prozentsätze, Szenarien)\n'
        f'- Alle internen Links wie in den Regeln beschrieben einbauen\n\n'
        f'Liefere nur den HTML-Artikelinhalt (ab H2), ohne Einleitung oder Erklärungen.'
    )

    log.info("Generiere Artikel: '%s'", title)

    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT_DE,
        messages=[{'role': 'user', 'content': user_prompt}],
    )

    content = message.content[0].text.strip()
    log.info("Generiert: %d Zeichen | %d Output-Tokens",
             len(content), message.usage.output_tokens)
    return content


def append_author_box(content: str) -> str:
    """Hängt einen Autoren-Block ans Ende des Artikels."""
    author_html = f"""
<div class="author-box" style="margin-top:2em;padding:1.2em 1.4em;background:#f0f4ff;border-left:4px solid #0057ff;border-radius:8px;">
  <p style="margin:0 0 4px;font-size:.85em;color:#8898aa;text-transform:uppercase;letter-spacing:.05em;">Über den Autor</p>
  <p style="margin:0 0 6px;font-weight:700;color:#0a1628;font-size:1em;">{AUTOR_NAME} · <span style="font-weight:400;color:#4a5568;font-size:.92em;">{AUTOR_TITLE}</span></p>
  <p style="margin:0;font-size:.9em;color:#4a5568;line-height:1.6;">{AUTOR_BIO}</p>
</div>"""
    return content + author_html


def build_meta(title: str, content: str, lang: str) -> dict:
    slug = title.lower()
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        ' ': '-', '?': '', '!': '', ':': '', ',': '',
        '.': '', '(': '', ')': '', '/': '-', '–': '-', '—': '-', '"': '', "'": '',
    }
    for ch, rep in replacements.items():
        slug = slug.replace(ch, rep)
    slug = '-'.join(filter(None, slug.split('-')))[:80]

    # Excerpt: ersten sauberen Satz extrahieren
    import re
    text_only = re.sub(r'<[^>]+>', ' ', content)
    words = text_only.split()
    excerpt = ' '.join(words[:40]) + '…'

    word_count = len(text_only.split())

    tags = ['Krankenzusatzversicherung', 'Versicherungsvergleich', 'GKV', 'Tarife 2026']
    for word in title.split():
        if len(word) > 6 and word not in tags:
            tags.append(word)

    return {
        'slug':       slug,
        'excerpt':    excerpt,
        'tags':       tags[:8],
        'word_count': word_count,
    }


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Artikel-Generator krankenzusatz-vergleich.de')
    parser.add_argument('--lang', choices=['de', 'en'], default='de',
                        help='Artikelsprache (Standard: de)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Nur generieren, nicht veröffentlichen')
    parser.add_argument('--topic', type=str, default=None,
                        help='Bestimmtes Thema erzwingen (Titeltext)')
    args = parser.parse_args()

    required_vars = ['ANTHROPIC_API_KEY', 'WP_URL', 'WP_USER', 'WP_APP_PASSWORD']
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        log.error("Fehlende .env-Variablen: %s", ', '.join(missing))
        sys.exit(1)

    conn = init_db()

    if args.topic:
        pool = TOPICS.get(args.lang, [])
        match = [(c, t) for c, t in pool if args.topic.lower() in t.lower()]
        if not match:
            log.error("Thema nicht gefunden: %s", args.topic)
            sys.exit(1)
        category, title = match[0]
    else:
        category, title = pick_topic(conn, args.lang)

    log.info("── Artikel-Generator gestartet ────────────────────")
    log.info("Sprache:   DE")
    log.info("Kategorie: %s", category)
    log.info("Titel:     %s", title)

    try:
        content = generate_article(category, title, args.lang)
    except anthropic.APIError as e:
        log.error("Claude API Fehler: %s", e)
        sys.exit(1)

    content = append_author_box(content)
    meta    = build_meta(title, content, args.lang)

    log.info("Wörter: ~%d", meta['word_count'])

    if args.dry_run:
        log.info("DRY-RUN – nicht veröffentlicht")
        print(f"\n{'='*60}")
        print(f"Titel:  {title}")
        print(f"Slug:   {meta['slug']}")
        print(f"Wörter: {meta['word_count']}")
        print(f"Tags:   {', '.join(meta['tags'])}")
        print(f"{'='*60}\n")
        print(content[:800] + '\n...')
        return

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
    except Exception as e:
        log.error("WordPress-Fehler: %s", e)
        sys.exit(1)

    log.info("── Fertig ─────────────────────────────────────────")


if __name__ == '__main__':
    main()
