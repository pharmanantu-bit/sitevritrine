#!/usr/bin/env python3
"""Générateur du site vitrine : Pharmacie de Nanterre Université.

Usage :  python3 build.py        -> produit le dossier dist/ (à mettre en ligne)
         python3 -m http.server -d dist 8000   -> aperçu sur http://localhost:8000

Pour modifier le site : changer les textes ici, les animations dans data/animations.json,
les dimanches de garde dans data/gardes.json, les photos dans assets/photos/.
"""
import datetime
import html
import json
import os
import pathlib
import re
import shutil
import zoneinfo

ROOT = pathlib.Path(__file__).parent
DIST = ROOT / "dist"

# ------------------------------------------------------------------ À ADAPTER
DOMAIN = "https://www.VOTRE-DOMAINE.fr"      # remplacer par l'adresse réelle du site, puis relancer build.py
# ---------------------------------------------------------------------------
# Réglages utilisés par la mise en ligne automatique (GitHub Pages) : inutile d'y toucher.
DOMAIN = os.environ.get("SITE_DOMAIN", DOMAIN).rstrip("/")
BASE = os.environ.get("SITE_BASE", "").rstrip("/")     # ex. "/sitevritrine" si le site n'est pas à la racine
NOINDEX = os.environ.get("SITE_NOINDEX") == "1"        # site d'aperçu : non référencé par les moteurs
# ---------------------------------------------------------------------------

TODAY = datetime.date.today()
TZ = zoneinfo.ZoneInfo("Europe/Paris")

S = dict(
    name="Pharmacie de Nanterre Université",
    tel="01 47 21 22 28",
    tel_e164="+33147212228",
    email="pharmacie.nanterre.u@gmail.com",
    street="390 boulevard des Provinces Françaises",
    zip="92000",
    city="Nanterre",
    lat=48.9009527,
    lng=2.2168887,
    maps="https://maps.app.goo.gl/rdrzxkHG7Mh9rery9",
    shop="https://pharmacie-nanterre-universite.apothical.fr",
    rating="4,6",
    reviews="470",
)
SOCIALS = [
    ("Instagram", "https://www.instagram.com/pharmacie_nanterre_universite/"),
    ("Facebook", "https://www.facebook.com/PHARMANANTUNIVERSITE/"),
    ("YouTube", "https://www.youtube.com/@PharmacieNanterreUniversit%C3%A9"),
    ("TikTok", "https://www.tiktok.com/@pharmacie_nanterre_u"),
    ("LinkedIn", "https://www.linkedin.com/company/26680027/"),
]
OWNERS = [
    ("david-illouz", "David Illouz"),
    ("jonathan-illouz", "Jonathan Illouz"),
]

DAYS = [("Lundi", "Monday"), ("Mardi", "Tuesday"), ("Mercredi", "Wednesday"), ("Jeudi", "Thursday"),
        ("Vendredi", "Friday"), ("Samedi", "Saturday"), ("Dimanche", "Sunday")]
HOURS = {d: ("08:00", "20:00") for d in ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]}
HOURS["Samedi"] = ("08:30", "20:00")
DELIV = {d: ("09:00", "19:00") for d in ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]}
GARDE_HOURS = ("09:00", "20:00")   # horaires affichés sur Google pour les dimanches de garde

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]

TODOS = []


# ------------------------------------------------------------------ outils
def esc(s):
    return html.escape(str(s), quote=True)


def todo(label):
    if label not in TODOS:
        TODOS.append(label)
    return f'<mark class="todo">[{esc(label)}]</mark>'


def hm(t):
    h, m = t.split(":")
    return f"{int(h)}h" + ("" if m == "00" else m)


def span(o, c):
    return f"{hm(o)} - {hm(c)}"


def fdate(d):
    jour = "1er" if d.day == 1 else str(d.day)
    return f"{JOURS[d.weekday()].capitalize()} {jour} {MOIS[d.month - 1]} {d.year}"


def path(slug):
    return "/" if slug == "" else f"/{slug}/"


def url(slug):
    return DOMAIN + path(slug)


def shop(p=""):
    return S["shop"] + p


def directions():
    q = f"{S['street']} {S['zip']} {S['city']}".replace(" ", "+")
    return f"https://www.google.com/maps/dir/?api=1&destination={q}"


def photo_file(key):
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = ROOT / "assets" / "photos" / f"{key}.{ext}"
        if p.exists():
            return p
    return None


def photo(key, alt, label):
    p = photo_file(key)
    if p:
        from PIL import Image
        w, h = Image.open(p).size
        return (f'<img src="/assets/photos/{p.name}" alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy">')
    t = f"photo : {label}"
    if t not in TODOS:
        TODOS.append(t)
    return f'<figure class="ph" role="img" aria-label="{esc(alt)}"><span>Photo à ajouter : {esc(label)}</span></figure>'


def btn(href, label, kind="solid", extra=""):
    return f'<a class="btn btn--{kind}" href="{esc(href)}"{extra}>{label}</a>'


def hours_table(caption, data, closed):
    rows = ""
    for fr, _ in DAYS:
        val = span(*data[fr]) if fr in data else closed
        rows += f'<tr><th scope="row">{fr}</th><td>{val}</td></tr>'
    return f'<table class="hours"><caption>{esc(caption)}</caption><tbody>{rows}</tbody></table>'


def load_json(name):
    p = ROOT / "data" / name
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def gardes():
    out = []
    for g in load_json("gardes.json"):
        d = datetime.date.fromisoformat(g["date"])
        if d >= TODAY:
            out.append((d, g.get("open", GARDE_HOURS[0]), g.get("close", GARDE_HOURS[1])))
    return sorted(out)[:10]


def animations():
    up, past = [], []
    for a in load_json("animations.json"):
        a = dict(a)
        a["d"] = datetime.date.fromisoformat(a["date"])
        (up if a["d"] >= TODAY else past).append(a)
    up.sort(key=lambda a: (a["d"], a.get("start", "")))
    past.sort(key=lambda a: a["d"], reverse=True)
    return up[:8], past[:8]


def when(a):
    s = fdate(a["d"])
    if a.get("start"):
        s += f", {span(a['start'], a['end'])}" if a.get("end") else f", {hm(a['start'])}"
    return s


def anim_html(a):
    extra = ""
    if a.get("partenaire"):
        extra += f"<p><strong>Partenaire :</strong> {esc(a['partenaire'])}</p>"
    if a.get("inscription"):
        extra += f"<p><strong>Inscription :</strong> {esc(a['inscription'])}</p>"
    return (f'<article class="anim"><p class="when">{esc(when(a))}</p><h3>{esc(a["titre"])}</h3>'
            f'<p>{esc(a.get("description", ""))}</p>{extra}</article>')


# ------------------------------------------------------------------ données structurées
SERVICES_LD = [
    ("Conseil pharmaceutique", "Conseil de l'équipe officinale, préparation des ordonnances, envoi d'ordonnance en ligne."),
    ("Conseil dermatologique et diagnostic de peau", "Diagnostic de peau personnalisé et conseil sur les soins dermo-cosmétiques."),
    ("Parapharmacie et dermo-cosmétique", "Soins visage et corps, compléments alimentaires, solaire, bébé, hygiène."),
    ("Phytothérapie et aromathérapie", "Plantes, huiles essentielles, gemmothérapie, herboristerie, apithérapie."),
    ("Orthopédie et contention", "Orthèses, contention, chaussures médicales, semelles, bilan podologique."),
    ("Location et vente de matériel médical", "Maintien à domicile, tire-lait, déambulateur, fauteuil roulant, lit médicalisé."),
    ("Dépistage TROD", "Test rapide d'orientation diagnostique de l'angine."),
    ("Vaccination en pharmacie", "Vaccination sur rendez-vous."),
    ("Accompagnement à l'arrêt du tabac", "Conseil et accompagnement par l'équipe."),
    ("Réservation de produits par serveur vocal", "Réservation par téléphone de tous les produits, à retirer à la pharmacie."),
    ("Livraison de produits de parapharmacie", "Livraison via Uber Eats dans les Hauts-de-Seine (92), du lundi au samedi de 9h à 19h."),
    ("Animations, mini-soins et ateliers prévention", "Une animation par semaine."),
]


