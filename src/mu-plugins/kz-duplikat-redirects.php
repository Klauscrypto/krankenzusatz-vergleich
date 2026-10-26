<?php
/**
 * Plugin Name: Duplikat-Weiterleitungen Blog
 * Description: 301 von geloeschten Doppel-Beitraegen (Slug -2/-3) auf den aeltesten Beitrag mit gleichem Titel.
 *
 * Der Artikel-Generator hat bis 26.10.2026 seinen Themen-Pool nach dem Durchlauf
 * wiederholt; 48 Beitraege waren Duplikate. Sie wurden geloescht, ihre Adressen
 * leiten hierher weiter, damit Google und alte Links nicht auf 404 laufen.
 * Quelle im Repo: src/mu-plugins/ (Deploy per GitHub Actions).
 */
add_action('template_redirect', function () {
    if (!is_404()) return;
    static $map = [
        '/blog/gkv-ratgeber/kuendigung-und-wechsel-so-wechseln-sie-ihre-zusatzversicherung-ohne-luecken-2/' => '/blog/gkv-ratgeber/kuendigung-und-wechsel-so-wechseln-sie-ihre-zusatzversicherung-ohne-luecken/',
        '/blog/gkv-ratgeber/kuendigung-und-wechsel-so-wechseln-sie-ihre-zusatzversicherung-ohne-luecken-3/' => '/blog/gkv-ratgeber/kuendigung-und-wechsel-so-wechseln-sie-ihre-zusatzversicherung-ohne-luecken/',
        '/blog/sehhilfen/brillenversicherung-2026-wann-lohnt-sie-sich-und-wann-nicht-2/' => '/blog/sehhilfen/brillenversicherung-2026-wann-lohnt-sie-sich-und-wann-nicht/',
        '/blog/sehhilfen/brillenversicherung-2026-wann-lohnt-sie-sich-und-wann-nicht-3/' => '/blog/sehhilfen/brillenversicherung-2026-wann-lohnt-sie-sich-und-wann-nicht/',
        '/blog/krankenhaus/wahlleistungen-im-krankenhaus-kosten-nutzen-und-die-besten-tarife-2026-2/' => '/blog/krankenhaus/wahlleistungen-im-krankenhaus-kosten-nutzen-und-die-besten-tarife-2026/',
        '/blog/krankenhaus/wahlleistungen-im-krankenhaus-kosten-nutzen-und-die-besten-tarife-2026-3/' => '/blog/krankenhaus/wahlleistungen-im-krankenhaus-kosten-nutzen-und-die-besten-tarife-2026/',
        '/blog/zahnzusatz/inlays-veneers-keramikzaehne-was-zahlt-welche-zusatzversicherung-2/' => '/blog/zahnzusatz/inlays-veneers-keramikzaehne-was-zahlt-welche-zusatzversicherung/',
        '/blog/zahnzusatz/inlays-veneers-keramikzaehne-was-zahlt-welche-zusatzversicherung-3/' => '/blog/zahnzusatz/inlays-veneers-keramikzaehne-was-zahlt-welche-zusatzversicherung/',
        '/blog/zahnzusatz/zahnzusatzversicherung-fuer-kinder-was-eltern-wirklich-wissen-muessen-2/' => '/blog/zahnzusatz/zahnzusatzversicherung-fuer-kinder-was-eltern-wirklich-wissen-muessen/',
        '/blog/zahnzusatz/zahnzusatzversicherung-fuer-kinder-was-eltern-wirklich-wissen-muessen-3/' => '/blog/zahnzusatz/zahnzusatzversicherung-fuer-kinder-was-eltern-wirklich-wissen-muessen/',
        '/blog/zahnzusatz/gkv-festzuschuesse-erklaert-wie-sie-mit-einer-zusatzversicherung-klug-kombiniere-2/' => '/blog/zahnzusatz/gkv-festzuschuesse-erklaert-wie-sie-mit-einer-zusatzversicherung-klug-kombiniere/',
        '/blog/zahnzusatz/gkv-festzuschuesse-erklaert-wie-sie-mit-einer-zusatzversicherung-klug-kombiniere-3/' => '/blog/zahnzusatz/gkv-festzuschuesse-erklaert-wie-sie-mit-einer-zusatzversicherung-klug-kombiniere/',
        '/blog/zahnzusatz/zahnzusatzversicherung-ohne-wartezeit-die-besten-tarife-2026-im-vergleich-2/' => '/blog/zahnzusatz/zahnzusatzversicherung-ohne-wartezeit-die-besten-tarife-2026-im-vergleich/',
        '/blog/zahnzusatz/zahnzusatzversicherung-ohne-wartezeit-die-besten-tarife-2026-im-vergleich-3/' => '/blog/zahnzusatz/zahnzusatzversicherung-ohne-wartezeit-die-besten-tarife-2026-im-vergleich/',
        '/blog/zahnzusatz/dkv-signal-iduna-oder-hanse-merkur-welche-zahnzusatz-passt-zu-mir-2/' => '/blog/zahnzusatz/dkv-signal-iduna-oder-hanse-merkur-welche-zahnzusatz-passt-zu-mir/',
        '/blog/zahnzusatz/dkv-signal-iduna-oder-hanse-merkur-welche-zahnzusatz-passt-zu-mir-3/' => '/blog/zahnzusatz/dkv-signal-iduna-oder-hanse-merkur-welche-zahnzusatz-passt-zu-mir/',
        '/blog/zahnzusatz/bonusheft-richtig-fuehren-so-steigern-sie-ihren-gkv-zuschuss-auf-bis-zu-65-2/' => '/blog/zahnzusatz/bonusheft-richtig-fuehren-so-steigern-sie-ihren-gkv-zuschuss-auf-bis-zu-65/',
        '/blog/zahnzusatz/bonusheft-richtig-fuehren-so-steigern-sie-ihren-gkv-zuschuss-auf-bis-zu-65-3/' => '/blog/zahnzusatz/bonusheft-richtig-fuehren-so-steigern-sie-ihren-gkv-zuschuss-auf-bis-zu-65/',
        '/blog/gkv-ratgeber/bonus-programme-der-krankenkassen-wirklicher-mehrwert-oder-marketing-gag-2/' => '/blog/gkv-ratgeber/bonus-programme-der-krankenkassen-wirklicher-mehrwert-oder-marketing-gag/',
        '/blog/gkv-ratgeber/bonus-programme-der-krankenkassen-wirklicher-mehrwert-oder-marketing-gag-3/' => '/blog/gkv-ratgeber/bonus-programme-der-krankenkassen-wirklicher-mehrwert-oder-marketing-gag/',
        '/blog/zahnzusatz/zahnzusatzversicherung-trotz-vorerkrankung-so-finden-sie-den-richtigen-tarif-2/' => '/blog/zahnzusatz/zahnzusatzversicherung-trotz-vorerkrankung-so-finden-sie-den-richtigen-tarif/',
        '/blog/zahnzusatz/zahnzusatzversicherung-trotz-vorerkrankung-so-finden-sie-den-richtigen-tarif-3/' => '/blog/zahnzusatz/zahnzusatzversicherung-trotz-vorerkrankung-so-finden-sie-den-richtigen-tarif/',
        '/blog/krankenhaus/einbettzimmer-im-krankenhaus-fuer-wen-lohnt-sich-die-zusatzversicherung-2/' => '/blog/krankenhaus/einbettzimmer-im-krankenhaus-fuer-wen-lohnt-sich-die-zusatzversicherung/',
        '/blog/krankenhaus/einbettzimmer-im-krankenhaus-fuer-wen-lohnt-sich-die-zusatzversicherung-3/' => '/blog/krankenhaus/einbettzimmer-im-krankenhaus-fuer-wen-lohnt-sich-die-zusatzversicherung/',
        '/blog/gkv-ratgeber/zusatzversicherung-kombinieren-so-maximieren-sie-schutz-bei-minimalem-beitrag-2/' => '/blog/gkv-ratgeber/zusatzversicherung-kombinieren-so-maximieren-sie-schutz-bei-minimalem-beitrag/',
        '/blog/gkv-ratgeber/zusatzversicherung-kombinieren-so-maximieren-sie-schutz-bei-minimalem-beitrag-3/' => '/blog/gkv-ratgeber/zusatzversicherung-kombinieren-so-maximieren-sie-schutz-bei-minimalem-beitrag/',
        '/blog/krankenhaus/krankenhaus-tagegeld-wieviel-brauche-ich-wirklich-und-wann-zahlt-es-sich-aus-2/' => '/blog/krankenhaus/krankenhaus-tagegeld-wieviel-brauche-ich-wirklich-und-wann-zahlt-es-sich-aus/',
        '/blog/krankenhaus/krankenhaus-tagegeld-wieviel-brauche-ich-wirklich-und-wann-zahlt-es-sich-aus-3/' => '/blog/krankenhaus/krankenhaus-tagegeld-wieviel-brauche-ich-wirklich-und-wann-zahlt-es-sich-aus/',
        '/blog/gkv-ratgeber/zusatzversicherung-im-alter-wann-ist-es-noch-sinnvoll-abzuschliessen-2/' => '/blog/gkv-ratgeber/zusatzversicherung-im-alter-wann-ist-es-noch-sinnvoll-abzuschliessen/',
        '/blog/krankenhaus/chefarztbehandlung-im-krankenhaus-wie-funktioniert-die-zusatzversicherung-wirkli-2/' => '/blog/krankenhaus/chefarztbehandlung-im-krankenhaus-wie-funktioniert-die-zusatzversicherung-wirkli/',
        '/blog/heilpraktiker/naturheilkunde-richtig-absichern-die-besten-heilpraktiker-tarife-im-ueberblick-2/' => '/blog/heilpraktiker/naturheilkunde-richtig-absichern-die-besten-heilpraktiker-tarife-im-ueberblick/',
        '/blog/zahnzusatz/zahnersatz-2026-was-zahlt-die-gkv-und-was-bleibt-an-ihnen-haengen-2/' => '/blog/zahnzusatz/zahnersatz-2026-was-zahlt-die-gkv-und-was-bleibt-an-ihnen-haengen/',
        '/blog/heilpraktiker/heilpraktiker-zusatzversicherung-2026-akupunktur-osteopathie-und-mehr-2/' => '/blog/heilpraktiker/heilpraktiker-zusatzversicherung-2026-akupunktur-osteopathie-und-mehr/',
        '/blog/krankenhaus/freie-krankenhauswahl-warum-spezialisten-oft-nur-ueber-privatpatienten-erreichba-2/' => '/blog/krankenhaus/freie-krankenhauswahl-warum-spezialisten-oft-nur-ueber-privatpatienten-erreichba/',
        '/blog/gkv-ratgeber/versicherungsantrag-ausfuellen-gesundheitsfragen-richtig-beantworten-2/' => '/blog/gkv-ratgeber/versicherungsantrag-ausfuellen-gesundheitsfragen-richtig-beantworten/',
        '/blog/zahnzusatz/professionelle-zahnreinigung-warum-die-gkv-kaum-zahlt-und-zusatztarife-helfen-2/' => '/blog/zahnzusatz/professionelle-zahnreinigung-warum-die-gkv-kaum-zahlt-und-zusatztarife-helfen/',
        '/blog/gkv-ratgeber/gkv-leistungen-2026-was-hat-sich-veraendert-und-wo-sind-die-groessten-luecken-2/' => '/blog/gkv-ratgeber/gkv-leistungen-2026-was-hat-sich-veraendert-und-wo-sind-die-groessten-luecken/',
        '/blog/gkv-ratgeber/krankenkasse-wechseln-2026-wann-es-sich-lohnt-und-worauf-sie-achten-muessen-2/' => '/blog/gkv-ratgeber/krankenkasse-wechseln-2026-wann-es-sich-lohnt-und-worauf-sie-achten-muessen/',
        '/blog/zahnzusatz/kieferorthopaedie-fuer-erwachsene-welche-tarife-uebernehmen-die-kosten-2/' => '/blog/zahnzusatz/kieferorthopaedie-fuer-erwachsene-welche-tarife-uebernehmen-die-kosten/',
        '/blog/krankenhaus/privatpatient-als-gkv-versicherter-so-geht-es-mit-der-richtigen-zusatzpolice-2/' => '/blog/krankenhaus/privatpatient-als-gkv-versicherter-so-geht-es-mit-der-richtigen-zusatzpolice/',
        '/blog/heilpraktiker/osteopathie-kosten-was-die-gkv-zahlt-und-warum-eine-zusatzversicherung-sinnvoll-2/' => '/blog/heilpraktiker/osteopathie-kosten-was-die-gkv-zahlt-und-warum-eine-zusatzversicherung-sinnvoll/',
        '/blog/gkv-ratgeber/gkv-zusatzleistungen-was-ihre-krankenkasse-extra-bietet-und-was-nicht-2/' => '/blog/gkv-ratgeber/gkv-zusatzleistungen-was-ihre-krankenkasse-extra-bietet-und-was-nicht/',
        '/blog/zahnzusatz/implantat-oder-bruecke-was-leistet-die-zahnzusatzversicherung-wirklich-2/' => '/blog/zahnzusatz/implantat-oder-bruecke-was-leistet-die-zahnzusatzversicherung-wirklich/',
        '/blog/zahnzusatz/zahnzusatz-ab-wann-sinnvoll-das-richtige-einstiegsalter-fuer-maximale-ersparnis-2/' => '/blog/zahnzusatz/zahnzusatz-ab-wann-sinnvoll-das-richtige-einstiegsalter-fuer-maximale-ersparnis/',
        '/blog/krankenhaus/krankenhauszusatz-fuer-selbststaendige-warum-schnelle-genesung-entscheidend-ist-2/' => '/blog/krankenhaus/krankenhauszusatz-fuer-selbststaendige-warum-schnelle-genesung-entscheidend-ist/',
        '/blog/vorsorge/vorsorgeuntersuchungen-was-die-gkv-zahlt-und-wo-zusatztarife-sinnvoll-sind-2/' => '/blog/vorsorge/vorsorgeuntersuchungen-was-die-gkv-zahlt-und-wo-zusatztarife-sinnvoll-sind/',
        '/blog/gkv-ratgeber/eigenanteil-bei-medikamenten-tipps-um-die-zuzahlung-zu-senken-2/' => '/blog/gkv-ratgeber/eigenanteil-bei-medikamenten-tipps-um-die-zuzahlung-zu-senken/',
        '/blog/krankenhaus/rooming-in-warum-eltern-eine-krankenhauszusatz-fuer-ihre-kinder-brauchen-2/' => '/blog/krankenhaus/rooming-in-warum-eltern-eine-krankenhauszusatz-fuer-ihre-kinder-brauchen/',
    ];
    $pfad = strtok($_SERVER['REQUEST_URI'] ?? '', '?');
    if ($pfad !== '' && substr($pfad, -1) !== '/') $pfad .= '/';
    if (isset($map[$pfad])) {
        wp_redirect(home_url(substr($map[$pfad], strlen('/blog'))), 301);
        exit;
    }
}, 1);
