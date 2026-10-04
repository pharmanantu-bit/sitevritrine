// La carte Google Maps ne se charge qu'au clic (RGPD : aucun cookie ni donnée envoyée avant).
document.querySelectorAll('[data-map]').forEach(function (box) {
  var btn = box.querySelector('button');
  if (!btn) return;
  btn.addEventListener('click', function () {
    var f = document.createElement('iframe');
    f.src = box.getAttribute('data-map');
    f.title = 'Carte : Pharmacie de Nanterre Université';
    f.loading = 'lazy';
    f.referrerPolicy = 'no-referrer-when-downgrade';
    box.replaceChildren(f);
  });
});