def pharmacy_node():
    people = []
    for key, name in OWNERS:
        p = {"@type": "Person", "@id": f"{DOMAIN}/equipe/#{key}", "name": name,
             "jobTitle": "Pharmacien titulaire", "worksFor": {"@id": f"{DOMAIN}/#pharmacie"}}
        f = photo_file(key)
        if f:
            p["image"] = f"{DOMAIN}/assets/photos/{f.name}"
        people.append(p)
    special = []
    for d, o, c in gardes():
        special.append({"@type": "OpeningHoursSpecification", "opens": o, "closes": c,
                        "validFrom": d.isoformat(), "validThrough": d.isoformat()})
    node = {
        "@type": "Pharmacy",
        "@id": f"{DOMAIN}/#pharmacie",
        "name": S["name"],
        "alternateName": ["Pharmacie Nanterre Université", "Pharmacie Nanterre Universite"],
        "description": ("Pharmacie d'officine à Nanterre, dans le quartier de l'université Paris Nanterre : conseil, "
                        "dermo-cosmétique, orthopédie, dépistage, réservation par téléphone et livraison de "
                        "parapharmacie dans les Hauts-de-Seine."),
        "url": DOMAIN + "/",
        "logo": f"{DOMAIN}/assets/logo-pharmacie.jpg",
        "image": [f"{DOMAIN}/assets/logo-pharmacie.jpg"],
        "telephone": S["tel_e164"],
        "email": S["email"],
        "address": {"@type": "PostalAddress", "streetAddress": S["street"], "postalCode": S["zip"],
                    "addressLocality": S["city"], "addressRegion": "Île-de-France", "addressCountry": "FR"},
        "geo": {"@type": "GeoCoordinates", "latitude": S["lat"], "longitude": S["lng"]},
        "hasMap": S["maps"],
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification",
             "dayOfWeek": [en for fr, en in DAYS[:5]], "opens": "08:00", "closes": "20:00"},
            {"@type": "OpeningHoursSpecification", "dayOfWeek": "Saturday", "opens": "08:30", "closes": "20:00"},
        ],
        "areaServed": {"@type": "AdministrativeArea", "name": "Hauts-de-Seine"},
        "sameAs": [S["maps"]] + [u for _, u in SOCIALS],
        "amenityFeature": [{"@type": "LocationFeatureSpecification", "name": "Accès fauteuil roulant", "value": True}],
        "contactPoint": [{"@type": "ContactPoint", "telephone": S["tel_e164"], "contactType": "customer service",
                          "areaServed": "FR", "availableLanguage": "fr"}],
        "hasOfferCatalog": {
            "@type": "OfferCatalog", "name": "Services de la pharmacie",
            "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": n, "description": d}}
                                for n, d in SERVICES_LD]},
        "employee": [{"@id": p["@id"]} for p in people],
    }
    if special:
        node["specialOpeningHoursSpecification"] = special
    return node, people


def delivery_node():
    return {
        "@type": "Service", "@id": f"{DOMAIN}/#livraison",
        "name": "Livraison de produits de parapharmacie (Uber Eats)",
        "serviceType": "Livraison à domicile",
        "description": "Livraison de produits de parapharmacie. Les médicaments ne sont pas concernés.",
        "provider": {"@id": f"{DOMAIN}/#pharmacie"},
        "areaServed": {"@type": "AdministrativeArea", "name": "Hauts-de-Seine"},
        "hoursAvailable": {"@type": "OpeningHoursSpecification",
                           "dayOfWeek": [en for fr, en in DAYS[:6]], "opens": "09:00", "closes": "19:00"},
    }


def event_nodes():
    up, _ = animations()
    out = []
    for a in up:
        st = datetime.datetime.combine(a["d"], datetime.time.fromisoformat(a.get("start", "10:00")), tzinfo=TZ)
        ev = {"@type": "Event", "name": a["titre"], "description": a.get("description", ""),
              "startDate": st.isoformat(), "eventStatus": "https://schema.org/EventScheduled",
              "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
              "isAccessibleForFree": True,
              "location": {"@type": "Place", "name": S["name"],
                           "address": {"@type": "PostalAddress", "streetAddress": S["street"],
                                       "postalCode": S["zip"], "addressLocality": S["city"], "addressCountry": "FR"}},
              "organizer": {"@id": f"{DOMAIN}/#pharmacie"}}
        if a.get("end"):
            ev["endDate"] = datetime.datetime.combine(a["d"], datetime.time.fromisoformat(a["end"]), tzinfo=TZ).isoformat()
        out.append(ev)
    return out


# ------------------------------------------------------------------ gabarit
NAV = [("services", "Services"), ("equipe", "Équipe"), ("animations", "Animations"),
       ("horaires-garde-livraison", "Horaires et garde"), ("faq", "FAQ"), ("contact", "Contact")]
PAGES = []   # (slug, titre court, priorité)


def jsonld(graph):
    return ('<script type="application/ld+json">'
            + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
            + "</script>")


def pagehead(h1, lede, crumb):
    return (f'<section class="pagehead"><div class="wrap"><p class="crumbs"><a href="/">Accueil</a> / {esc(crumb)}</p>'
            f'<h1>{h1}</h1><p class="lede">{lede}</p></div><div class="stripes" aria-hidden="true"></div></section>')


def map_block():
    src = f"https://www.google.com/maps?q={S['lat']},{S['lng']}&hl=fr&z=17&output=embed"
    return (f'<div class="map" data-map="{esc(src)}"><p>La carte est fournie par Google Maps. L\'afficher envoie '
            f'des données à Google.</p><button type="button" class="btn btn--line">Afficher la carte</button>'
            f'<p><a href="{esc(S["maps"])}">Ouvrir dans Google Maps</a> ou '
            f'<a href="{esc(directions())}">calculer l\'itinéraire</a></p></div>')


def footer():
    links = "".join(f'<li><a href="{path(s)}">{t}</a></li>' for s, t in NAV)
    links += '<li><a href="/dermo-cosmetique-nanterre/">Dermo-cosmétique</a></li>'
    links += '<li><a href="/orthopedie-materiel-medical-nanterre/">Orthopédie et matériel médical</a></li>'
    links += '<li><a href="/depistage-vaccination-nanterre/">Dépistage et vaccination</a></li>'
    soc = "".join(f'<li><a href="{esc(u)}" rel="noopener">{n}</a></li>' for n, u in SOCIALS)
    h = ('<p>Lundi au vendredi : 8h - 20h<br>Samedi : 8h30 - 20h<br>Dimanche : pharmacie de garde uniquement</p>'
         '<p>Livraison de parapharmacie : lundi au samedi, 9h - 19h</p>')
    return f'''<footer class="foot"><div class="wrap"><div class="foot__grid">
<div><h2>{esc(S["name"])}</h2>
<p>{esc(S["street"])}<br>{S["zip"]} {S["city"]}</p>
<p><a href="tel:{S["tel_e164"]}">{S["tel"]}</a><br><a href="mailto:{S["email"]}">{S["email"]}</a></p>
<p>Note Google : {S["rating"]}/5 sur {S["reviews"]} avis</p></div>
<div><h2>Horaires</h2>{h}</div>
<div><h2>Le site</h2><ul>{links}</ul></div>
<div><h2>Nous suivre</h2><ul>{soc}</ul>
<h2 style="margin-top:1.25rem">Commander en ligne</h2><ul>
<li><a href="{shop("/ordonnance")}" rel="noopener">Envoyer mon ordonnance</a></li>
<li><a href="{shop()}" rel="noopener">Boutique en ligne</a></li></ul></div>
</div><p class="legal"><a href="/mentions-legales/">Mentions légales et confidentialité</a>.
Les informations de ce site ne remplacent pas l'avis d'un médecin ou d'un pharmacien. En cas d'urgence, appelez le 15.</p></div></footer>'''


