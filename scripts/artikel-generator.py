#!/usr/bin/env python3
"""
artikel-generator.py
Generiert Ratgeber-Artikel via Claude API und veröffentlicht sie in WordPress. 1× täglich (auch am
Wochenende), nur DE. Gleiches Verfahren wie die anderen Jarvis-Blogs („aus einer Feder“):

  1. Artikel schreiben (Claude)
  2. Unabhängiger Faktencheck durch einen zweiten Durchgang (Fachlektor, korrigiert wo möglich)
  3. Qualitätsprüfung im Code: vollständig (nicht abgeschnitten), keine KI-Meta-Sätze
     („Entschuldigung“, „ich meine natürlich“ …), Mindestlänge, Haftungshinweis, nur erlaubte Versicherer
  4. Alles bestanden → live. Sonst → WordPress-Entwurf (nichts Fehlerhaftes geht online).

Verwendung:
  python3 artikel-generator.py --lang=de
  python3 artikel-generator.py --dry-run
  python3 artikel-generator.py --repair 144,145   # bestehende Beiträge neu schreiben (URL bleibt)
"""

import argparse
import re
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
from publish_artikel import publish_to_wordpress, wp_published_titles, get_post, update_post_content

# ── KONFIGURATION ────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
ENV_FILE   = BASE_DIR / '.env'
DB_FILE    = BASE_DIR / 'topics.db'
LOG_FILE   = Path('/var/log/krankenzusatz/generator.log')
MODEL      = os.environ.get('CLAUDE_MODEL', 'claude-opus-5-5')
MAX_TOKENS = 16000  # genug Luft, damit nichts abgeschnitten wird (abgeschnitten = Entwurf)
MIN_WOERTER = 900
ERLAUBTE_VERSICHERER = {'DKV', 'Signal Iduna', 'Hanse Merkur', 'HanseMerkur'}
ANDERE_VERSICHERER = ['Allianz', 'AXA', 'Barmenia', 'ARAG', 'ERGO', 'Gothaer', 'Debeka', 'Continentale',
                      'Württembergische', 'SDK', 'Münchener Verein', 'Union Krankenversicherung', 'Huk', 'HUK',
                      'Generali', 'Hallesche', 'Concordia',
                      'Alte Oldenburger', 'Württembergische', 'Zurich', 'R+V', 'LVM', 'VGH', 'Provinzial']
# Sätze, die nur ein Sprachmodell schreibt – dürfen nie online gehen
META_MUSTER = re.compile(
    r'Entschuldigung|ich meine natürlich|Korrektur:|Als (?:KI|Sprachmodell)|Hier ist (?:der|ein|Ihr) Artikel|'
    r'Ich hoffe, dieser Artikel|```|\bLorem\b|\[(?:TODO|Platzhalter)[^\]]*\]', re.I)

