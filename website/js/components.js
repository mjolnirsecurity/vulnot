/* ================================================================
   Shared Nav + Footer injector for all VULNOT pages
   ================================================================ */
(function () {
    // Determine path prefix from meta tag (0 = root, 1 = one level deep)
    var meta = document.querySelector('meta[name="path-depth"]');
    var depth = meta ? parseInt(meta.content, 10) : 0;
    var prefix = depth === 1 ? '../' : '';

    // Determine current page for active link highlight
    var path = window.location.pathname;
    var page = path.substring(path.lastIndexOf('/') + 1) || 'index.html';

    function isActive(href) {
        if (href === 'index.html' && (page === 'index.html' || page === '' || path.endsWith('/'))) return true;
        return page === href;
    }

    var links = [
        { href: 'index.html', label: 'Home' },
        { href: 'dashboards.html', label: 'Dashboards' },
        { href: 'training.html', label: 'Training' },
        { href: 'offensive.html', label: 'Offensive' },
        { href: 'defensive.html', label: 'Defensive' },
        { href: 'forensics.html', label: 'Forensics' },
        { href: 'siem.html', label: 'SIEM' },
        { href: 'contact.html', label: 'Contact' }
    ];

    var navLinks = links.map(function (l) {
        var cls = isActive(l.href) ? ' class="active"' : '';
        return '<a href="' + prefix + l.href + '"' + cls + '>' + l.label + '</a>';
    }).join('');

    var navHTML = '<nav><div class="container">'
        + '<a href="' + prefix + 'index.html" class="logo">'
        + '<img src="' + prefix + 'img/ms_sec-logo.png" alt="Mjolnir Security">'
        + '<span>VULNOT</span></a>'
        + '<button class="hamburger" aria-label="Toggle menu">&#9776;</button>'
        + '<div class="links">' + navLinks + '</div>'
        + '</div></nav>';

    var footerHTML = '<footer><div class="container">'
        + '<p>VULNOT v1.0 &mdash; Developed by Milind Bhargava at Mjolnir Security</p>'
        + '</div></footer>';

    // Inject nav
    var navEl = document.getElementById('site-nav');
    if (navEl) navEl.innerHTML = navHTML;

    // Inject footer
    var footEl = document.getElementById('site-footer');
    if (footEl) footEl.innerHTML = footerHTML;

    // Hamburger toggle
    var burger = document.querySelector('.hamburger');
    if (burger) {
        burger.addEventListener('click', function () {
            var linksDiv = document.querySelector('nav .links');
            if (linksDiv) linksDiv.classList.toggle('open');
        });
    }
})();