def render(slug, title, desc, body, extra_graph=None, crumb=None, home=False):
    canon = url(slug)
    nav = "".join(f'<a href="{path(s)}"' + (' aria-current="page"' if s == slug else "") + f'>{t}</a>' for s, t in NAV)
    node, people = pharmacy_node()
    graph = [node, delivery_node()] + (people if slug == "equipe" else [])
    graph.append({"@type": "WebSite", "@id": f"{DOMAIN}/#website", "url": DOMAIN + "/", "name": S["name"],
                  "inLanguage": "fr-FR", "publisher": {"@id": f"{DOMAIN}/#pharmacie"}})
    graph.append({"@type": "WebPage", "@id": canon + "#page", "url": canon, "name": title, "description": desc,
                  "inLanguage": "fr-FR", "isPartOf": {"@id": f"{DOMAIN}/#website"},
                  "about": {"@id": f"{DOMAIN}/#pharmacie"}})
    if not home and crumb:
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Accueil", "item": DOMAIN + "/"},
            {"@type": "ListItem", "position": 2, "name": crumb, "item": canon}]})
    graph += extra_graph or []
    og = f"{DOMAIN}/assets/logo-pharmacie.jpg"
    page = f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<meta name="theme-color" content="#ccfd04">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="{esc(S["name"])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/style.css">
{jsonld(graph)}
</head>
<body>
<a class="skip" href="#main">Aller au contenu</a>
<header class="top"><div class="wrap top__in">
<a class="brand" href="/"><img src="/assets/favicon-512.png" width="44" height="44" alt="Logo de la Pharmacie de Nanterre Université"><span>Pharmacie de<br>Nanterre Université</span></a>
<nav aria-label="Navigation principale">{nav}</nav></div></header>
<main id="main">
{body}
</main>
{footer()}
<nav class="dock" aria-label="Actions rapides"><a href="tel:{S["tel_e164"]}">Appeler</a><a href="{esc(directions())}">Itinéraire</a><a href="{shop("/ordonnance")}">Ordonnance</a></nav>
<script src="/assets/site.js" defer></script>
</body>
</html>
'''
    out = DIST / ("index.html" if slug == "" else f"{slug}/index.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rebase(page), encoding="utf-8")
    PAGES.append((slug, title, "1.0" if slug == "" else "0.8"))


# ------------------------------------------------------------------ FAQ (HTML + texte pour JSON-LD)
def faq_items():
    g = gardes()
    return [
        ("Quels sont les horaires de la pharmacie ?",
         "La pharmacie est ouverte du lundi au vendredi de 8h à 20h et le samedi de 8h30 à 20h. Elle est fermée le dimanche, sauf les dimanches de garde.",
         "La pharmacie est ouverte du lundi au vendredi de 8h à 20h et le samedi de 8h30 à 20h. Elle est fermée le dimanche, sauf les dimanches de garde."),
        ("La pharmacie est-elle ouverte le dimanche ?",
         f'Uniquement les dimanches où elle est de garde, en général de {span(*GARDE_HOURS)}. Les dates sont sur la page <a href="/horaires-garde-livraison/">Horaires, garde et livraison</a>.',
         f"Uniquement les dimanches où elle est de garde, en général de {span(*GARDE_HOURS)}."),
        ("Comment connaître la pharmacie de garde à Nanterre ?",
         f'Consultez le calendrier de nos dimanches de garde sur le site ou la <a href="{shop("/pharmacies-de-garde")}" rel="noopener">page des pharmacies de garde</a>. Le site monpharmacien-idf.fr donne aussi les pharmacies de garde en Île-de-France.',
         "Consultez le calendrier de nos dimanches de garde sur le site ou le site monpharmacien-idf.fr, qui donne les pharmacies de garde en Île-de-France."),
        ("Livrez-vous à domicile ?",
         "Oui, les produits de parapharmacie sont livrés via Uber Eats dans les Hauts-de-Seine (92), du lundi au samedi de 9h à 19h. Les médicaments ne sont pas livrés par ce service.",
         "Oui, les produits de parapharmacie sont livrés via Uber Eats dans les Hauts-de-Seine (92), du lundi au samedi de 9h à 19h. Les médicaments ne sont pas livrés par ce service."),
        ("Puis-je réserver mes produits par téléphone ?",
         f'Oui. Notre serveur vocal ({todo("numéro du serveur vocal")}) permet de réserver tous les produits : médicaments, parapharmacie et matériel médical. Vous les retirez ensuite à la pharmacie. Pour un médicament sur ordonnance, présentez l\'ordonnance au retrait.',
         "Oui. Notre serveur vocal permet de réserver tous les produits : médicaments, parapharmacie et matériel médical. Vous les retirez ensuite à la pharmacie. Pour un médicament sur ordonnance, présentez l'ordonnance au retrait."),
        ("Comment envoyer mon ordonnance à la pharmacie ?",
         f'Photographiez votre ordonnance et envoyez-la depuis <a href="{shop("/ordonnance")}" rel="noopener">notre site de commande</a>. Nous la préparons et vous la retirez au comptoir prioritaire, sans file d\'attente.',
         "Photographiez votre ordonnance et envoyez-la depuis notre site de commande. Nous la préparons et vous la retirez au comptoir prioritaire, sans file d'attente."),
        ("Faites-vous le test de l'angine (TROD) ?",
         f'Oui, le dépistage de l\'angine par test rapide (TROD) est proposé à la pharmacie. Voir la page <a href="/depistage-vaccination-nanterre/">Dépistage et vaccination</a>.',
         "Oui, le dépistage de l'angine par test rapide (TROD) est proposé à la pharmacie."),
        ("Peut-on se faire vacciner à la pharmacie ?",
         f'Oui, sur rendez-vous. Vous pouvez prendre rendez-vous depuis <a href="{shop("/rendez-vous")}" rel="noopener">notre page de rendez-vous</a> ou par téléphone au <a href="tel:{S["tel_e164"]}">{S["tel"]}</a>.',
         f"Oui, sur rendez-vous, depuis notre page de rendez-vous ou par téléphone au {S['tel']}."),
        ("Proposez-vous de l'orthopédie, de la contention et de la location de matériel médical ?",
         'Oui : orthèses, contention, chaussures médicales et semelles, matériel de maintien à domicile et location de matériel (tire-lait, déambulateur, fauteuil roulant, lit médicalisé). Détails sur la page <a href="/orthopedie-materiel-medical-nanterre/">Orthopédie et matériel médical</a>.',
         "Oui : orthèses, contention, chaussures médicales et semelles, matériel de maintien à domicile et location de matériel (tire-lait, déambulateur, fauteuil roulant, lit médicalisé)."),
        ("Faites-vous un diagnostic de peau ?",
         'Oui, un diagnostic de peau personnalisé est proposé à la pharmacie, avec des conseils sur les soins des marques Avène, La Roche-Posay, SVR et Uriage. Voir <a href="/dermo-cosmetique-nanterre/">Dermo-cosmétique</a>.',
         "Oui, un diagnostic de peau personnalisé est proposé à la pharmacie, avec des conseils sur les soins des marques Avène, La Roche-Posay, SVR et Uriage."),
        ("Organisez-vous des animations ou des ateliers ?",
         'Oui, une animation chaque semaine : rencontres avec des laboratoires partenaires, mini-soins par l\'équipe et ateliers prévention. Le programme est sur la page <a href="/animations/">Animations</a>.',
         "Oui, une animation chaque semaine : rencontres avec des laboratoires partenaires, mini-soins par l'équipe et ateliers prévention."),
        ("La pharmacie est-elle accessible aux personnes en fauteuil roulant ?",
         "Oui, la pharmacie est accessible aux personnes en fauteuil roulant et en situation de handicap.",
         "Oui, la pharmacie est accessible aux personnes en fauteuil roulant et en situation de handicap."),
        ("Où se trouve la pharmacie ?",
         f"{S['street']}, {S['zip']} {S['city']}, dans le quartier de l'université Paris Nanterre.",
         f"{S['street']}, {S['zip']} {S['city']}, dans le quartier de l'université Paris Nanterre."),
    ]


def qa_html(items):
    return '<div class="qa">' + "".join(f"<div><h3>{esc(q)}</h3><p>{a}</p></div>" for q, a, _ in items) + "</div>"


def faq_node(items):
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": t}} for q, _, t in items]}


# ------------------------------------------------------------------ pages
def page_home():
    up, _ = animations()
    if up:
        a = up[0]
        anim = (f'<p>Chaque semaine, une animation à la pharmacie : rencontre avec un laboratoire, mini-soins par l\'équipe '
                f'ou atelier prévention.</p>{anim_html(a)}')
    else:
        anim = ('<p>Chaque semaine, une animation à la pharmacie : rencontre avec un laboratoire partenaire, mini-soins par '
                'l\'équipe ou atelier prévention. Les prochaines dates sont annoncées sur la page Animations et sur '
                f'<a href="{esc(SOCIALS[0][1])}" rel="noopener">Instagram</a>.</p>')
    items = faq_items()[:4]
    body = f'''<section class="hero"><div class="wrap hero__in"><div>
