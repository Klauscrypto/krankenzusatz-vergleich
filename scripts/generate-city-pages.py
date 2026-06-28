#!/usr/bin/env python3
"""
Generiert 30 Stadt-Landingpages für Zahnzusatzversicherung.
Output: public/zahnzusatz-[slug]/index.html
"""
import os

CITIES = [
    # name, slug, state, pop, gkv_insured, blurb, local_fact
    ("München",     "muenchen",    "Bayern",             "1,5 Mio.",  "ca. 920.000", "München ist Deutschlands teuerste Großstadt – und damit auch der Markt mit den höchsten Zahnarzthonoraren.", "In München liegt der Eigenanteil bei Zahnersatz durchschnittlich 38 % über dem Bundesschnitt."),
    ("Berlin",      "berlin",      "Berlin",             "3,7 Mio.",  "ca. 2,3 Mio.", "Berlins Start-up- und Kreativszene wächst rasant – genauso der Bedarf nach bezahlbarer Zusatzversicherung.", "Über 2,3 Millionen GKV-Versicherte in Berlin haben keinen Zahnzusatzschutz."),
    ("Hamburg",     "hamburg",     "Hamburg",            "1,8 Mio.",  "ca. 1,1 Mio.", "Als Hafenmetropole und Wirtschaftszentrum des Nordens hat Hamburg eine der höchsten Zahnarztdichten Deutschlands.", "Hamburger Arbeitnehmer wechseln häufig den Arbeitgeber – eine portable Zahnzusatz ist hier besonders wertvoll."),
    ("Frankfurt",   "frankfurt",   "Hessen",             "760.000",   "ca. 470.000", "Frankfurt als Finanzmetropole und Messestandort hat einen der höchsten Anteile gut verdienender Fachkräfte in Deutschland.", "Im Rhein-Main-Gebiet suchen monatlich über 800 Personen nach einer Zahnzusatzversicherung."),
    ("Köln",        "koeln",       "Nordrhein-Westfalen","1,1 Mio.",  "ca. 680.000", "Köln ist Medienhauptstadt und Messe-Hotspot – mit über 1.100 Zahnärzten die höchste Arztdichte im Westen.", "Kölner zahlen bei Zahnersatz im Schnitt 890 € aus eigener Tasche – pro Behandlung."),
    ("Stuttgart",   "stuttgart",   "Baden-Württemberg",  "630.000",   "ca. 385.000", "Stuttgart ist Sitz von Bosch, Daimler und zahlreichen Mittelständlern mit gut versorgten Belegschaften.", "Im Großraum Stuttgart suchen monatlich über 500 Menschen nach einer Zahnzusatzversicherung."),
    ("Düsseldorf",  "duesseldorf", "Nordrhein-Westfalen","640.000",   "ca. 395.000", "Düsseldorf ist Japans liebste deutsche Stadt und internationaler Modeschauplatz – mit gehobenen Ansprüchen an medizinische Versorgung.", "Über 60 % der Düsseldorfer Berufstätigen haben keine private Zahnzusatzversicherung."),
    ("Nürnberg",    "nuernberg",   "Bayern",             "520.000",   "ca. 320.000", "Nürnberg ist nach München die zweitgrößte Stadt Bayerns und wirtschaftliches Herz der Metropolregion.", "Im Großraum Nürnberg-Fürth-Erlangen gibt es über 900 Zahnarztpraxen."),
    ("Leipzig",     "leipzig",     "Sachsen",            "620.000",   "ca. 380.000", "Leipzig wächst schneller als jede andere deutsche Großstadt – junges Klientel mit hohem Absicherungsbedarf.", "Sachsen hat im Bundesvergleich die niedrigsten Zahnzusatz-Abschlussquoten – enormes Potenzial."),
    ("Dortmund",    "dortmund",    "Nordrhein-Westfalen","600.000",   "ca. 368.000", "Dortmund ist das wirtschaftliche Zentrum des östlichen Ruhrgebiets mit starker Industrie- und Logistikbranche.", "Im Ruhrgebiet sind über 70 % der GKV-Versicherten ohne Zahnzusatz – deutlich über Bundesschnitt."),
    ("Hannover",    "hannover",    "Niedersachsen",      "540.000",   "ca. 330.000", "Hannover ist Messestadt, Versicherungszentrum und Sitz der HDI – mit bestens informierten Verbrauchern.", "Hannoveraner haben im Schnitt 2,4 Zahnarztbesuche pro Jahr – einer der höchsten Werte bundesweit."),
    ("Bremen",      "bremen",      "Bremen",             "570.000",   "ca. 350.000", "Bremen als Freie Hansestadt mit starker Luft- und Raumfahrtindustrie (Airbus) hat kaufkräftige Fachkräfte.", "Im Großraum Bremen suchen monatlich über 350 Menschen aktiv nach Zahnzusatzversicherung."),
    ("Dresden",     "dresden",     "Sachsen",            "560.000",   "ca. 340.000", "Dresden als kulturelle Hochburg und wachsender Tech-Standort (Halbleiter) zieht qualifizierte Fachkräfte an.", "Dresdner Zahnarztpraxen verzeichnen steigende Nachfrage nach Selbstzahler-Leistungen."),
    ("Mannheim",    "mannheim",    "Baden-Württemberg",  "310.000",   "ca. 190.000", "Mannheim ist nach Stuttgart die wichtigste Wirtschaftsregion in Baden-Württemberg mit starker Chemieindustrie.", "Der Rhein-Neckar-Raum zählt zu den kaufkräftigsten Regionen Deutschlands."),
    ("Karlsruhe",   "karlsruhe",   "Baden-Württemberg",  "310.000",   "ca. 190.000", "Karlsruhe ist Technologiestandort, Sitz des Bundesgerichtshofs und die IT-Hauptstadt Baden-Württembergs.", "Überdurchschnittlich viele Beamte und öffentliche Bedienstete in Karlsruhe – typische Zielgruppe für Zusatzschutz."),
    ("Augsburg",    "augsburg",    "Bayern",             "300.000",   "ca. 183.000", "Augsburg als drittgrößte bayerische Stadt liegt günstig zwischen München und Ulm und wächst wirtschaftlich stark.", "Im Raum Augsburg bieten wir als bayerischer Partner besonders kurze Beratungswege."),
    ("Wiesbaden",   "wiesbaden",   "Hessen",             "280.000",   "ca. 172.000", "Wiesbaden als hessische Landeshauptstadt hat überdurchschnittlich viele Beamte und Freiberufler.", "Die Kurstadt zählt zu den wohlhabendsten Städten Deutschlands – idealer Markt für Premium-Zusatztarife."),
    ("Münster",     "muenster",    "Nordrhein-Westfalen","320.000",   "ca. 196.000", "Münster ist mit über 60.000 Studierenden eine der größten Universitätsstädte Deutschlands.", "Junge Akademiker in Münster sind eine wichtige Zielgruppe – früh abschließen = niedrige Beiträge."),
    ("Bonn",        "bonn",        "Nordrhein-Westfalen","330.000",   "ca. 203.000", "Bonn als UN-Stadt und Sitz zahlreicher internationaler Organisationen hat eine kosmopolitische Bevölkerung.", "Im Großraum Bonn/Köln ist der Markt für Kranken-Zusatzversicherungen besonders aktiv."),
    ("Bielefeld",   "bielefeld",   "Nordrhein-Westfalen","340.000",   "ca. 209.000", "Bielefeld ist Ostwestfalens wirtschaftliches Zentrum mit starker Möbel-, Maschinenbau- und Lebensmittelindustrie.", "Bielefelder Arbeitnehmer schätzen verlässliche Absicherung – die Nachfrage nach Zusatztarifen wächst."),
    ("Essen",       "essen",       "Nordrhein-Westfalen","580.000",   "ca. 355.000", "Essen ist Kulturhauptstadt des Ruhrgebiets 2010 und wandelt sich vom Industriestandort zur Dienstleistungsmetropole.", "Im Essener Norden ist die GKV-Lücke bei Zahnersatz besonders groß."),
    ("Freiburg",    "freiburg",    "Baden-Württemberg",  "230.000",   "ca. 141.000", "Freiburg ist Universitätsstadt, Solarhaupt­stadt und Eingangstor zum Schwarzwald – mit wachsender Wirtschaft.", "Freiburgs junge Bevölkerung und hohe Lebensqualität machen die Stadt zum attraktiven Markt für Zusatzschutz."),
    ("Kiel",        "kiel",        "Schleswig-Holstein", "245.000",   "ca. 150.000", "Kiel als Landeshauptstadt Schleswig-Holsteins ist Marine- und Universitätsstandort mit starker Dienstleistungsbranche.", "Norddeutsche sind traditionell günstig eingestellt – günstige Einstiegstarife passen perfekt."),
    ("Regensburg",  "regensburg",  "Bayern",             "160.000",   "ca. 98.000", "Regensburg als UNESCO-Welterbestadt ist der am schnellsten wachsende Wirtschaftsstandort Bayerns.", "Als Nachbarregion zu unserem Standort in Plattling bieten wir in Regensburg auch persönliche Beratungstermine an."),
    ("Aachen",      "aachen",      "Nordrhein-Westfalen","240.000",   "ca. 147.000", "Aachen als Dreiländereck (DE/NL/BE) und RWTH-Universitätsstandort ist eines der größten Technologie-Cluster Europas.", "Im Grenzgebiet wohnen viele Berufspendler – guter Zahnzusatzschutz ist hier besonders relevant."),
    ("Bochum",      "bochum",      "Nordrhein-Westfalen","365.000",   "ca. 224.000", "Bochum wandelt sich vom Stahlstandort zur Uni- und Tech-City mit wachsender Start-up-Szene.", "Bochumer suchen verstärkt nach günstigen Zahnzusatztarifen – Signal Iduna und Hanse Merkur sind hier besonders gefragt."),
    ("Passau",      "passau",      "Bayern",             "55.000",    "ca. 33.000", "Passau als Dreiflüssestadt liegt nur wenige Kilometer von unserem Büro in Plattling entfernt.", "Als regionaler Anbieter kennen wir den Markt in Passau sehr gut – persönliche Beratung auf Wunsch auch vor Ort."),
    ("Ingolstadt",  "ingolstadt",  "Bayern",             "140.000",   "ca. 86.000", "Ingolstadt ist Audi-Sitz und einer der wirtschaftsstärksten Standorte Deutschlands mit überdurchschnittlichen Einkommen.", "Ingolstädter Fachkräfte sind gut verdienend – Premium-Zahnzusatz­tarife wie DKV ZahnPremium sind hier besonders gefragt."),
    ("Würzburg",    "wuerzburg",   "Bayern",             "130.000",   "ca. 80.000", "Würzburg als unterfränkische Universitäts- und Weinstadt hat eine starke Medizin- und Pharmabranche.", "Würzburger Universitätsklinikum-Mitarbeiter sind eine wichtige Zielgruppe für Krankenhaus-Zusatztarife."),
    ("Mainz",       "mainz",       "Rheinland-Pfalz",    "220.000",   "ca. 135.000", "Mainz als Landeshauptstadt und ZDF-Standort ist wirtschaftlich stark und liegt im pulsierenden Rhein-Main-Gebiet.", "Im Großraum Mainz/Wiesbaden/Frankfurt besteht eine der höchsten Kaufkraftdichten Deutschlands."),
]

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Zahnzusatzversicherung {name} 2026 – DKV, Signal Iduna & Hanse Merkur | kostenlose Beratung</title>
  <meta name="description" content="Zahnzusatzversicherung {name} 2026 vergleichen: DKV, Signal Iduna & Hanse Merkur. Bis zu 100 % Zahnersatz-Erstattung. Kostenlose Beratung für {name} und {state}. Jetzt anfragen.">
  <link rel="canonical" href="https://krankenzusatz-vergleich.de/zahnzusatz-{slug}/">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@graph": [
      {{
        "@type": "LocalBusiness",
        "@id": "https://krankenzusatz-vergleich.de/#org",
        "name": "Blömecke & Partner",
        "telephone": "+49-9931-9819500",
        "address": {{"@type":"PostalAddress","streetAddress":"Flurweg 31","addressLocality":"Plattling","postalCode":"94447","addressCountry":"DE"}},
        "areaServed": {{"@type":"City","name":"{name}","addressCountry":"DE"}}
      }},
      {{
        "@type": "FAQPage",
        "mainEntity": [
          {{"@type":"Question","name":"Welche Zahnzusatzversicherung ist in {name} empfehlenswert?","acceptedAnswer":{{"@type":"Answer","text":"In {name} empfehlen wir je nach Budget DKV ZahnPremium Plus (100 % Erstattung), Hanse Merkur ZahnPrivat 100 (90 %, bestes Preis-Leistungs-Verhältnis) oder Signal Iduna Zahn Premium als günstigen Einstieg ab 14 €/Monat."}}}},
          {{"@type":"Question","name":"Wie viel kostet ein Zahnarztbesuch in {name}?","acceptedAnswer":{{"@type":"Answer","text":"Zahnarztpreise variieren je nach Praxis. Zahnersatz (Kronen, Brücken) kostet in Großstädten wie {name} oft 800–3.500 € je Zahn. Die GKV übernimmt nur ca. 35–65 % – eine Zahnzusatz deckt den Rest ab."}}}},
          {{"@type":"Question","name":"Kann ich als Wohnhafter in {name} bei Blömecke & Partner abschließen?","acceptedAnswer":{{"@type":"Answer","text":"Ja, absolut. Wir beraten bundesweit telefonisch und per Video – kostenlos und unverbindlich. Als bayerischer Versicherungsvermittler sind wir in ganz Deutschland tätig."}}}}
        ]
      }}
    ]
  }}
  </script>
  <style>
    :root{{--blue:#0057ff;--coral:#ff5c35;--coral-dark:#e04a28;--navy:#0a1628;--text:#1a2b3c;--muted:#4a5568;--border:#e2e8f0;--bg:#f7f9fc;}}
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    body{{font-family:'Inter',system-ui,sans-serif;color:var(--text);background:var(--bg);line-height:1.6;}}
    nav{{position:sticky;top:0;z-index:100;background:#fff;border-bottom:1px solid var(--border);padding:0 24px;}}
    .nav-inner{{max-width:1100px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:64px;}}
    .nav-logo{{font-weight:800;color:var(--blue);text-decoration:none;font-size:1rem;}}
    .nav-links a{{text-decoration:none;color:var(--muted);font-size:.9rem;margin-left:20px;font-weight:500;}}
    .nav-links a:hover{{color:var(--blue);}}
    .nav-cta{{background:var(--coral);color:#fff !important;padding:10px 20px;border-radius:8px;font-weight:700;font-size:.85rem;margin-left:16px;}}
    .nav-cta:hover{{background:var(--coral-dark);}}
    .hero{{background:linear-gradient(135deg,var(--navy) 0%,#0d2b6b 60%,#0057ff 100%);color:#fff;padding:64px 24px 72px;}}
    .hero-inner{{max-width:900px;margin:0 auto;}}
    .breadcrumb{{font-size:.78rem;color:rgba(255,255,255,.6);margin-bottom:18px;}}
    .breadcrumb a{{color:rgba(255,255,255,.7);text-decoration:none;}}
    .hero h1{{font-size:clamp(1.7rem,3.8vw,2.6rem);font-weight:900;line-height:1.15;margin-bottom:14px;}}
    .hero h1 em{{color:#ffcc00;font-style:normal;}}
    .hero-desc{{font-size:1rem;color:rgba(255,255,255,.85);max-width:600px;margin-bottom:28px;}}
    .hero-stats{{display:flex;gap:28px;flex-wrap:wrap;margin-bottom:32px;}}
    .hero-stat .val{{font-size:1.8rem;font-weight:900;color:#ffcc00;}}
    .hero-stat .lab{{font-size:.75rem;color:rgba(255,255,255,.7);margin-top:2px;}}
    .hero-cta{{display:inline-block;background:var(--coral);color:#fff;font-weight:800;font-size:1rem;padding:15px 32px;border-radius:12px;text-decoration:none;}}
    .hero-cta:hover{{background:var(--coral-dark);}}
    .content{{max-width:900px;margin:0 auto;padding:56px 24px;}}
    h2{{font-size:1.45rem;font-weight:800;color:var(--navy);margin:44px 0 14px;}}
    h2:first-child{{margin-top:0;}}
    p{{color:var(--muted);margin-bottom:12px;font-size:.96rem;}}
    ul.checks{{list-style:none;padding:0;margin-bottom:18px;}}
    ul.checks li{{padding:5px 0 5px 26px;position:relative;color:var(--muted);font-size:.94rem;}}
    ul.checks li::before{{content:'✓';position:absolute;left:0;color:#16a34a;font-weight:700;}}
    .compare-table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:.88rem;}}
    .compare-table th{{background:var(--navy);color:#fff;padding:12px 14px;text-align:left;font-weight:700;}}
    .compare-table th:first-child{{border-radius:8px 0 0 0;}}
    .compare-table th:last-child{{border-radius:0 8px 0 0;}}
    .compare-table td{{padding:11px 14px;border-bottom:1px solid var(--border);color:var(--muted);}}
    .compare-table tr:hover td{{background:#f0f4ff;}}
    .badge-best{{background:#fef3c7;color:#92400e;font-size:.7rem;font-weight:700;padding:2px 7px;border-radius:20px;margin-left:5px;}}
    .badge-tip{{background:#dcfce7;color:#166534;font-size:.7rem;font-weight:700;padding:2px 7px;border-radius:20px;margin-left:5px;}}
    .stars{{color:#f59e0b;}}
    .local-box{{background:#f0f4ff;border-left:4px solid var(--blue);border-radius:8px;padding:18px 20px;margin:20px 0;}}
    .local-box strong{{color:var(--navy);}}
    #kontakt{{scroll-margin-top:80px;}}
    .form-section{{background:linear-gradient(135deg,var(--navy),#0d2b6b);color:#fff;padding:56px 24px;}}
    .form-inner{{max-width:620px;margin:0 auto;}}
    .form-inner h2{{color:#fff;font-size:1.7rem;margin-bottom:8px;}}
    .form-inner .sub{{color:rgba(255,255,255,.8);margin-bottom:26px;font-size:.95rem;}}
    .form-row{{display:grid;grid-template-columns:1fr 1fr;gap:12px;}}
    .fg{{display:flex;flex-direction:column;gap:5px;}}
    .fg.full{{grid-column:1/-1;}}
    label{{font-size:.8rem;font-weight:600;color:rgba(255,255,255,.85);}}
    input,select,textarea{{padding:11px 14px;border:1.5px solid rgba(255,255,255,.2);border-radius:8px;background:rgba(255,255,255,.08);color:#fff;font-size:.93rem;font-family:inherit;}}
    input::placeholder,textarea::placeholder{{color:rgba(255,255,255,.4);}}
    input:focus,select:focus,textarea:focus{{outline:none;border-color:rgba(255,255,255,.6);}}
    select option{{color:#000;background:#fff;}}
    .btn-submit{{width:100%;padding:15px;background:var(--coral);border:none;border-radius:10px;color:#fff;font-size:1rem;font-weight:800;cursor:pointer;margin-top:6px;}}
    .btn-submit:hover{{background:var(--coral-dark);}}
    .form-note{{font-size:.73rem;color:rgba(255,255,255,.5);text-align:center;margin-top:10px;}}
    #formStatus{{margin-top:14px;padding:12px;border-radius:8px;text-align:center;font-weight:600;display:none;}}
    #formStatus.ok{{background:#dcfce7;color:#166534;display:block;}}
    #formStatus.err{{background:#fee2e2;color:#991b1b;display:block;}}
    .faq-section{{background:#fff;padding:56px 24px;}}
    .faq-inner{{max-width:760px;margin:0 auto;}}
    .faq-inner h2{{text-align:center;margin-bottom:32px;}}
    .faq-item{{border:1px solid var(--border);border-radius:10px;margin-bottom:8px;overflow:hidden;}}
    .faq-q{{padding:16px 18px;font-weight:700;cursor:pointer;display:flex;justify-content:space-between;align-items:center;font-size:.95rem;}}
    .faq-q::after{{content:'+';font-size:1.3rem;color:var(--blue);}}
    .faq-item.open .faq-q::after{{content:'−';}}
    .faq-a{{max-height:0;overflow:hidden;transition:max-height .3s ease;}}
    .faq-item.open .faq-a{{max-height:300px;}}
    .faq-a p{{padding:0 18px 16px;color:var(--muted);font-size:.91rem;margin:0;}}
    .city-links{{background:#f7f9fc;padding:40px 24px;text-align:center;}}
    .city-links h3{{font-size:1rem;font-weight:700;color:var(--navy);margin-bottom:16px;}}
    .city-links a{{display:inline-block;margin:4px 6px;padding:7px 14px;background:#fff;border:1px solid var(--border);border-radius:20px;font-size:.82rem;color:var(--blue);text-decoration:none;font-weight:500;}}
    .city-links a:hover{{background:var(--blue);color:#fff;}}
    footer{{background:var(--navy);color:rgba(255,255,255,.6);text-align:center;padding:28px 24px;font-size:.82rem;}}
    footer a{{color:rgba(255,255,255,.7);text-decoration:none;}}
    footer a:hover{{color:#fff;}}
    @media(max-width:600px){{.form-row{{grid-template-columns:1fr;}}.hero-stats{{gap:16px;}}.compare-table{{font-size:.78rem;}}.compare-table th,.compare-table td{{padding:9px 8px;}}}}
  </style>
</head>
<body>

<nav>
  <div class="nav-inner">
    <a href="/" class="nav-logo">krankenzusatz-vergleich.de</a>
    <div class="nav-links">
      <a href="/">Startseite</a>
      <a href="/zahnzusatz/">Zahnzusatz</a>
      <a href="/krankenhaus/">Krankenhaus</a>
      <a href="/blog/">Ratgeber</a>
      <a href="#kontakt" class="nav-cta">Jetzt vergleichen</a>
    </div>
  </div>
</nav>

<section class="hero">
  <div class="hero-inner">
    <p class="breadcrumb"><a href="/">Startseite</a> &rsaquo; <a href="/zahnzusatz/">Zahnzusatzversicherung</a> &rsaquo; {name}</p>
    <h1>Zahnzusatzversicherung <em>{name}</em> 2026 – kostenloser Vergleich</h1>
    <p class="hero-desc">{blurb} Vergleichen Sie DKV, Signal Iduna und Hanse Merkur – persönlich beraten, kostenlos und unverbindlich.</p>
    <div class="hero-stats">
      <div class="hero-stat"><div class="val">100 %</div><div class="lab">Max. Zahnersatz-Erstattung</div></div>
      <div class="hero-stat"><div class="val">{gkv_insured}</div><div class="lab">GKV-Versicherte in {name}</div></div>
      <div class="hero-stat"><div class="val">ab 14 €</div><div class="lab">Zahnzusatz ab/Monat</div></div>
      <div class="hero-stat"><div class="val">0 €</div><div class="lab">Beratungskosten</div></div>
    </div>
    <a href="#kontakt" class="hero-cta">Kostenlosen Vergleich für {name} anfordern &rarr;</a>
  </div>
</section>

<div class="content">

  <h2>Zahnzusatzversicherung in {name} – warum jetzt abschließen?</h2>
  <p>{local_fact}</p>
  <p>Die gesetzliche Krankenkasse übernimmt in {name} – wie bundesweit – nur die Basisversorgung beim Zahnarzt: rund 35–65 % der Regelleistung bei Zahnersatz. Hochwertige Versorgung wie Keramikkronen, Implantate oder professionelle Zahnreinigung zahlen Sie vollständig selbst.</p>

  <div class="local-box">
    <strong>Gut zu wissen für {name}:</strong> Als bundesweit tätiger Versicherungsvermittler mit Sitz in Bayern beraten wir Kunden in {name} telefonisch, per Video oder per WhatsApp – schnell, persönlich und kostenlos. Gleicher Preis wie beim Direktabschluss beim Versicherer.
  </div>

  <h2>Die 3 besten Zahnzusatzversicherungen für {name} im Vergleich</h2>
  <table class="compare-table">
    <thead>
      <tr>
        <th>Anbieter &amp; Tarif</th>
        <th>Zahnersatz</th>
        <th>Prophylaxe</th>
        <th>Preis ab</th>
        <th>Bewertung</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>DKV</strong> ZahnPremium Plus <span class="badge-best">Testsieger</span></td>
        <td>100 % ohne Limit</td>
        <td>100 % bis 150 €</td>
        <td>28 €/Mon.</td>
        <td><span class="stars">★★★★★</span> 4,9</td>
      </tr>
      <tr>
        <td><strong>Hanse Merkur</strong> ZahnPrivat 100 <span class="badge-tip">Preis-Leistung</span></td>
        <td>90 % bis 3.000 €/J.</td>
        <td>80 % bis 120 €</td>
        <td>22 €/Mon.</td>
        <td><span class="stars">★★★★★</span> 4,7</td>
      </tr>
      <tr>
        <td><strong>Signal Iduna</strong> Zahn Premium <span class="badge-tip">Günstigster</span></td>
        <td>80 % bis 2.000 €/J.</td>
        <td>80 % bis 100 €</td>
        <td>14 €/Mon.</td>
        <td><span class="stars">★★★★☆</span> 4,4</td>
      </tr>
    </tbody>
  </table>
  <p style="font-size:.78rem;color:#8898aa;">* Preisbeispiele für 30-jährige GKV-Versicherte. Individuelle Beiträge auf Anfrage. Stand Juni 2026.</p>

  <h2>Was zahlt die GKV beim Zahnarzt in {name}?</h2>
  <p>Egal ob in {name}, München oder Berlin – die GKV zahlt deutschlandweit nach denselben Regeln:</p>
  <ul class="checks">
    <li>Zahnfüllung (Amalgam/Kunststoff): ca. 80 % GKV-Anteil</li>
    <li>Zahnkrone: ca. 35–60 % GKV-Zuschuss (bei vollständigem Bonusheft)</li>
    <li>Implantat: 0 % – vollständig selbst zu tragen</li>
    <li>Professionelle Zahnreinigung: 0 % – vollständig selbst zu tragen</li>
    <li>Kieferorthopädie Erwachsene: 0 % – vollständig selbst zu tragen</li>
  </ul>
  <p>Eine Zahnzusatzversicherung schließt diese Lücken und erstattet bis zu 100 % der Behandlungskosten – je nach gewähltem Tarif.</p>

  <h2>Für wen lohnt sich die Zahnzusatz in {name}?</h2>
  <ul class="checks">
    <li>GKV-Versicherte in {name} die ihren Zahnersatz nicht selbst tragen wollen</li>
    <li>Berufstätige und Familien mit Kindern (KFO-Kosten absichern)</li>
    <li>Menschen die regelmäßige professionelle Zahnreinigung planen</li>
    <li>Alle unter 40 Jahren – jetzt abschließen = dauerhaft günstige Beiträge</li>
  </ul>

</div>

<section class="form-section" id="kontakt">
  <div class="form-inner">
    <h2>Kostenloser Zahnzusatz-Vergleich für {name}</h2>
    <p class="sub">Unser Berater meldet sich innerhalb von 24 Stunden – telefonisch oder per WhatsApp.</p>
    <form id="leadForm">
      <input type="hidden" name="source" value="Stadtseite Zahnzusatz {name}">
      <div class="form-row">
        <div class="fg">
          <label for="vorname">Vorname *</label>
          <input type="text" id="vorname" name="vorname" placeholder="Max" required>
        </div>
        <div class="fg">
          <label for="nachname">Nachname *</label>
          <input type="text" id="nachname" name="nachname" placeholder="Mustermann" required>
        </div>
        <div class="fg">
          <label for="email">E-Mail *</label>
          <input type="email" id="email" name="email" placeholder="max@beispiel.de" required>
        </div>
        <div class="fg">
          <label for="telefon">Telefon</label>
          <input type="tel" id="telefon" name="telefon" placeholder="+49 …">
        </div>
        <div class="fg">
          <label for="alter">Ihr Alter</label>
          <input type="number" id="alter" name="alter" placeholder="35" min="18" max="80">
        </div>
        <div class="fg">
          <label for="interesse">Gewünschter Tarif</label>
          <select id="interesse" name="interesse">
            <option value="">Bitte wählen</option>
            <option value="DKV ZahnPremium Plus">DKV ZahnPremium Plus (100 %)</option>
            <option value="Hanse Merkur ZahnPrivat 100">Hanse Merkur ZahnPrivat (90 %)</option>
            <option value="Signal Iduna Zahn Premium">Signal Iduna Zahn Premium (80 %)</option>
            <option value="Beratung">Ich möchte beraten werden</option>
          </select>
        </div>
        <div class="fg full">
          <label for="nachricht">Fragen oder Besonderheiten</label>
          <textarea id="nachricht" name="nachricht" placeholder="z.B. geplante Behandlungen, Vorerkrankungen, Budget …" rows="3"></textarea>
        </div>
      </div>
      <button type="submit" class="btn-submit">Kostenlosen Vergleich für {name} anfordern &rarr;</button>
      <p class="form-note">Mit der Übermittlung stimmen Sie unserer <a href="/datenschutz/" style="color:rgba(255,255,255,.5)">Datenschutzerklärung</a> zu.</p>
      <div id="formStatus"></div>
    </form>
  </div>
</section>

<section class="faq-section">
  <div class="faq-inner">
    <h2>Häufige Fragen – Zahnzusatz {name}</h2>
    <div class="faq-item">
      <div class="faq-q">Welche Zahnzusatzversicherung ist in {name} empfehlenswert?</div>
      <div class="faq-a"><p>Je nach Budget: DKV ZahnPremium Plus (100 % Erstattung, ab 28 €/Mon.), Hanse Merkur ZahnPrivat 100 (90 %, bestes Preis-Leistungs-Verhältnis, ab 22 €/Mon.) oder Signal Iduna Zahn Premium als günstiger Einstieg ab 14 €/Monat.</p></div>
    </div>
    <div class="faq-item">
      <div class="faq-q">Kann ich als Bewohner von {name} bei Blömecke & Partner abschließen?</div>
      <div class="faq-a"><p>Ja, wir beraten bundesweit – telefonisch, per Video oder per WhatsApp. Als zugelassener Versicherungsvermittler (IHK München, Nr. D-6ULZ-YVLWB-50) sind wir in ganz Deutschland tätig.</p></div>
    </div>
    <div class="faq-item">
      <div class="faq-q">Wie schnell bin ich nach Abschluss versichert?</div>
      <div class="faq-a"><p>Die Police wird in der Regel innerhalb von 3–5 Werktagen ausgestellt. Es gilt dann eine Wartezeit von 3 Monaten – außer bei Unfallbehandlungen, die sofort abgesichert sind.</p></div>
    </div>
    <div class="faq-item">
      <div class="faq-q">Was kostet die Beratung?</div>
      <div class="faq-a"><p>Die Beratung ist für Sie vollständig kostenlos. Wir erhalten eine Provision vom Versicherer nach Vertragsabschluss – wie bei jedem autorisierten Vermittler. Sie zahlen denselben Preis wie beim Direktabschluss.</p></div>
    </div>
  </div>
</section>

<section class="city-links">
  <h3>Zahnzusatzversicherung in anderen Städten</h3>
  {city_links}
</section>

<footer>
  <p>&copy; 2026 krankenzusatz-vergleich.de – Blömecke &amp; Partner · Flurweg 31 · 94447 Plattling · <a href="tel:+4999319819500">09931 – 981 9500</a></p>
  <p style="margin-top:8px;">
    <a href="/">Startseite</a> &nbsp;·&nbsp;
    <a href="/zahnzusatz/">Zahnzusatz</a> &nbsp;·&nbsp;
    <a href="/krankenhaus/">Krankenhaus</a> &nbsp;·&nbsp;
    <a href="/erstinformation/">Erstinformation</a> &nbsp;·&nbsp;
    <a href="/impressum/">Impressum</a> &nbsp;·&nbsp;
    <a href="/datenschutz/">Datenschutz</a>
  </p>
</footer>

<a href="https://wa.me/4999319819500?text=Hallo%2C%20ich%20wohne%20in%20{name_encoded}%20und%20interessiere%20mich%20f%C3%BCr%20eine%20Zahnzusatzversicherung." target="_blank" rel="noopener" style="position:fixed;bottom:28px;right:28px;z-index:200;background:#25d366;color:#fff;width:54px;height:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 16px rgba(37,211,102,.5);text-decoration:none;" aria-label="WhatsApp">
  <svg width="24" height="24" viewBox="0 0 24 24" fill="white"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
</a>

<script>
document.querySelectorAll('.faq-q').forEach(q => q.addEventListener('click', () => q.parentElement.classList.toggle('open')));
document.getElementById('leadForm').addEventListener('submit', async e => {{
  e.preventDefault();
  const btn = e.target.querySelector('.btn-submit');
  const status = document.getElementById('formStatus');
  btn.textContent = 'Wird gesendet …'; btn.disabled = true;
  try {{
    const r = await fetch('/lead.php', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(Object.fromEntries(new FormData(e.target)))}});
    if (r.ok) {{ status.className='ok'; status.textContent='Vielen Dank! Wir melden uns innerhalb von 24 Stunden.'; e.target.reset(); }}
    else throw new Error();
  }} catch {{ status.className='err'; status.textContent='Fehler beim Senden. Bitte rufen Sie uns an: 09931 – 981 9500'; }}
  btn.textContent='Kostenlosen Vergleich für {name} anfordern →'; btn.disabled=false;
}});
</script>
</body>
</html>'''

def generate_city_links(current_slug, cities):
    links = []
    for name, slug, *_ in cities:
        if slug != current_slug:
            links.append(f'<a href="/zahnzusatz-{slug}/">{name}</a>')
    return '\n  '.join(links)

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    public_dir = os.path.join(base_dir, 'public')

    sitemap_entries = []

    for name, slug, state, pop, gkv, blurb, local_fact in CITIES:
        # URL-encode city name for WhatsApp
        name_encoded = name.replace('ü','%C3%BC').replace('ö','%C3%B6').replace('ä','%C3%A4').replace(' ','%20')

        city_links = generate_city_links(slug, CITIES)

        html = HTML_TEMPLATE.format(
            name=name,
            slug=slug,
            state=state,
            pop=pop,
            gkv_insured=gkv,
            blurb=blurb,
            local_fact=local_fact,
            name_encoded=name_encoded,
            city_links=city_links,
        )

        out_dir = os.path.join(public_dir, f'zahnzusatz-{slug}')
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, 'index.html')

        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f'  ✓  /zahnzusatz-{slug}/')
        sitemap_entries.append(f'''  <url>
    <loc>https://krankenzusatz-vergleich.de/zahnzusatz-{slug}/</loc>
    <lastmod>2026-06-28</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.75</priority>
  </url>''')

    # Write sitemap snippet
    snippet_file = os.path.join(public_dir, '_city_sitemap_entries.txt')
    with open(snippet_file, 'w') as f:
        f.write('\n'.join(sitemap_entries))

    print(f'\n{len(CITIES)} Stadtseiten generiert.')
    print(f'Sitemap-Einträge: {snippet_file}')

if __name__ == '__main__':
    main()
