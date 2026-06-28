<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="footer-logo">kranken<span>zusatz</span>-vergleich.de</div>
        <p class="footer-desc">
          Unabhängiger Vergleich für Krankenzusatzversicherungen.
          Täglich aktualisiert. DSGVO-konform.
        </p>
      </div>
      <div>
        <h4>Versicherungen</h4>
        <ul>
          <li><a href="<?php echo get_term_link('zahnzusatz', 'category'); ?>">Zahnzusatz</a></li>
          <li><a href="<?php echo get_term_link('krankenhaus', 'category'); ?>">Krankenhaus</a></li>
          <li><a href="<?php echo get_term_link('auslandsreise', 'category'); ?>">Auslandsreise</a></li>
          <li><a href="<?php echo get_term_link('heilpraktiker', 'category'); ?>">Heilpraktiker</a></li>
        </ul>
      </div>
      <div>
        <h4>Rechtliches</h4>
        <ul>
          <li><a href="<?php echo get_permalink(get_page_by_path('impressum')); ?>">Impressum</a></li>
          <li><a href="<?php echo get_permalink(get_page_by_path('datenschutz')); ?>">Datenschutz</a></li>
          <li><a href="https://krankenzusatz-vergleich.de/">Zur Startseite</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; <?php echo date('Y'); ?> krankenzusatz-vergleich.de
        &nbsp;·&nbsp; Alle Angaben ohne Gewähr &nbsp;·&nbsp; Kein Finanzberatungsersatz
      </span>
      <div class="footer-legal">
        <a href="<?php echo get_permalink(get_page_by_path('impressum')); ?>">Impressum</a>
        <a href="<?php echo get_permalink(get_page_by_path('datenschutz')); ?>">Datenschutz</a>
      </div>
    </div>
  </div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