<h1>Pharmacie de Nanterre Université</h1>
<p class="lede">Votre pharmacie de proximité à Nanterre, dans le quartier de l'université Paris Nanterre. Conseil, parapharmacie, orthopédie, dépistage, réservation par téléphone et livraison dans les Hauts-de-Seine.</p>
<div class="actions">{btn("tel:" + S["tel_e164"], "Appeler la pharmacie")}{btn(shop("/ordonnance"), "Envoyer mon ordonnance", "line", ' rel="noopener"')}{btn(directions(), "Itinéraire", "line")}</div>
</div><img class="hero__logo" src="/assets/logo-pharmacie.jpg" width="720" height="720" alt="Logo de la Pharmacie de Nanterre Université : une croix à bandes entourée de feuilles"></div></section>
<section class="strip"><div class="wrap"><dl>
<div><dt>Adresse</dt><dd>{esc(S["street"])}<br>{S["zip"]} {S["city"]}</dd></div>
<div><dt>Horaires</dt><dd>Lundi au vendredi : 8h - 20h<br>Samedi : 8h30 - 20h<br>Dimanche : pharmacie de garde uniquement</dd></div>
<div><dt>Téléphone</dt><dd><a href="tel:{S["tel_e164"]}">{S["tel"]}</a><br><a href="mailto:{S["email"]}">{S["email"]}</a></dd></div>
</dl></div></section>

<section class="sec"><div class="wrap">
<h2>Une pharmacie ouverte sur le quartier</h2>
<p class="answer">La Pharmacie de Nanterre Université est une pharmacie d'officine située au {esc(S["street"])}, {S["zip"]} {S["city"]}. Elle est ouverte du lundi au vendredi de 8h à 20h, le samedi de 8h30 à 20h et les dimanches de garde. Notre équipe vous conseille pour votre santé, votre peau et votre quotidien.</p>
<p>Les titulaires, David et Jonathan Illouz, et toute l'équipe accueillent les étudiants, les familles et les habitants du quartier. Nos clients nous donnent la note de {S["rating"]}/5 sur Google, sur {S["reviews"]} avis.</p>
<ul class="svc">
<li><h3>Conseil et ordonnances</h3><p>Conseil de l'équipe, préparation des ordonnances, envoi d'ordonnance en ligne et retrait au comptoir prioritaire.</p><p><a href="/services/#conseil">Voir le détail</a></p></li>
<li><h3>Dermo-cosmétique et parapharmacie</h3><p>Diagnostic de peau personnalisé, soins Avène, La Roche-Posay, SVR et Uriage, compléments alimentaires.</p><p><a href="/dermo-cosmetique-nanterre/">Voir la dermo-cosmétique</a></p></li>
<li><h3>Orthopédie et matériel médical</h3><p>Orthèses, contention, chaussures médicales, maintien à domicile et location de matériel.</p><p><a href="/orthopedie-materiel-medical-nanterre/">Voir l'orthopédie</a></p></li>
<li><h3>Dépistage et vaccination</h3><p>Test rapide de l'angine (TROD) et vaccination sur rendez-vous.</p><p><a href="/depistage-vaccination-nanterre/">Voir le dépistage</a></p></li>
<li><h3>Nature et bien-être</h3><p>Phytothérapie, aromathérapie, gemmothérapie, herboristerie et conseil de l'équipe.</p><p><a href="/services/#nature">Voir le détail</a></p></li>
<li><h3>Maman et bébé</h3><p>Grossesse, allaitement, soins et alimentation du bébé, location de tire-lait.</p><p><a href="/services/#maman-bebe">Voir le détail</a></p></li>
</ul></div></section>

<section class="sec sec--forest"><div class="wrap">
<h2>Commander, réserver, se faire livrer</h2>
<ul class="svc">
<li><h3>Envoyer mon ordonnance</h3><p>Photographiez votre ordonnance avant de quitter le cabinet médical. Nous la préparons et vous la retirez au comptoir prioritaire, sans attendre.</p><p>{btn(shop("/ordonnance"), "Envoyer mon ordonnance", "solid", ' rel="noopener"')}</p></li>
<li><h3>Réserver par téléphone</h3><p>Notre serveur vocal permet de réserver tous les produits : médicaments, parapharmacie et matériel médical. Retrait à la pharmacie.</p><p><a href="/horaires-garde-livraison/#reservation">Comment réserver</a></p></li>
<li><h3>Livraison Uber Eats</h3><p>Produits de parapharmacie livrés dans les Hauts-de-Seine (92), du lundi au samedi de 9h à 19h. Les médicaments ne sont pas livrés.</p><p><a href="/horaires-garde-livraison/#livraison">Voir la livraison</a></p></li>
</ul></div></section>

<section class="sec"><div class="wrap"><h2>Une animation chaque semaine</h2>{anim}<p>{btn("/animations/", "Voir les animations", "line")}</p></div></section>

<section class="sec sec--tint"><div class="wrap"><h2>L'équipe</h2>
<p class="answer">David et Jonathan Illouz sont pharmaciens titulaires de la Pharmacie de Nanterre Université. Ils sont entourés d'une équipe de pharmaciens et de préparateurs.</p>
<p>{btn("/equipe/", "Rencontrer l'équipe", "line")}</p>
<div class="gallery">{photo("facade", "Façade de la Pharmacie de Nanterre Université, boulevard des Provinces Françaises", "façade de la pharmacie")}{photo("interieur", "Intérieur de la Pharmacie de Nanterre Université", "intérieur de la pharmacie")}{photo("equipe", "L'équipe de la Pharmacie de Nanterre Université", "équipe devant le comptoir")}</div>
</div></section>