AUTOR_NAME   = "Alexander Blömecke"
AUTOR_TITLE  = "Versicherungsexperte, Inhaber Blömecke &amp; Partner"
AUTOR_BIO    = (
    "Alexander Blömecke ist zugelassener Versicherungsvermittler (IHK München, "
    "Nr. D-6ULZ-YVLWB-50) und Inhaber von Blömecke &amp; Partner in Auerbach. "
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

        # ── Erweiterung 26.10.2026 (der alte Pool war aufgebraucht und wurde wiederholt) ──
        # Zahnzusatzversicherung
        ("zahnzusatz", "Wurzelbehandlung: Wann die GKV zahlt und wann Sie privat zahlen müssen"),
        ("zahnzusatz", "Parodontose-Behandlung: Kosten, GKV-Leistung und was eine Zusatzversicherung übernimmt"),
        ("zahnzusatz", "Zahnstaffel erklärt: Warum die Erstattung in den ersten Jahren begrenzt ist"),
        ("zahnzusatz", "Fehlende Zähne beim Abschluss: Was Sie vor dem Vertrag wissen müssen"),
        ("zahnzusatz", "Heil- und Kostenplan verstehen: So lesen Sie den Plan Ihres Zahnarztes"),
        ("zahnzusatz", "Kunststofffüllung oder Amalgam: Was die GKV zahlt und was der Zahnarzt berechnet"),
        ("zahnzusatz", "Zahnersatz im Ausland: Lohnt sich der Weg – und was zahlt die Versicherung?"),
        ("zahnzusatz", "Knirschschiene und Aufbissschiene: Wer übernimmt die Kosten?"),
        ("zahnzusatz", "Zahnarztrechnung nach GOZ: Was der Steigerungssatz für Ihren Eigenanteil bedeutet"),
        ("zahnzusatz", "Zahnzusatzversicherung für Rentner: Worauf es im Ruhestand ankommt"),
        ("zahnzusatz", "Zahnzusatz für Paare und Familien: Einzelverträge oder gemeinsam absichern?"),
        ("zahnzusatz", "Laufende Behandlung beim Abschluss: Warum der Zeitpunkt entscheidend ist"),
        ("zahnzusatz", "Prothese, Teilprothese, Brücke: Kostenvergleich mit und ohne Zusatzversicherung"),
        ("zahnzusatz", "Bleaching und ästhetische Zahnmedizin: Was eine Zahnzusatzversicherung leistet"),
        ("zahnzusatz", "Zahnzusatzversicherung kündigen: Fristen, Folgen und der richtige Zeitpunkt"),
        # Krankenhaus
        ("krankenhaus", "Geplante Operation: Wie Sie vorher Ihre Krankenhausleistungen prüfen"),
        ("krankenhaus", "Zweibettzimmer oder Einbettzimmer: Was der Unterschied im Tarif kostet"),
        ("krankenhaus", "Krankenhauszusatz für Familien: Kinder richtig mitversichern"),
        ("krankenhaus", "Ambulante Operation: Greift die Krankenhauszusatzversicherung?"),
        ("krankenhaus", "Wahlärztliche Leistungen: Was auf der Wahlleistungsvereinbarung steht"),
        ("krankenhaus", "Krankenhauszusatz ohne Gesundheitsfragen: Vor- und Nachteile"),
        ("krankenhaus", "Reha nach dem Krankenhaus: Was die GKV zahlt und wo Lücken bleiben"),
        ("krankenhaus", "Krankenhausaufenthalt im Ausland: Was GKV und Zusatzversicherung abdecken"),
        ("krankenhaus", "Krankenhauszusatz für Berufseinsteiger: Warum sich ein früher Abschluss lohnen kann"),
        ("krankenhaus", "Zuzahlung im Krankenhaus: 10 Euro pro Tag und wie Sie sie begrenzen"),
        # Heilpraktiker / Naturheilkunde
        ("heilpraktiker", "Homöopathie und Naturheilverfahren: Was die GKV übernimmt – und was nicht"),
        ("heilpraktiker", "Gebührenverzeichnis für Heilpraktiker (GebüH): Was es für Ihre Erstattung bedeutet"),
        ("heilpraktiker", "Chiropraktik und manuelle Therapie: Kosten und Erstattung im Überblick"),
        ("heilpraktiker", "Traditionelle Chinesische Medizin: Wann eine Zusatzversicherung zahlt"),
        ("heilpraktiker", "Heilpraktiker oder Arzt für Naturheilverfahren: Unterschied bei der Erstattung"),
        # Vorsorge
        ("vorsorge", "Krebsvorsorge: Welche Untersuchungen die GKV zahlt und welche IGeL-Leistungen sind"),
        ("vorsorge", "IGeL-Leistungen beim Arzt: Wann sie sinnvoll sind und wer sie bezahlt"),
        ("vorsorge", "Reiseimpfungen: Wer die Kosten übernimmt und wie Sie sparen"),
        ("vorsorge", "Check-up ab 35: Was die Gesundheitsuntersuchung umfasst"),
        ("vorsorge", "Hautkrebs-Screening: GKV-Leistung, Zusatzkosten und Erstattung"),
        ("vorsorge", "Vorsorge für Kinder: U-Untersuchungen, Zahnprophylaxe und Zusatzleistungen"),
        # Sehhilfen
        ("sehhilfen", "Augenlasern: Kosten, Ablauf und ob eine Zusatzversicherung zahlt"),
        ("sehhilfen", "Kontaktlinsen und Brille: Wann die GKV ausnahmsweise zuzahlt"),
        ("sehhilfen", "Gleitsichtbrille: Was sie kostet und wie Sie sich gegen die Kosten absichern"),
        ("sehhilfen", "Brille für Kinder: GKV-Zuschuss und sinnvolle Ergänzungen"),
        # GKV-Ratgeber
        ("gkv-ratgeber", "Beitragserhöhung bei der Zusatzversicherung: Warum sie kommt und was Sie tun können"),
        ("gkv-ratgeber", "Wartezeiten in der Zusatzversicherung: Wann der Schutz wirklich beginnt"),
        ("gkv-ratgeber", "Vorvertragliche Anzeigepflicht: Was passiert, wenn Sie etwas vergessen"),
        ("gkv-ratgeber", "Zusatzversicherung und Steuer: Was Sie absetzen können"),
        ("gkv-ratgeber", "Arbeitgeberfinanzierte Zusatzversicherung: So funktioniert die bKV"),
        ("gkv-ratgeber", "Zusatzversicherung für Beamtenanwärter und Azubis: Was sinnvoll ist"),
        ("gkv-ratgeber", "Familienversicherung in der GKV: Wer mitversichert ist und welche Lücken bleiben"),
        ("gkv-ratgeber", "Erstattung einreichen: So bekommen Sie Ihr Geld schnell von der Zusatzversicherung"),
        ("gkv-ratgeber", "Leistungsablehnung durch die Versicherung: Ihre Rechte und nächsten Schritte"),
        ("gkv-ratgeber", "Zusatzbeitrag der Krankenkasse 2026: Was er bedeutet und wann ein Wechsel lohnt"),
        ("gkv-ratgeber", "Pflegezusatzversicherung: Warum die gesetzliche Pflegeversicherung nur ein Teil ist"),
        ("gkv-ratgeber", "Zusatzversicherung nach Umzug ins Ausland: Was mit Ihrem Vertrag passiert"),
        ("gkv-ratgeber", "Tarifvergleich richtig lesen: Erstattungssätze, Höchstbeträge und Kleingedrucktes"),
        ("gkv-ratgeber", "Beratung oder online abschließen: Was bei der Zusatzversicherung sicherer ist"),
        ("gkv-ratgeber", "Krankentagegeld für Angestellte: Wann sich die Absicherung lohnt"),
    ],
}

