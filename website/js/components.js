/* ================================================================
   Shared Nav + Footer + Fullscreen HMI Dashboard Controller
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
        + '<p>VULNOT v2.0 &mdash; Developed by Milind Bhargava at Mjolnir Security &bull; Moodle LMS: <a href="https://portal.mjolnir.training" target="_blank" rel="noopener" style="color:#00d4ff;text-decoration:none;">portal.mjolnir.training</a></p>'
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

    // ================================================================
    // 15 HMI Dashboards Catalog
    // ================================================================
    var DASHBOARDS = [
        { slug: 'water-treatment.html', title: '01. Water Treatment Plant (Modbus :502)' },
        { slug: 'power-grid.html', title: '02. Power Grid Substation (DNP3 :20000)' },
        { slug: 'manufacturing.html', title: '03. Manufacturing Line (S7comm :102)' },
        { slug: 'chemical-reactor.html', title: '04. Chemical Reactor R-101 (OPC UA :4840)' },
        { slug: 'building-automation.html', title: '05. Building Automation (BACnet :47808)' },
        { slug: 'packaging-line.html', title: '06. Packaging Line PL-01 (EtherNet/IP :44818)' },
        { slug: 'iiot-factory.html', title: '07. IIoT Smart Factory (MQTT :1883)' },
        { slug: 'cnc-motion.html', title: '08. CNC Motion Control (PROFINET :34964)' },
        { slug: 'historian.html', title: '09. OT Data Historian (HTTP :8553)' },
        { slug: 'ai-scada-copilot.html', title: '10. AI SCADA Copilot & MCP Server (:8090)' },
        { slug: 'ai-pdm-vision.html', title: '11. AI PdM & Edge Vision QC (:8091)' },
        { slug: 'rl-chiller-soar.html', title: '12. RL Chiller Optimizer & OT SOAR (:8092)' },
        { slug: 'district-heating.html', title: '13. Municipal District Heating (Modbus :5020)' },
        { slug: 'der-bess-microgrid.html', title: '14. DER Solar, BESS & OCPP EV Depot (:8093)' },
        { slug: 'efs-blood-cryo.html', title: '15. EFS Blood Plasma Cryo-Storage (:5021)' }
    ];

    // Map each training lab ID to its corresponding HMI dashboard
    var LAB_TO_DASHBOARD = {
        'lab-01': 'water-treatment.html',
        'lab-02': 'water-treatment.html',
        'lab-03': 'power-grid.html',
        'lab-04': 'manufacturing.html',
        'lab-05': 'chemical-reactor.html',
        'lab-06': 'building-automation.html',
        'lab-07': 'iiot-factory.html',
        'lab-08': 'historian.html',
        'lab-09': 'power-grid.html',
        'lab-10': 'packaging-line.html',
        'lab-11': 'cnc-motion.html',
        'lab-12': 'ai-scada-copilot.html',
        'lab-13': 'ai-pdm-vision.html',
        'lab-14': 'rl-chiller-soar.html',
        'lab-15': 'der-bess-microgrid.html',
        'lab-16': 'efs-blood-cryo.html',
        'forensics-01': 'manufacturing.html',
        'forensics-02': 'power-grid.html',
        'forensics-03': 'chemical-reactor.html',
        'forensics-04': 'historian.html',
        'forensics-05': 'water-treatment.html',
        'forensics-06': 'district-heating.html',
        'forensics-07': 'power-grid.html',
        'forensics-08': 'efs-blood-cryo.html',
        'soc-01': 'water-treatment.html',
        'soc-02-dpi': 'water-treatment.html',
        'soc-02': 'power-grid.html',
        'soc-03': 'chemical-reactor.html',
        'soc-04': 'historian.html',
        'soc-05-cbf': 'building-automation.html',
        'soc-05': 'ai-scada-copilot.html'
    };

    // ================================================================
    // Standalone Dashboard Page Mode (website/dashboards/*.html)
    // ================================================================
    var frameEl = document.querySelector('.dashboard-frame');
    if (frameEl) {
        document.body.classList.add('hmi-fullscreen-page');
        if (window.location.search.indexOf('embed=1') !== -1 || window.self !== window.top) {
            document.body.classList.add('hmi-embed-mode');
        } else {
            var statusBar = frameEl.querySelector('.status-bar');
            if (statusBar) {
                var fsBtn = document.createElement('button');
                fsBtn.type = 'button';
                fsBtn.className = 'hmi-inline-fs-btn';
                fsBtn.innerHTML = '&#x26F6; Fullscreen';
                fsBtn.addEventListener('click', function () {
                    if (!document.fullscreenElement) {
                        document.documentElement.requestFullscreen().catch(function () {});
                    } else {
                        document.exitFullscreen().catch(function () {});
                    }
                });
                document.addEventListener('fullscreenchange', function () {
                    fsBtn.innerHTML = document.fullscreenElement ? '&#x2715; Exit Fullscreen' : '&#x26F6; Fullscreen';
                });

                var backLink = document.createElement('a');
                backLink.href = prefix + 'dashboards.html';
                backLink.className = 'hmi-inline-fs-btn';
                backLink.innerHTML = '&larr; All 15 HMIs';

                statusBar.appendChild(fsBtn);
                statusBar.appendChild(backLink);
            }
        }
    }

    // ================================================================
    // Fullscreen Modal <dialog> for Dashboards on index / dashboards / training
    // ================================================================
    var fsDialog = document.createElement('dialog');
    fsDialog.id = 'hmi-fullscreen-dialog';
    fsDialog.setAttribute('closedby', 'any');
    fsDialog.setAttribute('aria-labelledby', 'hmi-fs-title');

    var optionsHTML = DASHBOARDS.map(function (d) {
        return '<option value="' + prefix + 'dashboards/' + d.slug + '">' + d.title + '</option>';
    }).join('');

    fsDialog.innerHTML = ''
        + '<div class="hmi-fs-toolbar">'
        + '  <div class="hmi-fs-toolbar-left">'
        + '    <h2 id="hmi-fs-title" class="hmi-fs-toolbar-title">VULNOT Fullscreen HMI</h2>'
        + '    <select id="hmi-fs-switcher" class="hmi-fs-select" aria-label="Switch HMI Dashboard">'
        +        optionsHTML
        + '    </select>'
        + '  </div>'
        + '  <div class="hmi-fs-toolbar-actions">'
        + '    <button type="button" id="hmi-fs-native-btn" class="hmi-inline-fs-btn">&#x26F6; Native Fullscreen</button>'
        + '    <a id="hmi-fs-open-tab" href="#" target="_blank" rel="noopener" class="hmi-inline-fs-btn">Open Tab &nearr;</a>'
        + '    <form method="dialog" style="margin:0;">'
        + '      <button type="submit" value="close" class="hmi-inline-fs-btn" style="border-color:rgba(255,107,107,0.5);color:#ff6b6b;" autofocus>&#x2715; Exit Fullscreen (Esc)</button>'
        + '    </form>'
        + '  </div>'
        + '</div>'
        + '<iframe id="hmi-fs-iframe" class="hmi-fs-iframe" title="VULNOT Interactive HMI Dashboard" allowfullscreen></iframe>';

    document.body.appendChild(fsDialog);

    var iframeEl = document.getElementById('hmi-fs-iframe');
    var titleEl = document.getElementById('hmi-fs-title');
    var switcherEl = document.getElementById('hmi-fs-switcher');
    var openTabEl = document.getElementById('hmi-fs-open-tab');
    var nativeBtn = document.getElementById('hmi-fs-native-btn');

    function loadDashboardInModal(url, customTitle, requestNativeFs) {
        var cleanUrl = url.split('?')[0];
        var embedUrl = cleanUrl + '?embed=1';
        iframeEl.src = embedUrl;
        openTabEl.href = cleanUrl;

        // Sync dropdown selection and title
        var matchedTitle = customTitle || 'VULNOT Fullscreen HMI';
        for (var i = 0; i < switcherEl.options.length; i++) {
            if (switcherEl.options[i].value === cleanUrl || cleanUrl.endsWith(switcherEl.options[i].value.replace('../', ''))) {
                switcherEl.selectedIndex = i;
                if (!customTitle) matchedTitle = switcherEl.options[i].text;
                break;
            }
        }
        titleEl.textContent = matchedTitle;

        if (!fsDialog.open) {
            fsDialog.showModal();
        }
        if (requestNativeFs && fsDialog.requestFullscreen && !document.fullscreenElement) {
            fsDialog.requestFullscreen().catch(function () {
                // Gracefully remain in 100vw x 100vh top-layer modal if native fullscreen is blocked
            });
        }
    }

    window.openFullscreenHMI = function (url, title) {
        loadDashboardInModal(url, title, true);
    };

    switcherEl.addEventListener('change', function () {
        var selectedOpt = switcherEl.options[switcherEl.selectedIndex];
        loadDashboardInModal(selectedOpt.value, selectedOpt.text, false);
    });

    nativeBtn.addEventListener('click', function () {
        if (!document.fullscreenElement) {
            fsDialog.requestFullscreen().catch(function () {});
        } else {
            document.exitFullscreen().catch(function () {});
        }
    });

    document.addEventListener('fullscreenchange', function () {
        if (nativeBtn) {
            nativeBtn.innerHTML = document.fullscreenElement ? '&#x2715; Windowed Modal' : '&#x26F6; Native Fullscreen';
        }
    });

    fsDialog.addEventListener('close', function () {
        fsDialog.returnValue = '';
        iframeEl.src = 'about:blank';
        if (document.fullscreenElement) {
            document.exitFullscreen().catch(function () {});
        }
    });

    // Fallback for browsers without declarative <dialog closedby="any"> support
    if (!('closedBy' in HTMLDialogElement.prototype)) {
        var outside = function (e, dialog) {
            var r = dialog.getBoundingClientRect();
            return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
        };
        var pressedOutside = false;
        fsDialog.addEventListener('pointerdown', function (e) {
            pressedOutside = outside(e, fsDialog);
        });
        fsDialog.addEventListener('pointerup', function (e) {
            if (pressedOutside && outside(e, fsDialog)) fsDialog.close();
        });
    }

    // Attach click handler to all [data-fullscreen-hmi] cards on index.html and dashboards.html
    document.querySelectorAll('[data-fullscreen-hmi]').forEach(function (card) {
        card.addEventListener('click', function (e) {
            // Allow Ctrl/Cmd/Middle-click to open in new tab naturally
            if (e.metaKey || e.ctrlKey || e.shiftKey || e.button === 1) return;
            e.preventDefault();
            var targetUrl = card.getAttribute('data-fullscreen-hmi');
            var hmiTitle = card.getAttribute('data-hmi-title') || card.querySelector('h4')?.textContent || 'VULNOT Fullscreen HMI';
            loadDashboardInModal(targetUrl, hmiTitle, true);
        });
    });

    // Inject "HMI ⛶" fullscreen launch button onto every lab card on training.html
    document.querySelectorAll('.lab-card[data-lab-id]').forEach(function (labCard) {
        var labId = labCard.getAttribute('data-lab-id');
        var slug = LAB_TO_DASHBOARD[labId];
        if (!slug) return;
        var actionContainer = labCard.querySelector('.lab-card-footer > div');
        if (!actionContainer) return;

        var hmiBtn = document.createElement('button');
        hmiBtn.type = 'button';
        hmiBtn.className = 'btn-moodle-secondary';
        hmiBtn.style.cssText = 'padding:5px 10px;font-size:11px;border-color:rgba(0,212,255,0.4);color:#00d4ff;';
        hmiBtn.innerHTML = 'HMI &#x26F6;';
        hmiBtn.title = 'Launch Scenario HMI Dashboard in Fullscreen';
        hmiBtn.addEventListener('click', function () {
            var labTitle = labCard.querySelector('h4')?.textContent || labId.toUpperCase();
            loadDashboardInModal(prefix + 'dashboards/' + slug, labTitle + ' — Live HMI', true);
        });
        actionContainer.insertBefore(hmiBtn, actionContainer.firstChild);
    });
})();
