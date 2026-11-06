<?php
/**
 * Plugin Name: Tarifrechner-Kasten unter Blogartikeln
 * Description: Haengt unter jeden Artikel die passenden Original-Tarifrechner von DKV und Signal Iduna (Partnerlinks Bloemecke).
 *
 * Thema nach Kategorie, Reise/Ausland zusaetzlich nach Titel. Gilt fuer alte und neue Beitraege,
 * ohne den Text der Beitraege zu aendern. Prioritaet 9: steht vor dem allgemeinen CTA des Themes.
 * Links: DKV Vermittlernummer 10004762, Signal Iduna advnr 7157241 (Mail Alex, 01.07.2026).
 * Quelle im Repo: src/mu-plugins/ (Deploy per GitHub Actions).
 */

function kz_rechner_links(): array {
    $dkv = 'https://www.beitragsrechner.dkv.com/tarifrechner/400140/%s?oenr=10004762';
    $si  = 'https://signal-iduna.de/rechner/%s?advnr=7157241';
    return [
        'zahn' => [
            'titel' => 'Zahnzusatz: Beitrag jetzt selbst berechnen',
            'links' => [
                ['DKV Zahntarif Z100', sprintf($dkv, 'Z100')],
                ['DKV Zahntarif Z80', sprintf($dkv, 'Z80')],
                ['Signal Iduna Zahnrechner', sprintf($si, 'zahn/beitrag/grunddaten')],
            ],
            'mehr' => '/dkv/#zahn',
        ],
        'stationaer' => [
            'titel' => 'Krankenhauszusatz: Beitrag jetzt selbst berechnen',
            'links' => [
                ['DKV Krankenhaustarif KS2', sprintf($dkv, 'KS2')],
                ['DKV Krankenhaustarif KS1', sprintf($dkv, 'KS1')],
                ['Signal Iduna stationär', sprintf($si, 'stationaer/beitrag/geburtsdatum')],
            ],
            'mehr' => '/dkv/#stationaer',
        ],
        'ambulant' => [
            'titel' => 'Ambulante Zusatzversicherung: Beitrag jetzt selbst berechnen',
            'links' => [
                ['Signal Iduna ambulant', sprintf($si, 'ambulant/beitrag/grunddaten-geburtsdatum')],
                ['DKV ambulante Tarife', '/dkv/#ambulant'],
            ],
            'mehr' => '/dkv/#ambulant',
        ],
        'reise' => [
            'titel' => 'Auslandsreise-Krankenversicherung: Beitrag jetzt berechnen',
            'links' => [
                ['DKV Reisetarif RDE', sprintf($dkv, 'RDE')],
                ['Signal Iduna Reiserechner', 'https://signal-iduna.de/rechner/reise/kranken?adp=true&advnr=7157241'],
            ],
            'mehr' => '/dkv/#reise',
        ],
        'allgemein' => [
            'titel' => 'Beitrag selbst berechnen und online abschließen',
            'links' => [
                ['Alle DKV-Tarifrechner', '/dkv/'],
                ['Alle Signal-Iduna-Rechner', '/signal-iduna/'],
            ],
            'mehr' => '',
        ],
    ];
}

function kz_rechner_thema(int $post_id): string {
    $titel = mb_strtolower(get_the_title($post_id));
    if (preg_match('/reise|ausland|urlaub/u', $titel)) return 'reise';
    $slugs = wp_list_pluck(get_the_category($post_id) ?: [], 'slug');
    if (in_array('zahnzusatz', $slugs, true)) return 'zahn';
    if (in_array('krankenhaus', $slugs, true)) return 'stationaer';
    if (array_intersect(['heilpraktiker', 'sehhilfen', 'vorsorge'], $slugs)) return 'ambulant';
    if (preg_match('/zahn/u', $titel)) return 'zahn';
    if (preg_match('/krankenhaus|stationär|chefarzt|einbettzimmer/u', $titel)) return 'stationaer';
    return 'allgemein';
}

add_filter('the_content', function (string $content): string {
    if (!is_single() || !in_the_loop() || !is_main_query()) return $content;
    $alle  = kz_rechner_links();
    $box   = $alle[kz_rechner_thema(get_the_ID())];
    $knopf = '';
    foreach ($box['links'] as [$text, $url]) {
        $extern = str_starts_with($url, 'http') ? ' target="_blank" rel="noopener"' : '';
        $knopf .= '<a href="' . esc_url($url) . '"' . $extern
            . ' style="display:inline-block;margin:6px 8px 0 0;padding:11px 16px;border-radius:10px;background:var(--accent,#0057ff);color:#fff;font-weight:700;text-decoration:none;font-size:.92rem;">'
            . esc_html($text) . ' →</a>';
    }
    $mehr = $box['mehr']
        ? ' <a href="' . esc_url($box['mehr']) . '">Alle passenden Tarife ansehen</a>.'
        : '';
    $html = '<div class="kz-rechner" style="margin:36px 0 8px;padding:22px 24px;border-radius:12px;background:#f5f8fc;border:1.5px solid #dfe7f3;">'
        . '<h3 style="margin:0 0 6px;font-size:1.1rem;">' . esc_html($box['titel']) . '</h3>'
        . '<p style="margin:0 0 6px;color:#5a6b80;font-size:.93rem;">Mit den offiziellen Rechnern von DKV und Signal Iduna: Beitrag sofort sehen, Antrag direkt online stellen. Gleicher Preis wie beim Direktabschluss, mit persönlicher Betreuung durch Blömecke &amp; Partner.' . $mehr . '</p>'
        . $knopf . '</div>';
    return $content . $html;
}, 9);
