# Site vitrine : Pharmacie de Nanterre Université

Site statique (HTML/CSS, aucun framework, aucun cookie), généré par `build.py`.

## Mettre en ligne
1. Ouvrir `build.py` et remplacer `DOMAIN` par l'adresse réelle du site (ex. https://www.pharmacie-nanterre-universite.fr).
2. Compléter les éléments listés dans `A_COMPLETER.md` (ils apparaissent en jaune sur le site tant qu'ils ne sont pas remplis).
3. Lancer `python3 build.py` : le dossier `dist/` contient le site.
4. Envoyer le contenu de `dist/` à la racine de l'hébergement (OVH, Netlify, Cloudflare Pages, etc.). Le site doit être servi à la racine du domaine.

Aperçu local : `python3 -m http.server -d dist 8000` puis http://localhost:8000

## Photos
Déposer dans `assets/photos/` (JPG, PNG ou WebP, de préférence moins de 400 Ko) : `facade`, `interieur`, `equipe`, `david-illouz`, `jonathan-illouz`.
Relancer `python3 build.py`. Pour les photos de personnes, obtenir leur accord (droit à l'image).

## Animations de la semaine
Éditer `data/animations.json` (modèle : `data/animations.exemple.json`), puis relancer `python3 build.py` et remettre `dist/` en ligne.
Les animations passées passent automatiquement dans « Les dernières animations ». Les événements sont aussi publiés en données structurées.

## Dimanches de garde
Éditer `data/gardes.json` (modèle : `data/gardes.exemple.json`). Les dates alimentent la page Horaires et garde,
le fichier llms.txt et les horaires exceptionnels en données structurées.

## Après la mise en ligne
- Déclarer le site dans Google Search Console et Bing Webmaster Tools, soumettre `sitemap.xml`.
- Google Business Profile : dimanche « fermé » dans les horaires habituels, horaires exceptionnels pour chaque dimanche de garde, lien vers le site, livraison.
- Harmoniser nom, adresse, téléphone et horaires partout : Apothical, Doctolib, Pages Jaunes, Pharmanity, Santé.fr, Bing Places, Apple Business Connect.
- Chaque mois, poser les 10 questions types à ChatGPT, Claude, Gemini et Perplexity (recherche web activée) et noter si la pharmacie est citée.

## Choix techniques
- Données structurées JSON-LD : Pharmacy, Service (livraison), Person, FAQPage, Event, BreadcrumbList.
- La note Google (4,6/5, 470 avis) est affichée en texte mais n'est pas déclarée en AggregateRating : Google ignore les avis qu'une entreprise publie sur son propre site.
- Aucune description ni aucun prix de médicament : seulement des services et de la parapharmacie.
- La carte Google Maps ne se charge qu'au clic (RGPD).
- Horaires de garde « 9h - 20h » repris de la fiche Google : à confirmer.