<section class="sec"><div class="wrap"><h2>Ce que disent nos clients</h2>
<p class="rating">{S["rating"]}/5</p>
<p>Note moyenne sur {S["reviews"]} avis Google. <a href="{esc(S["maps"])}" rel="noopener">Lire les avis sur Google Maps</a>.</p></div></section>

<section class="sec sec--tint"><div class="wrap"><h2>Questions fréquentes</h2>{qa_html(items)}
<p style="margin-top:1.5rem">{btn("/faq/", "Toutes les questions", "line")}</p></div></section>

<section class="sec"><div class="wrap"><h2>Nous trouver</h2>
<p>{esc(S["street"])}, {S["zip"]} {S["city"]}, dans le quartier de l'université Paris Nanterre. {todo("accès : station RER / tram / bus les plus proches")}</p>{map_block()}</div></section>'''
    render("", "Pharmacie de Nanterre Université, pharmacie à Nanterre (92)",
           "Pharmacie à Nanterre Université : conseil, dermo-cosmétique, orthopédie, dépistage, livraison dans le 92. "
           "Ouvert du lundi au samedi, 8h-20h. 01 47 21 22 28.", body, home=True)


def page_services():
    def sec(i, t, b):
        return f'<section class="block" id="{i}"><h2>{t}</h2>{b}</section>'
    body = pagehead("Services de la pharmacie de Nanterre Université",
                    "Conseil, ordonnances, dermo-cosmétique, orthopédie, dépistage, réservation par téléphone et livraison. Tout ce que fait la pharmacie, en un seul endroit.",
                    "Services") + '<div class="sec"><div class="wrap">' + "".join([
        sec("conseil", "Conseil pharmaceutique et ordonnances",
            f'<p>L\'équipe vous conseille au comptoir, du lundi au samedi. Vous pouvez aussi <a href="{shop("/ordonnance")}" rel="noopener">envoyer votre ordonnance en ligne</a> : nous la préparons et vous la retirez au comptoir prioritaire. Les renouvellements peuvent être programmés.</p>'
            f'<p>Nous collectons les médicaments périmés (Cyclamed) et proposons les boîtes à aiguilles (Dastri) pour une élimination sûre.</p>'),
        sec("dermo", "Dermo-cosmétique et parapharmacie",
            '<p>Diagnostic de peau personnalisé, soins des marques Avène, La Roche-Posay, SVR et Uriage, compléments alimentaires, solaire, hygiène, bébé.</p><p><a href="/dermo-cosmetique-nanterre/">Découvrir la dermo-cosmétique</a></p>'),
        sec("nature", "Nature : phytothérapie, aromathérapie, herboristerie",
            '<p>Plantes, huiles essentielles, gemmothérapie, apithérapie et herboristerie. Notre équipe vous explique comment utiliser ces produits.</p>'),
        sec("maman-bebe", "Maman et bébé",
            '<p>Grossesse, allaitement, soins et alimentation du bébé, biberonnerie, change, éveil. Location de tire-lait et de pèse-bébé.</p>'),
        sec("orthopedie", "Orthopédie, contention et matériel médical",
            '<p>Orthèses, contention, chaussures médicales et semelles, incontinence, maintien à domicile, location de matériel.</p><p><a href="/orthopedie-materiel-medical-nanterre/">Découvrir l\'orthopédie et le matériel médical</a></p>'),
        sec("depistage", "Dépistage et vaccination",
            '<p>Test rapide de l\'angine (TROD) et vaccination sur rendez-vous.</p><p><a href="/depistage-vaccination-nanterre/">Découvrir le dépistage et la vaccination</a></p>'),
        sec("tabac", "Accompagnement à l'arrêt du tabac",
            '<p>L\'équipe vous conseille et vous accompagne dans votre démarche d\'arrêt du tabac.</p>'),
        sec("reservation", "Réservation de produits par serveur vocal",
            f'<p>Appelez notre serveur vocal ({todo("numéro du serveur vocal")}) pour réserver tous vos produits : médicaments, parapharmacie, matériel médical. Retirez-les ensuite à la pharmacie. Pour un médicament sur ordonnance, présentez l\'ordonnance au retrait.</p>'),
        sec("livraison", "Livraison",
            f'<p>Les produits de parapharmacie sont livrés via Uber Eats dans les Hauts-de-Seine (92), du lundi au samedi de 9h à 19h. Pour la parapharmacie commandée sur <a href="{shop()}" rel="noopener">notre boutique en ligne</a>, la livraison Colissimo et le retrait en point relais sont possibles. Les médicaments ne sont pas concernés par la livraison.</p>'),
        sec("animations", "Animations, mini-soins et ateliers prévention",
            '<p>Une animation chaque semaine : rencontres avec des laboratoires, mini-soins par l\'équipe, ateliers prévention.</p><p><a href="/animations/">Voir les animations</a></p>'),
        sec("fidelite", "Carte avantage et parrainage",
            '<p>Une carte avantage et un parrainage (5 % de réduction pour le parrain et le filleul sur les produits éligibles). Demandez à l\'équipe.</p>'),
        sec("accessibilite", "Accessibilité",
            '<p>La pharmacie est accessible aux personnes en fauteuil roulant et en situation de handicap.</p>'),
        sec("application", "Application mobile",
            f'<p>Prenez rendez-vous, envoyez vos ordonnances et commandez en quelques clics avec <a href="{shop("/application-mobile")}" rel="noopener">l\'application de la pharmacie</a>.</p>'),
    ]) + "</div></div>"
    render("services", "Services de la pharmacie à Nanterre Université",
           "Conseil, ordonnances, dermo-cosmétique, orthopédie, dépistage TROD, vaccination, réservation par téléphone "
           "et livraison dans le 92. Pharmacie de Nanterre Université.", body, crumb="Services")


def page_dermo():
    body = pagehead("Dermo-cosmétique et parapharmacie à Nanterre",
                    "Un diagnostic de peau personnalisé, des soins de marques de pharmacie et le conseil de l'équipe, boulevard des Provinces Françaises.",
                    "Dermo-cosmétique") + f'''<div class="sec"><div class="wrap prose">
<h2>Un diagnostic de peau personnalisé</h2>
<p>À la Pharmacie de Nanterre Université, l'équipe réalise un diagnostic de peau personnalisé pour vous aider à choisir vos soins. Venez avec vos habitudes et vos questions : nous adaptons le conseil à votre peau et à votre budget.</p>
<h2>Les marques que vous trouvez à la pharmacie</h2>
<ul>
<li><strong>Soins de la peau :</strong> Avène, La Roche-Posay, SVR, Uriage, ainsi que de la skincare coréenne.</li>
<li><strong>Compléments alimentaires :</strong> Pileje, Aragan, Solgar, NHCO, Biocyte, EA Pharma.</li>
<li><strong>Nature :</strong> aromathérapie, phytothérapie, gemmothérapie, apithérapie.</li>
</ul>
<h2>Visage, corps, cheveux, solaire, bébé</h2>
<p>Démaquillants, nettoyants, sérums, soins du visage et des yeux, hygiène du corps, soins des mains et des pieds, shampoings et soins des cheveux, protection solaire et après-soleil, soins et toilette du bébé : l'équipe vous oriente vers le produit adapté.</p>
<h2>Découvrir, tester, commander</h2>
<p>Chaque semaine, des animations avec les laboratoires partenaires permettent de tester les produits et de découvrir les nouveautés. Vous pouvez aussi commander en ligne sur <a href="{shop()}" rel="noopener">notre boutique</a>, ou vous faire livrer en parapharmacie via Uber Eats dans le 92.</p>
<p>{btn("/animations/", "Voir les animations", "line")} {btn("tel:" + S["tel_e164"], "Appeler la pharmacie")}</p>
</div></div>'''
    render("dermo-cosmetique-nanterre", "Dermo-cosmétique et parapharmacie à Nanterre, pharmacie",
           "Diagnostic de peau personnalisé, Avène, La Roche-Posay, SVR, Uriage, compléments alimentaires. "
           "Pharmacie de Nanterre Université, Nanterre (92).", body, crumb="Dermo-cosmétique")