# ── SYSTEM-PROMPT ────────────────────────────────────────────────────────────
SYSTEM_PROMPT_DE = f"""Du bist Alexander Blömecke, erfahrener Versicherungsexperte und Inhaber von Blömecke & Partner in Auerbach, Bayern. Du schreibst Ratgeber-Artikel für den Blog krankenzusatz-vergleich.de.

WICHTIGE REGELN:

Länge & Qualität:
- Mindestens 1.500 Wörter, idealerweise 1.800–2.200 Wörter
- Kein generischer Fülltext – jeder Abschnitt muss echten Mehrwert bieten
- Konkrete Beispiele und Vergleiche einbauen
- Wo sinnvoll: eine Tabelle mit Vergleich (HTML <table>)

Zahlen & Fakten (sehr wichtig – der Text wird anschließend von einem Fachlektor geprüft):
- Nur gesicherte, allgemein gültige Zahlen (z. B. gesetzliche Regeln der GKV). Bei Unsicherheit weglassen.
- Kosten nur als Spannen und erkennbar als Beispiel („beispielsweise“, „rund“, „je nach Praxis“).
- Keine erfundenen Tarifnamen, Testergebnisse, Studien, Statistiken oder Beitragshöhen.

Ton & Stil:
- Sachlich, vertrauenswürdig, auf Augenhöhe mit dem Leser
- Kein Werbesprech, keine übertriebenen Versprechen
- Persönliche Formulierungen erlaubt: "In meiner Beratungspraxis erlebe ich häufig..."

Format (semantisches HTML, KEIN Markdown):
- Nur h2 und h3 (kein h1 – wird vom WordPress-Theme gesetzt)
- p, ul, ol, li, strong, em, table, thead, tbody, tr, th, td
- Abschnittsstruktur: Einleitung → Hauptteil (3–5 Abschnitte) → Fazit

Interne Verlinkung (nur wenn der Begriff inhaltlich zum Thema passt – genau einmal pro Keyword;
erwähne nie ein Produkt nur, um einen Link unterzubringen):
- Erste Erwähnung "Zahnzusatzversicherung" → <a href="https://krankenzusatz-vergleich.de/zahnzusatz/">Zahnzusatzversicherung</a>
- Erste Erwähnung "Krankenhauszusatz" → <a href="https://krankenzusatz-vergleich.de/krankenhaus/">Krankenhauszusatz</a>
- Erste Erwähnung "DKV" → <a href="https://krankenzusatz-vergleich.de/dkv/">DKV</a>
- Erste Erwähnung "Signal Iduna" → <a href="https://krankenzusatz-vergleich.de/signal-iduna/">Signal Iduna</a>
- Erste Erwähnung "Hanse Merkur" → <a href="https://krankenzusatz-vergleich.de/hanse-merkur/">Hanse Merkur</a>
- Erste Erwähnung "Krankenzusatzversicherung" (allgemein) → <a href="https://krankenzusatz-vergleich.de/">Krankenzusatzversicherung</a>

Versicherer: Nur DKV, Signal Iduna und Hanse Merkur nennen – keine anderen.

Haftungshinweis: Am Ende jedes Artikels EINEN Satz einfügen:
<p><em>Hinweis: Dieser Artikel dient der allgemeinen Information und ersetzt keine individuelle Versicherungsberatung.</em></p>

Ausgabe: Nur HTML-Artikelinhalt ohne <html>, <head>, <body> Tags. Beginne direkt mit dem ersten <h2>.
Schreibe den Text in einem Zug fertig – keine Selbstkorrekturen im Text, keine Anmerkungen an den Leser
über das Schreiben, keine Entschuldigungen."""

