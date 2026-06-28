"""
publish_artikel.py – Aufgabe 6
WordPress REST API Integration: veröffentlicht Artikel via POST /wp-json/wp/v2/posts
"""

import os
import logging
import requests
from requests.auth import HTTPBasicAuth

log = logging.getLogger(__name__)

# ── KATEGORIE-SLUG → WP-TERM-ID CACHE ───────────────────────────
_cat_id_cache: dict[str, int] = {}


def _wp_auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(
        os.environ['WP_USER'],
        os.environ['WP_APP_PASSWORD'],
    )


def _wp_url(path: str) -> str:
    base = os.environ['WP_URL'].rstrip('/')
    return f"{base}/blog/wp-json/wp/v2/{path}"


def get_or_create_category(slug: str) -> int:
    """Gibt WP-Kategorie-ID zurück, erstellt Kategorie bei Bedarf."""
    if slug in _cat_id_cache:
        return _cat_id_cache[slug]

    # Suchen
    r = requests.get(_wp_url('categories'), params={'slug': slug, 'per_page': 1},
                     auth=_wp_auth(), timeout=15)
    r.raise_for_status()
    data = r.json()

    if data:
        cat_id = data[0]['id']
    else:
        # Erstellen
        name_map = {
            'zahnzusatz':    'Zahnzusatzversicherung',
            'krankenhaus':   'Krankenhausversicherung',
            'auslandsreise': 'Auslandsreisekrankenversicherung',
            'heilpraktiker': 'Heilpraktiker & Alternativmedizin',
            'sehhilfen':     'Sehhilfen & Brillenversicherung',
            'vorsorge':      'Vorsorge & Gesundheit',
            'expat-guide':   'Expat Guide',
            'gkv-ratgeber':  'GKV Ratgeber',
        }
        r = requests.post(
            _wp_url('categories'),
            json={'name': name_map.get(slug, slug.replace('-', ' ').title()), 'slug': slug},
            auth=_wp_auth(), timeout=15,
        )
        r.raise_for_status()
        cat_id = r.json()['id']
        log.info("Neue Kategorie erstellt: %s (ID %d)", slug, cat_id)

    _cat_id_cache[slug] = cat_id
    return cat_id


def get_or_create_tags(tag_names: list[str]) -> list[int]:
    """Gibt WP-Tag-IDs zurück, erstellt fehlende Tags."""
    tag_ids = []
    for name in tag_names:
        r = requests.get(_wp_url('tags'), params={'search': name, 'per_page': 1},
                         auth=_wp_auth(), timeout=15)
        r.raise_for_status()
        data = r.json()

        if data and data[0]['name'].lower() == name.lower():
            tag_ids.append(data[0]['id'])
        else:
            r = requests.post(
                _wp_url('tags'),
                json={'name': name},
                auth=_wp_auth(), timeout=15,
            )
            if r.status_code in (200, 201):
                tag_ids.append(r.json()['id'])
            else:
                log.warning("Tag nicht erstellt: %s – %s", name, r.text[:100])

    return tag_ids


def publish_to_wordpress(
    title:         str,
    content:       str,
    category_slug: str,
    tags:          list[str],
    excerpt:       str,
    slug:          str,
    lang:          str = 'de',
) -> int:
    """
    Veröffentlicht einen Artikel in WordPress via REST API.
    Gibt die WordPress Post-ID zurück.
    """
    cat_id  = get_or_create_category(category_slug)
    tag_ids = get_or_create_tags(tags)

    payload = {
        'title':      title,
        'content':    content,
        'excerpt':    excerpt,
        'slug':       slug,
        'status':     'publish',
        'categories': [cat_id],
        'tags':       tag_ids,
        'meta': {
            'yoast_wpseo_metadesc':    excerpt[:155],
            'yoast_wpseo_focuskw':     title.split(':')[0].strip(),
        },
    }

    # Sprachmarkierung für Polylang (wenn EN-Artikel)
    if lang == 'en':
        payload['lang'] = 'en'

    log.info("Veröffentliche in WordPress: '%s' [%s]", title, lang.upper())

    r = requests.post(
        _wp_url('posts'),
        json=payload,
        auth=_wp_auth(),
        timeout=30,
    )

    if r.status_code not in (200, 201):
        log.error("WordPress API Fehler %d: %s", r.status_code, r.text[:300])
        r.raise_for_status()

    post = r.json()
    log.info("Artikel veröffentlicht: ID %d → %s", post['id'], post.get('link', ''))
    return post['id']