def page_ortho():
    body = pagehead("Orthopédie, contention et matériel médical à Nanterre",
                    "Orthèses, contention, chaussures médicales, matériel de maintien à domicile et location : l'équipe vous conseille et vous oriente.",
                    "Orthopédie et matériel médical") + f'''<div class="sec"><div class="wrap prose">
<h2>Orthopédie</h2>
<p>Ceintures lombaires et de maternité, colliers cervicaux, attelles, coudières, genouillères et chevillères : un rayon d'orthopédie pour le cou, le dos, l'épaule, le coude, le poignet, le genou et la cheville.</p>
<h2>Podologie et chaussures médicales</h2>
<p>Semelles, talonnettes, protecteurs, chaussures orthopédiques et chaussures médicales, bottes de marche post-opératoires. Des bilans podologiques gratuits sont proposés à certaines dates : suivez nos réseaux ou demandez à l'équipe.</p>
<h2>Contention</h2>
<p>Chaussettes, bas et collants de contention pour homme et femme, bandes de contention, contention maternité.</p>
<h2>Maintien à domicile et location</h2>
<p>Tensiomètres, oxymètres, thermomètres, cannes et déambulateurs, aides au quotidien, incontinence. Location de matériel : tire-lait, pèse-bébé, déambulateur, fauteuil roulant, lit médicalisé, matériel d'aérosolthérapie et d'apnée du sommeil, selon disponibilité.</p>
<h2>Prise en charge et conseil</h2>
<p>La prise en charge dépend de votre situation et de votre prescription. Présentez votre ordonnance : l'équipe vous explique les options et les démarches. Vous pouvez aussi <a href="{shop("/ordonnance")}" rel="noopener">envoyer votre ordonnance en ligne</a>.</p>
<p>{btn("tel:" + S["tel_e164"], "Appeler la pharmacie")} {btn(directions(), "Itinéraire", "line")}</p>
</div></div>'''
    render("orthopedie-materiel-medical-nanterre", "Orthopédie, contention et matériel médical à Nanterre",
           "Orthèses, contention, chaussures médicales, semelles, location de matériel médical et maintien à domicile. "
           "Pharmacie de Nanterre Université (92).", body, crumb="Orthopédie et matériel médical")


def page_depistage():
    body = pagehead("Dépistage (TROD) et vaccination à Nanterre",
                    "Test rapide de l'angine et vaccination en pharmacie, sans quitter le quartier.",
                    "Dépistage et vaccination") + f'''<div class="sec"><div class="wrap prose">
<h2>Test de l'angine (TROD)</h2>
<p>Un test rapide d'orientation diagnostique (TROD) permet de savoir si un mal de gorge est d'origine bactérienne. Il est réalisé par un membre de l'équipe à la pharmacie. <a href="{shop("/trod-angine/nouveau")}" rel="noopener">Prendre rendez-vous pour le test de l'angine</a>.</p>
<h2>Vaccination en pharmacie</h2>
<p>Nous vaccinons sur rendez-vous. Les vaccins que nous pouvons réaliser dépendent de la réglementation en vigueur. {todo("liste des vaccins proposés")} <a href="{shop("/rendez-vous")}" rel="noopener">Prendre rendez-vous</a> ou appeler le <a href="tel:{S["tel_e164"]}">{S["tel"]}</a>.</p>
<h2>Prévention</h2>
<p>Nous organisons régulièrement des ateliers prévention. Consultez la page <a href="/animations/">Animations</a>.</p>
<p>Ces informations ne remplacent pas l'avis d'un médecin. En cas d'urgence, appelez le 15.</p>
<p>{btn(shop("/rendez-vous"), "Prendre rendez-vous", "solid", ' rel="noopener"')}</p>
</div></div>'''
    render("depistage-vaccination-nanterre", "Dépistage angine (TROD) et vaccination à Nanterre",
           "Test rapide de l'angine (TROD) et vaccination sur rendez-vous à la Pharmacie de Nanterre Université, "
           "boulevard des Provinces Françaises.", body, crumb="Dépistage et vaccination")


def page_equipe():
    people = ""
    for key, name in OWNERS:
        people += (f'<div class="person" id="{key}">{photo(key, f"{name}, pharmacien titulaire", f"portrait de {name}")}'
                   f'<h3>{name}</h3><p class="role">Pharmacien titulaire</p>'
                   f'<p>{name} est pharmacien titulaire de la {S["name"]}. {todo("courte présentation de " + name)}</p></div>')
    body = pagehead("L'équipe de la pharmacie de Nanterre Université",
                    "Deux pharmaciens titulaires et une équipe qui vous accueille et vous conseille du lundi au samedi.",
                    "Équipe") + f'''<div class="sec"><div class="wrap">
<h2>Les pharmaciens titulaires</h2>
<p class="answer">La pharmacie est dirigée par David Illouz et Jonathan Illouz, pharmaciens titulaires.</p>
<div class="people">{people}</div>
<h2 style="margin-top:3rem">Pharmaciens adjoints et préparateurs</h2>
<p>Une équipe de pharmaciens et de préparateurs vous conseille au comptoir et prépare vos ordonnances. {todo("prénoms et fonctions des autres membres de l'équipe")}</p>
<div class="gallery">{photo("equipe", "L'équipe de la Pharmacie de Nanterre Université", "équipe devant le comptoir")}</div>
<p style="margin-top:1.5rem">{btn("/contact/", "Contacter l'équipe", "line")}</p>
</div></div>'''
    render("equipe", "L'équipe de la Pharmacie de Nanterre Université",
           "David et Jonathan Illouz, pharmaciens titulaires, et l'équipe de la pharmacie de Nanterre Université. "
           "Conseil du lundi au samedi.", body, crumb="Équipe")


def page_animations():
    up, past = animations()
    if up:
        prog = "".join(anim_html(a) for a in up)
    else:
        prog = (f'<p>Le programme des prochaines semaines sera publié ici. Pour ne rien manquer, suivez-nous sur '
                f'<a href="{esc(SOCIALS[0][1])}" rel="noopener">Instagram</a> ou appelez le <a href="tel:{S["tel_e164"]}">{S["tel"]}</a>.</p>')
    arch = ""
    if past:
        arch = '<h2 style="margin-top:3rem">Les dernières animations</h2>' + "".join(anim_html(a) for a in past)
    body = pagehead("Animations, mini-soins et ateliers prévention",
                    "Chaque semaine, la pharmacie organise une animation : laboratoires partenaires, mini-soins par l'équipe, ateliers prévention.",
                    "Animations") + f'''<div class="sec"><div class="wrap">
<h2>Rendez-vous chaque semaine</h2>
<p class="answer">Une animation a lieu à la pharmacie chaque semaine, {todo("jour et créneau habituels")}. Elle est gratuite.</p>
<h2>Au programme</h2>{prog}
<h2 style="margin-top:3rem">Trois types d'animations</h2>
<ul class="svc">
<li><h3>Animations laboratoires</h3><p>Rencontre avec une marque partenaire : test des produits, découverte des nouveautés, conseils d'utilisation.</p></li>
<li><h3>Mini-soins par l'équipe</h3><p>Un moment de soin réalisé par l'équipe de la pharmacie. {todo("liste des mini-soins proposés")}</p></li>
<li><h3>Ateliers prévention</h3><p>Des ateliers pour mieux comprendre sa santé et la préserver. {todo("thèmes des ateliers prévention")}</p></li>
</ul>
{arch}
<p style="margin-top:2rem">Inscription : {todo("modalités d'inscription (sur place, téléphone, en ligne)")}</p>
</div></div>'''
    render("animations", "Animations et ateliers prévention, pharmacie à Nanterre",
           "Une animation chaque semaine à la Pharmacie de Nanterre Université : laboratoires partenaires, mini-soins "
           "et ateliers prévention. Gratuit.", body, extra_graph=event_nodes(), crumb="Animations")