SYSTEM_PRUEFUNG = """Du bist strenger Fachlektor für Krankenversicherung (GKV, private Zusatzversicherungen) in
Deutschland und prüfst einen Ratgeber-Artikel für krankenzusatz-vergleich.de vor der Veröffentlichung.

Prüfe auf:
1. Fachliche Fehler oder veraltete Aussagen (GKV-Leistungen, Festzuschüsse, Zuzahlungen, Wartezeiten, Recht).
2. Erfundene Zahlen, Tarifnamen, Testergebnisse, Studien oder Statistiken.
3. Übertreibungen, Heilsversprechen oder individuelle Beratung („Sie sollten Tarif X abschließen“).
4. Inhaltliche Sprünge, Selbstkorrekturen, KI-Meta-Sätze, Wiederholungen, abgebrochene Sätze.
5. Versicherer außer DKV, Signal Iduna und Hanse Merkur (entfernen).
6. Interne Links, die nicht zum Thema passen (entfernen, Text glätten).

Korrigiere den Artikel so, dass alle Probleme behoben sind (Zweifelhaftes streichen oder vorsichtig formulieren).
Erhalte HTML-Struktur, Links und den Hinweis-Satz am Ende. Kürze nicht unnötig.

Antworte GENAU in diesem Format:
<pruefung>{"freigabe": true oder false, "probleme": ["…", "…"]}</pruefung>
<artikel>…vollständiger korrigierter HTML-Artikel…</artikel>

freigabe = true NUR, wenn der korrigierte Artikel ohne Bedenken veröffentlicht werden kann."""

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


def pick_topic(conn: sqlite3.Connection, lang: str) -> tuple[str, str] | None:
    """Wählt ein Thema, das es im Blog noch nicht gibt – oder None.

    Früher wurde der Pool zurückgesetzt, sobald alle Themen durch waren. Ergebnis
    bis Oktober 2026: 48 von 90 Beiträgen waren Wiederholungen mit Slug -2/-3.
    Deshalb zählt jetzt zusätzlich, was in WordPress wirklich steht (auch von Hand
    angelegte Beiträge), und ein leerer Pool bricht ab statt zu wiederholen."""
    published = {
        row[0]
        for row in conn.execute("SELECT topic FROM published WHERE lang = ?", (lang,))
    }
    published |= wp_published_titles()
    available = [(cat, t) for cat, t in TOPICS.get(lang, []) if t not in published]
    return random.choice(available) if available else None


def mark_published(conn: sqlite3.Connection, topic: str, lang: str, wp_post_id: int | None):
    conn.execute(
        "INSERT OR REPLACE INTO published (topic, lang, published_at, wp_post_id) VALUES (?, ?, ?, ?)",
        (topic, lang, datetime.now(timezone.utc).isoformat(), wp_post_id),
    )
    conn.commit()


# ── ARTIKEL GENERIEREN ───────────────────────────────────────────────────────
def _ask(client, system: str, user: str) -> str:
    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{'role': 'user', 'content': user}],
    )
    if message.stop_reason == 'max_tokens':
        raise RuntimeError('Antwort abgeschnitten (max_tokens)')
    if message.stop_reason == 'refusal':
        raise RuntimeError('Modell hat abgelehnt')
    text = ''.join(b.text for b in message.content if getattr(b, 'type', '') == 'text').strip()
    log.info("Antwort: %d Zeichen | %d Output-Tokens | %s", len(text), message.usage.output_tokens, message.stop_reason)
    return text


