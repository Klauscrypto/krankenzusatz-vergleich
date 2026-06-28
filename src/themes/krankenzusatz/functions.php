<?php
// Theme-Setup
add_action('after_setup_theme', function () {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', ['comment-list', 'comment-form', 'search-form', 'gallery', 'caption']);
    add_theme_support('custom-logo');

    register_nav_menus([
        'primary' => 'Hauptmenü',
        'footer'  => 'Footer-Menü',
    ]);
});

// Styles & Scripts
add_action('wp_enqueue_scripts', function () {
    wp_enqueue_style(
        'krankenzusatz-style',
        get_stylesheet_uri(),
        [],
        wp_get_theme()->get('Version')
    );
    // Google Fonts: Inter
    wp_enqueue_style(
        'inter-font',
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap',
        [],
        null
    );
});

// Sidebar registrieren
add_action('widgets_init', function () {
    register_sidebar([
        'name'          => 'Blog Sidebar',
        'id'            => 'sidebar-1',
        'before_widget' => '<div class="widget">',
        'after_widget'  => '</div>',
        'before_title'  => '<h3>',
        'after_title'   => '</h3>',
    ]);
});

// Excerpt-Länge
add_filter('excerpt_length', fn() => 30);
add_filter('excerpt_more',   fn() => '…');

// Kategorie-Emoji-Map für Post-Thumbs
function kz_cat_emoji(int $post_id): string {
    $map = [
        'zahnzusatz'      => '🦷',
        'krankenhaus'     => '🏥',
        'auslandsreise'   => '✈️',
        'heilpraktiker'   => '🌿',
        'sehhilfen'       => '👁️',
        'vorsorge'        => '🧘',
        'expat-guide'     => '🌍',
        'gkv-ratgeber'    => '📋',
    ];
    $cats = get_the_category($post_id);
    foreach ($cats as $cat) {
        if (isset($map[$cat->slug])) {
            return $map[$cat->slug];
        }
    }
    return '📝';
}

// Kategorie-CSS-Klasse für Post-Thumb
function kz_cat_class(int $post_id): string {
    $cats = get_the_category($post_id);
    if (!empty($cats)) {
        return 'cat-' . sanitize_html_class($cats[0]->slug);
    }
    return 'cat-default';
}

// REST API: Application Passwords aktivieren
add_filter('wp_is_application_passwords_available', '__return_true');

// REST API: CORS für Artikel-Generator
add_action('rest_api_init', function () {
    remove_filter('rest_pre_serve_request', 'rest_send_cors_headers');
    add_filter('rest_pre_serve_request', function ($value) {
        header('Access-Control-Allow-Origin: *');
        header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
        header('Access-Control-Allow-Headers: Authorization, Content-Type');
        return $value;
    });
}, 15);

// Yoast SEO: automatisch Meta aus Post-Content übernehmen
add_filter('wpseo_metadesc', function ($desc) {
    if (empty($desc) && is_singular()) {
        $desc = wp_trim_words(get_the_excerpt(), 30);
    }
    return $desc;
});

// Automatisches CTA-Block ans Ende jedes Artikels hängen
add_filter('the_content', function (string $content): string {
    if (!is_single()) {
        return $content;
    }
    $cta = '<div class="cta-block">
        <h3>Jetzt kostenlos Tarife vergleichen</h3>
        <p>Finde die beste Krankenzusatzversicherung – unabhängig, täglich aktuell, kostenlos.</p>
        <a href="https://krankenzusatz-vergleich.de/#vergleich-starten">⚡ Jetzt vergleichen →</a>
    </div>';
    return $content . $cta;
});

// Automatische interne Verlinkung: "Krankenzusatzversicherung" im Text → Landingpage
add_filter('the_content', function (string $content): string {
    if (!is_single()) {
        return $content;
    }
    static $done = false;
    if ($done) return $content;
    $done = true;

    $link = '<a href="https://krankenzusatz-vergleich.de/">Krankenzusatzversicherung</a>';
    // Nur erste Erwähnung verlinken (nicht in headings oder bereits verlinktem Text)
    $content = preg_replace(
        '/(?<!<a[^>]*>)(?<![">])Krankenzusatzversicherung(?![^<]*<\/a>)/',
        $link,
        $content,
        1
    );
    return $content;
});