def page_garde():
    g = gardes()
    if g:
        lst = "<ul>" + "".join(f"<li>{fdate(d)} : {span(o, c)}</li>" for d, o, c in g) + "</ul>"
    else:
        lst = (f'<p>Le calendrier de nos prochains dimanches de garde sera publié ici. En attendant, consultez '
               f'<a href="{shop("/pharmacies-de-garde")}" rel="noopener">la page des pharmacies de garde</a> ou le site '
               f'monpharmacien-idf.fr.</p>')
    body = pagehead("Horaires, pharmacie de garde, livraison et réservation",
                    "Quand nous sommes ouverts, comment réserver vos produits par téléphone et comment vous faire livrer dans les Hauts-de-Seine.",
                    "Horaires, garde et livraison") + f'''<div class="sec"><div class="wrap">
<div class="prose">
<h2>Horaires d'ouverture</h2>
{hours_table("Horaires de la pharmacie", HOURS, "Fermé, sauf dimanches de garde")}
<p>Les jours fériés, les horaires peuvent changer : appelez le <a href="tel:{S["tel_e164"]}">{S["tel"]}</a>.</p>
</div>
<div class="block" id="garde"><h2>Dimanches de garde</h2>
<p>La pharmacie est ouverte le dimanche uniquement les dimanches où elle est de garde, en général de {span(*GARDE_HOURS)}.</p>{lst}</div>
<div class="block" id="reservation"><h2>Réserver vos produits par téléphone</h2>
<p>Notre serveur vocal ({todo("numéro du serveur vocal")}) permet de réserver tous les produits : médicaments, parapharmacie, matériel médical. {todo("horaires du serveur vocal")}</p>
<p>Vous retirez votre réservation à la pharmacie. Pour un médicament sur ordonnance, présentez l'ordonnance au retrait. Délai de mise de côté : {todo("durée de mise de côté")}.</p>
<p>Autre option : <a href="{shop("/ordonnance")}" rel="noopener">envoyer votre ordonnance en ligne</a> et la retirer au comptoir prioritaire.</p></div>
<div class="block" id="livraison"><h2>Livraison de parapharmacie</h2>
<p>Les produits de parapharmacie sont livrés via Uber Eats dans les Hauts-de-Seine (92). Les médicaments ne sont pas livrés par ce service.</p>
{hours_table("Horaires de livraison", DELIV, "Pas de livraison")}
<p>Pour les commandes de parapharmacie sur <a href="{shop()}" rel="noopener">notre boutique en ligne</a>, la livraison Colissimo et le retrait en point relais sont possibles.</p></div>
<div class="block" id="acces"><h2>Nous trouver</h2>
<p>{esc(S["street"])}, {S["zip"]} {S["city"]}, dans le quartier de l'université Paris Nanterre. La pharmacie est accessible aux personnes en fauteuil roulant. {todo("accès : station RER / tram / bus les plus proches")}</p>{map_block()}</div>
</div></div>'''
    render("horaires-garde-livraison", "Horaires, pharmacie de garde et livraison à Nanterre (92)",
           "Horaires de la Pharmacie de Nanterre Université, dimanches de garde, réservation par téléphone et livraison "
           "de parapharmacie dans le 92 (Uber Eats).", body, extra_graph=None, crumb="Horaires, garde et livraison")


def page_faq():
    items = faq_items()
    body = pagehead("Questions fréquentes sur la pharmacie",
                    "Horaires, garde, livraison, réservation, ordonnance, dépistage : les réponses aux questions que l'on nous pose le plus.",
                    "FAQ") + f'<div class="sec"><div class="wrap">{qa_html(items)}<p style="margin-top:2rem">Une autre question ? {btn("tel:" + S["tel_e164"], "Appeler la pharmacie")}</p></div></div>'
    render("faq", "FAQ : horaires, garde, livraison, ordonnance (Nanterre)",
           "Réponses aux questions sur la Pharmacie de Nanterre Université : horaires, dimanche de garde, livraison, "
           "réservation par téléphone, ordonnance en ligne, TROD angine.", body, extra_graph=[faq_node(items)], crumb="FAQ")


def page_contact():
    soc = "".join(f'<li><a href="{esc(u)}" rel="noopener">{n}</a></li>' for n, u in SOCIALS)
    body = pagehead("Contacter la pharmacie de Nanterre Université",
                    "Par téléphone, par e-mail ou sur place : nous répondons du lundi au samedi.",
                    "Contact") + f'''<div class="sec"><div class="wrap"><div class="prose">
<h2>Coordonnées</h2>
<p><strong>{esc(S["name"])}</strong><br>{esc(S["street"])}<br>{S["zip"]} {S["city"]}</p>
<p>Téléphone : <a href="tel:{S["tel_e164"]}">{S["tel"]}</a><br>E-mail : <a href="mailto:{S["email"]}">{S["email"]}</a></p>
<p>Pour échanger en sécurité sur un rendez-vous, une ordonnance ou un produit, utilisez la <a href="{shop("/#chat-trigger")}" rel="noopener">messagerie de notre site de commande</a>.</p>
{hours_table("Horaires", HOURS, "Fermé, sauf dimanches de garde")}
<h2>Réseaux sociaux</h2><ul>{soc}</ul>
<h2>Plan d'accès</h2></div>{map_block()}
<p style="margin-top:1.5rem">{btn("tel:" + S["tel_e164"], "Appeler")} {btn(directions(), "Itinéraire", "line")}</p></div></div>'''
    render("contact", "Contact et accès : Pharmacie de Nanterre Université",
           "Adresse, téléphone, e-mail et plan d'accès de la Pharmacie de Nanterre Université, 390 boulevard des "
           "Provinces Françaises, Nanterre.", body, crumb="Contact")


