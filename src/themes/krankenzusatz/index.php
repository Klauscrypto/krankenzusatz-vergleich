<?php get_header(); ?>

<section class="page-header">
  <div class="container">
    <p class="eyebrow">Ratgeber & Aktuelles</p>
    <h1>
      <?php
      if (is_category()) {
          single_cat_title();
      } elseif (is_tag()) {
          echo 'Tag: '; single_tag_title();
      } elseif (is_search()) {
          echo 'Suchergebnisse: ' . get_search_query();
      } else {
          echo 'Alle Ratgeber-Artikel';
      }
      ?>
    </h1>
    <p class="subtitle">Täglich neue Beiträge zu Krankenzusatzversicherungen – auf Deutsch und Englisch.</p>
  </div>
</section>

<main>
  <div class="container">
    <div class="blog-layout">

      <!-- Artikel-Liste -->
      <div>
        <?php if (have_posts()) : ?>
          <div class="post-list">
            <?php while (have_posts()) : the_post(); ?>
              <article class="post-card">
                <div class="post-thumb <?php echo kz_cat_class(get_the_ID()); ?>">
                  <?php echo kz_cat_emoji(get_the_ID()); ?>
                </div>
                <div class="post-body">
                  <?php
                  $cats = get_the_category();
                  if ($cats) {
                      echo '<a class="post-tag" href="' . get_category_link($cats[0]->term_id) . '">'
                         . esc_html($cats[0]->name) . '</a>';
                  }
                  ?>
                  <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
                  <p class="post-excerpt"><?php the_excerpt(); ?></p>
                  <div class="post-meta">
                    <span><?php echo get_the_date('d. F Y'); ?></span>
                    <a class="read-more" href="<?php the_permalink(); ?>">Weiterlesen →</a>
                  </div>
                </div>
              </article>
            <?php endwhile; ?>
          </div>

          <!-- Pagination -->
          <div class="pagination">
            <?php
            echo paginate_links([
              'prev_text' => '‹',
              'next_text' => '›',
              'type'      => 'list',
            ]);
            ?>
          </div>

        <?php else : ?>
          <p style="padding:40px 0; color:var(--ink-mute);">
            Keine Artikel gefunden. Der Artikel-Generator startet in Kürze.
          </p>
        <?php endif; ?>
      </div>

      <!-- Sidebar -->
      <aside class="sidebar">
        <!-- CTA-Widget -->
        <div class="widget widget-cta">
          <h3>Jetzt kostenlos vergleichen</h3>
          <p>340+ Tarife täglich geprüft. Kein Callcenter. 2 Minuten.</p>
          <a href="https://krankenzusatz-vergleich.de/#vergleich-starten">⚡ Tarife vergleichen</a>
        </div>

        <!-- Kategorien -->
        <div class="widget">
          <h3>Themen</h3>
          <ul>
            <?php
            wp_list_categories([
              'show_count'  => true,
              'hide_empty'  => false,
              'title_li'    => '',
              'orderby'     => 'count',
              'order'       => 'DESC',
            ]);
            ?>
          </ul>
        </div>

        <!-- Neueste Artikel -->
        <div class="widget">
          <h3>Neueste Artikel</h3>
          <ul>
            <?php
            $recent = get_posts(['numberposts' => 5, 'post_status' => 'publish']);
            foreach ($recent as $post) :
              setup_postdata($post);
            ?>
              <li><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></li>
            <?php
            endforeach;
            wp_reset_postdata();
            ?>
          </ul>
        </div>

        <!-- EN-Version Hinweis -->
        <div class="widget">
          <h3>🇬🇧 English Version</h3>
          <ul>
            <li><a href="https://krankenzusatz-vergleich.de/en/">Expat Guide (EN)</a></li>
            <li><a href="<?php bloginfo('url'); ?>/en/">English Blog Posts</a></li>
          </ul>
        </div>
      </aside>

    </div>
  </div>
</main>

<?php get_footer(); ?>