def generate_article(category: str, title: str, lang: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    heute = datetime.now().strftime('%d.%m.%Y')
    user_prompt = (
        f'Heute ist der {heute}.\n'
        f'Schreibe einen ausführlichen, hochwertigen Ratgeber-Artikel mit dem Titel:\n'
        f'"{title}"\n\n'
        f'Kategorie: {category}\n\n'
        f'Anforderungen:\n'
        f'- 1.200 bis 1.800 Wörter echten Inhalt\n'
        f'- Mindestens 3 aussagekräftige H2-Abschnitte\n'
        f'- Eine Vergleichstabelle (wenn zum Thema passend)\n'
        f'- Praxisnahe Beispiele; Zahlen nur nach den Regeln oben\n'
        f'- Interne Links nur, wo sie zum Thema passen\n\n'
        f'Liefere nur den HTML-Artikelinhalt (ab H2), ohne Einleitung oder Erklärungen.'
    )
    log.info("Generiere Artikel: '%s' (Modell %s)", title, MODEL)
    content = _ask(client, SYSTEM_PROMPT_DE, user_prompt)
    return re.sub(r'^```(?:html)?\s*|\s*```$', '', content).strip()


def faktencheck(title: str, content: str) -> tuple[bool, list[str], str]:
    """Zweiter, unabhängiger Durchgang. Gibt (freigabe, probleme, korrigierter_html) zurück."""
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    antwort = _ask(client, SYSTEM_PRUEFUNG, f'Titel: {title}\n\n{content}')
    m_p = re.search(r'<pruefung>\s*(\{.*?\})\s*</pruefung>', antwort, re.S)
    m_a = re.search(r'<artikel>\s*(.*?)\s*</artikel>', antwort, re.S)
    if not m_p or not m_a:
        return False, ['Faktencheck-Antwort nicht lesbar'], content
    try:
        p = json.loads(m_p.group(1))
    except json.JSONDecodeError:
        return False, ['Faktencheck-JSON nicht lesbar'], content
    html = m_a.group(1).strip()
    # Alles vor der ersten Überschrift weg (z. B. ein mitkopiertes „Titel: …“)
    i = html.find('<h2')
    if i > 0:
        html = html[i:]
    return bool(p.get('freigabe')), [str(x) for x in p.get('probleme', [])], html


def qualitaet(content: str) -> list[str]:
    """Prüfungen im Code – jede Beanstandung hält den Artikel als Entwurf zurück."""
    gruende = []
    text = re.sub(r'<[^>]+>', ' ', content)
    woerter = len(text.split())
    if woerter < MIN_WOERTER:
        gruende.append(f'zu kurz ({woerter} Wörter)')
    m = META_MUSTER.search(text)
    if m:
        gruende.append(f'KI-Meta-Satz: „{m.group(0)}“')
    if 'ersetzt keine individuelle Versicherungsberatung' not in text:
        gruende.append('Hinweis-Satz am Ende fehlt (vermutlich abgeschnitten)')
    if not re.search(r'</(?:p|ul|ol|table)>\s*$', content.strip()):
        gruende.append('endet nicht mit einem vollständigen Absatz (abgeschnitten?)')
    if not content.lstrip().startswith('<h2'):
        gruende.append('beginnt nicht mit einer Zwischenüberschrift (Vorspann/„Titel:“ im Text?)')
    if re.search(r'<h1\b|^#{1,3} ', content, re.M):
        gruende.append('falsches Format (h1 oder Markdown)')
    for v in ANDERE_VERSICHERER:
        if re.search(r'\b' + re.escape(v.strip()) + r'\b', text):
            gruende.append(f'nicht erlaubter Versicherer: {v.strip()}')
    for tag in ('table', 'ul', 'ol'):
        if content.count(f'<{tag}') != content.count(f'</{tag}>'):
            gruende.append(f'unvollständiges HTML ({tag})')
    return gruende


def erzeugen(category: str, title: str, lang: str) -> tuple[str, list[str], list[str]]:
    """Schreiben → Faktencheck → Qualitätsprüfung. Gibt (html, gruende, probleme) zurück."""
    content = generate_article(category, title, lang)
    freigabe, probleme, geprueft = faktencheck(title, content)
    for p in probleme:
        log.info("Faktencheck: %s", p)
    gruende = qualitaet(geprueft)
    if not freigabe:
        gruende.append('Faktencheck nicht bestanden')
    return geprueft, gruende, probleme


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
    parser.add_argument('--repair', type=str, default=None,
                        help='Kommagetrennte WordPress-Post-IDs neu schreiben (URL bleibt gleich)')
    args = parser.parse_args()

    required_vars = ['ANTHROPIC_API_KEY', 'WP_URL', 'WP_USER', 'WP_APP_PASSWORD']
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        log.error("Fehlende .env-Variablen: %s", ', '.join(missing))
        sys.exit(1)

    conn = init_db()

    if args.repair:
        fehler = 0
        for pid in [int(x) for x in args.repair.split(',') if x.strip()]:
            post = get_post(pid)
            title = re.sub(r'<[^>]+>', '', post['title']['raw'] if 'raw' in post['title'] else post['title']['rendered'])
            cat_slug = 'gkv-ratgeber'
            for c, t in TOPICS['de']:
                if t == title:
                    cat_slug = c
            log.info("── Reparatur Beitrag %d: %s", pid, title)
            try:
                content, gruende, _ = erzeugen(cat_slug, title, 'de')
            except Exception as e:
                log.error("Reparatur %d fehlgeschlagen: %s", pid, e); fehler += 1; continue
            if gruende:
                log.error("Reparatur %d nicht übernommen (alter Text bleibt): %s", pid, '; '.join(gruende)); fehler += 1; continue
            content = append_author_box(content)
            meta = build_meta(title, content, 'de')
            if args.dry_run:
                print(content[:800]); continue
            update_post_content(pid, content, excerpt=meta['excerpt'])
            log.info("✓ Beitrag %d repariert (~%d Wörter)", pid, meta['word_count'])
        sys.exit(1 if fehler else 0)

    if args.topic:
        pool = TOPICS.get(args.lang, [])
        match = [(c, t) for c, t in pool if args.topic.lower() in t.lower()]
        if not match:
            log.error("Thema nicht gefunden: %s", args.topic)
            sys.exit(1)
        category, title = match[0]
    else:
        picked = pick_topic(conn, args.lang)
        if not picked:
            log.error("Keine neuen Themen mehr für '%s' – TOPICS erweitern. Es wird nichts veröffentlicht.", args.lang)
            sys.exit(1)
        category, title = picked

    log.info("── Artikel-Generator gestartet ────────────────────")
    log.info("Sprache:   DE")
    log.info("Kategorie: %s", category)
    log.info("Titel:     %s", title)

    try:
        content, gruende, probleme = erzeugen(category, title, args.lang)
        if gruende and not args.topic:
            # Ein zweiter Versuch mit neuem Thema, damit der Tag nicht leer bleibt; das erste wird Entwurf
            log.warning("Versuch 1 nur Entwurf (%s) – speichere Entwurf, neuer Versuch", '; '.join(gruende))
            if not args.dry_run:
                c1 = append_author_box(content); m1 = build_meta(title, c1, args.lang)
                pid1 = publish_to_wordpress(title=title, content=c1, category_slug=category, tags=m1['tags'],
                                            excerpt=m1['excerpt'], slug=m1['slug'], lang=args.lang, status='draft')
                mark_published(conn, title, args.lang, pid1)
            nxt = pick_topic(conn, args.lang)
            if nxt:
                category, title = nxt
                log.info("Neues Thema: %s", title)
                content, gruende, probleme = erzeugen(category, title, args.lang)
    except (anthropic.APIError, RuntimeError) as e:
        log.error("Claude API Fehler: %s", e)
        sys.exit(1)

    status = 'draft' if gruende else 'publish'
    if gruende:
        log.warning("Nur als ENTWURF gespeichert – Gründe: %s", '; '.join(gruende))

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
        print(f"Status: {status} {'; '.join(gruende)}")
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
            status=status,
        )
        mark_published(conn, title, args.lang, wp_post_id)
        log.info("✓ %s: WP Post ID %d", 'Veröffentlicht' if status == 'publish' else 'Entwurf', wp_post_id)
    except Exception as e:
        log.error("WordPress-Fehler: %s", e)
        sys.exit(1)

    log.info("── Fertig ─────────────────────────────────────────")


if __name__ == '__main__':
    main()