def page_legal():
    body = pagehead("Mentions légales et confidentialité", "Informations légales sur l'éditeur du site et sur vos données.",
                    "Mentions légales") + f'''<div class="sec"><div class="wrap prose">
<h2>Éditeur du site</h2>
<p>{esc(S["name"])}, officine de pharmacie. Forme juridique : {todo("forme juridique (SELARL, SNC...)")}.<br>
Adresse : {esc(S["street"])}, {S["zip"]} {S["city"]}.<br>Téléphone : {S["tel"]}. E-mail : {S["email"]}.</p>
<p>Pharmaciens titulaires et directeurs de la publication : David Illouz ({todo("n° RPPS de David Illouz")}) et Jonathan Illouz ({todo("n° RPPS de Jonathan Illouz")}).<br>
N° de licence de l'officine : {todo("n° de licence ou FINESS de l'officine")}.</p>
<h2>Autorité et ordre professionnel</h2>
<p>Pharmaciens inscrits à l'Ordre national des pharmaciens (<a href="https://www.ordre.pharmacien.fr" rel="noopener">ordre.pharmacien.fr</a>), section {todo("section et conseil régional de l'Ordre")}. Agence régionale de santé d'Île-de-France.</p>
<h2>Hébergeur</h2>
<p>{todo("nom et adresse de l'hébergeur du site")}</p>
<h2>Santé et information</h2>
<p>Les informations de ce site sont données à titre d'information et ne remplacent pas l'avis d'un médecin ou d'un pharmacien. Ce site ne fait pas la promotion de médicaments. En cas d'urgence, appelez le 15.</p>
<h2>Données personnelles et cookies</h2>
<p>Ce site ne dépose pas de cookie de suivi et n'utilise pas d'outil de mesure d'audience. La carte Google Maps ne se charge qu'après votre clic : Google peut alors recevoir des données sur votre navigation. Si vous nous écrivez par e-mail ou par téléphone, nous utilisons vos informations uniquement pour vous répondre. Vous pouvez demander l'accès, la rectification ou la suppression de vos données à {S["email"]}.</p>
<p>Les commandes et rendez-vous en ligne sont gérés sur <a href="{shop()}" rel="noopener">notre site de commande</a>, qui a sa propre politique de confidentialité.</p>
<h2>Propriété intellectuelle</h2>
<p>Le logo, les textes et les photos de ce site appartiennent à la {esc(S["name"])}. Toute reproduction sans autorisation est interdite.</p>
</div></div>'''
    render("mentions-legales", "Mentions légales, Pharmacie de Nanterre Université",
           "Mentions légales, informations sur l'éditeur et politique de confidentialité du site de la Pharmacie de "
           "Nanterre Université.", body, crumb="Mentions légales")
    PAGES[-1] = (PAGES[-1][0], PAGES[-1][1], "0.3")


# ------------------------------------------------------------------ fichiers techniques
def rebase(text):
    """Préfixe les liens internes (/...) par BASE quand le site n'est pas servi à la racine du domaine."""
    if NOINDEX:
        text = text.replace("<head>", '<head><meta name="robots" content="noindex">', 1)
    if not BASE:
        return text
    return re.sub(r'((?:href|src)=")/(?!/)', rf"\1{BASE}/", text)


def write(rel, text):
    if rel.endswith(".html"):
        text = rebase(text)
    p = DIST / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def technical_files():
    now = TODAY.isoformat()
    urls = "".join(f"<url><loc>{url(s)}</loc><lastmod>{now}</lastmod><priority>{p}</priority></url>\n"
                   for s, _, p in PAGES)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")
    bots = ["Googlebot", "Bingbot", "OAI-SearchBot", "ChatGPT-User", "GPTBot", "Claude-SearchBot", "Claude-User",
            "ClaudeBot", "PerplexityBot", "Google-Extended", "Applebot"]
    robots = ("# Tous les robots sont autorisés, y compris ceux des assistants IA (recherche et réponses).\n"
              "# Pour refuser l'entraînement des modèles tout en restant cité dans les réponses,\n"
              "# remplacer 'Allow: /' par 'Disallow: /' pour GPTBot, ClaudeBot et Google-Extended uniquement.\n\n"
              "User-agent: *\nAllow: /\n\n"
              + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots)
              + f"Sitemap: {DOMAIN}/sitemap.xml\n")
    if NOINDEX:
        robots = "# Site d'aperçu : non référencé par les moteurs de recherche.\nUser-agent: *\nDisallow: /\n"
    write("robots.txt", robots)

    g = gardes()
    garde_txt = ("; ".join(f"{fdate(d)} ({span(o, c)})" for d, o, c in g)) if g else "calendrier publié sur la page Horaires et garde"
    up, _ = animations()
    anim_txt = "; ".join(f"{when(a)} : {a['titre']}" for a in up) if up else "une animation chaque semaine, programme sur la page Animations"
    llms = f"""# {S['name']}

> Pharmacie d'officine à Nanterre (92), dans le quartier de l'université Paris Nanterre. Conseil, dermo-cosmétique, orthopédie, dépistage TROD, vaccination, réservation de produits par téléphone, livraison de parapharmacie dans les Hauts-de-Seine, animations hebdomadaires.

## Informations clés
- Adresse : {S['street']}, {S['zip']} {S['city']}
- Téléphone : {S['tel']} ({S['tel_e164']})
- E-mail : {S['email']}
- Horaires : lundi au vendredi 8h-20h ; samedi 8h30-20h ; dimanche fermé sauf dimanches de garde (en général 9h-20h)
- Prochains dimanches de garde : {garde_txt}
- Pharmaciens titulaires : David Illouz et Jonathan Illouz
- Note Google : {S['rating']}/5 sur {S['reviews']} avis
- Accessibilité : accès fauteuil roulant
- Livraison : produits de parapharmacie uniquement (Uber Eats), Hauts-de-Seine (92), lundi au samedi 9h-19h. Les médicaments ne sont pas livrés.
- Réservation : tous les produits (médicaments, parapharmacie, matériel médical) par serveur vocal, retrait à la pharmacie.
- Animations : {anim_txt}

## Pages
- [Accueil]({url('')}): présentation de la pharmacie
- [Services]({url('services')}): liste complète des services
- [Dermo-cosmétique]({url('dermo-cosmetique-nanterre')}): diagnostic de peau, marques Avène, La Roche-Posay, SVR, Uriage
- [Orthopédie et matériel médical]({url('orthopedie-materiel-medical-nanterre')}): orthèses, contention, location
- [Dépistage et vaccination]({url('depistage-vaccination-nanterre')}): TROD angine, vaccination sur rendez-vous
- [Équipe]({url('equipe')}): pharmaciens titulaires et équipe
- [Animations]({url('animations')}): animations laboratoires, mini-soins, ateliers prévention
- [Horaires, garde et livraison]({url('horaires-garde-livraison')}): horaires, dimanches de garde, livraison, réservation
- [FAQ]({url('faq')}): questions fréquentes
- [Contact]({url('contact')}): coordonnées et plan d'accès

## Services en ligne
- [Envoyer une ordonnance]({shop('/ordonnance')})
- [Boutique en ligne de parapharmacie]({shop()})
- [Prendre rendez-vous]({shop('/rendez-vous')})
- [Pharmacies de garde]({shop('/pharmacies-de-garde')})

## Réseaux
""" + "".join(f"- [{n}]({u})\n" for n, u in SOCIALS)
    write("llms.txt", llms)
    write("404.html", f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page introuvable</title><meta name="robots" content="noindex"><link rel="stylesheet" href="/assets/style.css"></head>
<body><main class="sec"><div class="wrap"><h1>Page introuvable</h1><p>Cette page n'existe pas ou a été déplacée.</p>
<p>{btn("/", "Retour à l'accueil")} {btn("tel:" + S["tel_e164"], "Appeler la pharmacie", "line")}</p></div></main></body></html>''')


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "assets", DIST / "assets")
    for fn in (page_home, page_services, page_dermo, page_ortho, page_depistage, page_equipe,
               page_animations, page_garde, page_faq, page_contact, page_legal):
        fn()
    technical_files()
    lines = "\n".join(f"- [ ] {t}" for t in TODOS)
    (ROOT / "A_COMPLETER.md").write_text(
        "# À compléter avant la mise en ligne\n\n"
        "Ces éléments apparaissent en jaune sur le site tant qu'ils ne sont pas remplis (texte dans build.py,\n"
        "photos dans assets/photos/, puis relancer `python3 build.py`).\n\n"
        f"- [ ] Remplacer DOMAIN dans build.py par l'adresse réelle du site (actuellement {DOMAIN})\n"
        f"{lines}\n", encoding="utf-8")
    print(f"{len(PAGES)} pages générées dans {DIST}")
    print(f"{len(TODOS)} éléments à compléter :")
    for t in TODOS:
        print("  -", t)


if __name__ == "__main__":
    main()
