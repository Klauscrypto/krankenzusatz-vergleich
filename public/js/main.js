// Blog-Beiträge laden (später aus API/CMS)
const posts = [
  {
    title: "Zahnzusatzversicherung: Was lohnt sich 2026?",
    excerpt: "Wir zeigen, worauf Sie beim Abschluss achten sollten und welche Leistungen wirklich wichtig sind.",
    date: "28.06.2026"
  },
  {
    title: "Brillenversicherung im Vergleich",
    excerpt: "Sehhilfen können teuer werden – eine Zusatzversicherung kann sich schnell amortisieren.",
    date: "20.06.2026"
  },
  {
    title: "Heilpraktiker-Zusatzversicherung erklärt",
    excerpt: "Immer mehr Menschen nutzen alternative Heilmethoden. Was übernimmt die Zusatzversicherung?",
    date: "10.06.2026"
  }
];

const grid = document.getElementById("blog-grid");
if (grid) {
  posts.forEach(post => {
    grid.innerHTML += `
      <article class="blog-card">
        <h3>${post.title}</h3>
        <p>${post.excerpt}</p>
        <p class="date">${post.date}</p>
      </article>`;
  });
}
