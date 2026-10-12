<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
  <meta charset="<?php bloginfo('charset'); ?>">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <?php wp_head(); ?>
<script src="/analytics.js" defer data-ga="G-XXXXXXXXXX" data-umami="2a962e6a-2b9d-4850-951d-2b23afafef3c" data-umami-src="https://stats.pilsner-vertrieb.de/script.js" data-privacy="/datenschutz/" data-accent="#0057ff"></script>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<header class="site-header">
  <div class="container nav-inner">
    <a class="site-title" href="https://krankenzusatz-vergleich.de/">
      kranken<span>zusatz</span>-vergleich.de
    </a>
    <nav aria-label="Hauptmenü">
      <?php wp_nav_menu([
        'theme_location' => 'primary',
        'menu_class'     => 'nav-menu',
        'container'      => false,
        'fallback_cb'    => function () {
          echo '<ul class="nav-menu">
            <li><a href="https://krankenzusatz-vergleich.de/#kategorien">Tarife</a></li>
            <li><a href="https://krankenzusatz-vergleich.de/#vergleich">Vergleich</a></li>
            <li><a href="https://krankenzusatz-vergleich.de/#faq">FAQ</a></li>
            <li><a href="' . get_bloginfo('url') . '">Ratgeber</a></li>
          </ul>';
        },
      ]); ?>
    </nav>
    <a class="nav-cta" href="https://krankenzusatz-vergleich.de/#vergleich-starten">
      Jetzt vergleichen
    </a>
  </div>
</header>
