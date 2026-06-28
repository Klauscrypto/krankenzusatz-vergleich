<?php get_header(); ?>

<main class="single-layout">
  <div class="container--narrow">

    <?php while (have_posts()) : the_post(); ?>

      <article class="post-header">
        <?php
        $cats = get_the_category();
        if ($cats) {
            echo '<a class="post-tag" href="' . get_category_link($cats[0]->term_id) . '">'
               . esc_html($cats[0]->name) . '</a>';
        }
        ?>
        <h1><?php the_title(); ?></h1>
        <p class="post-intro"><?php echo wp_trim_words(get_the_excerpt(), 40); ?></p>
        <div class="post-meta">
          <span><?php echo get_the_date('d. F Y'); ?></span>
          <span><?php echo ceil(str_word_count(strip_tags(get_the_content())) / 200); ?> Min. Lesezeit</span>
        </div>
      </article>

      <div class="entry-content">
        <?php the_content(); ?>
      </div>

      <!-- Tags -->
      <?php
      $tags = get_the_tags();
      if ($tags) :
      ?>
        <div style="margin-top:32px; display:flex; gap:8px; flex-wrap:wrap;">
          <?php foreach ($tags as $tag) : ?>
            <a href="<?php echo get_tag_link($tag); ?>"
               style="background:#eef3ff;color:var(--accent);padding:4px 10px;border-radius:20px;font-size:.78rem;font-weight:600;text-decoration:none;">
              #<?php echo esc_html($tag->name); ?>
            </a>
          <?php endforeach; ?>
        </div>
      <?php endif; ?>

      <!-- Verwandte Artikel -->
      <?php
      $related = get_posts([
        'category__in'   => wp_get_post_categories(get_the_ID()),
        'post__not_in'   => [get_the_ID()],
        'numberposts'    => 3,
        'post_status'    => 'publish',
        'orderby'        => 'rand',
      ]);
      if ($related) :
      ?>
        <div style="margin-top:48px; border-top:1px solid var(--border); padding-top:32px;">
          <h2 style="font-size:1.1rem; margin-bottom:16px;">Weitere Artikel</h2>
          <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px;">
            <?php foreach ($related as $p) : ?>
              <a href="<?php echo get_permalink($p); ?>"
                 style="background:var(--surface);border:1.5px solid var(--border);border-radius:var(--radius);padding:16px;text-decoration:none;color:var(--ink);font-size:.88rem;font-weight:600;transition:border-color .2s;"
                 onmouseover="this.style.borderColor='var(--accent)'"
                 onmouseout="this.style.borderColor='var(--border)'">
                <?php echo esc_html($p->post_title); ?>
              </a>
            <?php endforeach; ?>
          </div>
        </div>
      <?php endif; ?>

    <?php endwhile; ?>

  </div>
</main>

<?php get_footer(); ?>
