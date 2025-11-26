// Archivo JS de ejemplo
document.addEventListener('DOMContentLoaded', function () {
  console.log('Matrischol frontend ready');
});


document.addEventListener('DOMContentLoaded', function() {
    const navBtns = document.querySelectorAll('.bottom-nav .nav-btn');

    if (!navBtns.length) return;

    // comparar la URL completa (sin hash ni query) para evitar activar múltiples botones
    const normalize = u => u.split('#')[0].split('?')[0].replace(/\/+$/, '');
    const currentHref = normalize(window.location.href);

    navBtns.forEach(btn => {
        const href = btn.getAttribute('href') || '';
        const link = new URL(href, window.location.href);
        const linkHref = normalize(link.href);

        if (linkHref === currentHref) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }

        // mantener comportamiento visual inmediato al hacer click
        btn.addEventListener('click', function() {
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
});

// Función pública para cambiar el color del logo.
// Uso:
//   setLogoColor('blue')     -> aplica clase .logo-filter-blue
//   setLogoColor('green')    -> aplica clase .logo-filter-green
//   setLogoColor('red')      -> aplica clase .logo-filter-red
//   setLogoColor('none')     -> restaura el filtro por defecto
window.setLogoColor = function(name) {
    const logo = document.querySelector('.site-logo');
    if (!logo) return;

    // remover clases conocidas
    logo.classList.remove('logo-filter-blue','logo-filter-green','logo-filter-red','logo-filter-yellow','logo-filter-white','logo-filter-dark','logo-filter-default');

    if (!name || name === 'none' || name === 'default') {
        logo.classList.add('logo-filter-default');
        logo.style.removeProperty('--logo-filter');
        return;
    }

    const cls = `logo-filter-${name}`;
    // si existe la clase en CSS, aplícala; en caso contrario, intenta usar 'name' como valor de filtro CSS
    logo.classList.add(cls);
};

/* Theme picker: construir UI, aplicar temas y persistir elección en localStorage */
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const themePicker = document.getElementById('theme-picker');
    if (!themeToggle || !themePicker) return;

    const THEMES = [
        { id: 'default', name: 'Default', color: '#ffffff' },
        { id: 'amarillo', name: 'Amarillo', color: '#fffbe6' },
        { id: 'azul', name: 'Azul', color: '#f0f8ff' },
        { id: 'oscuro', name: 'Oscuro', color: '#0b1220' }
    ];

    // util: hex -> {r,g,b}
    function hexToRgb(hex) {
        hex = String(hex).replace('#','');
        if (hex.length === 3) hex = hex.split('').map(h=>h+h).join('');
        const int = parseInt(hex, 16);
        return { r: (int >> 16) & 255, g: (int >> 8) & 255, b: int & 255 };
    }
    // util: luminance 0..1
    function luminance(rgb) {
        const srgb = ['r','g','b'].map(k => {
            const v = rgb[k] / 255;
            return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * srgb[0] + 0.7152 * srgb[1] + 0.0722 * srgb[2];
    }
    function contrastColor(hex) {
        try {
            const lum = luminance(hexToRgb(hex));
            return lum > 0.55 ? '#000000' : '#ffffff';
        } catch (e) { return '#000000'; }
    }
    function rgbaFromHex(hex, a) {
        const {r,g,b} = hexToRgb(hex);
        return `rgba(${r}, ${g}, ${b}, ${a})`;
    }
    function mix(hex1, hex2, weight) {
        const a = hexToRgb(hex1); const b = hexToRgb(hex2);
        const r = Math.round(a.r * (1-weight) + b.r * weight);
        const g = Math.round(a.g * (1-weight) + b.g * weight);
        const bl = Math.round(a.b * (1-weight) + b.b * weight);
        return '#' + ((1 << 24) + (r << 16) + (g << 8) + bl).toString(16).slice(1);
    }

    // invertir color (simple complementario), suavizado para no quedar demasiado agresivo
    function invertColor(hex) {
        try {
            const rgb = hexToRgb(hex);
            const ir = 255 - rgb.r;
            const ig = 255 - rgb.g;
            const ib = 255 - rgb.b;
            const inv = '#' + ((1 << 24) + (ir << 16) + (ig << 8) + ib).toString(16).slice(1);
            // mezclar ligeramente con blanco para que no quede tan fuerte
            return mix(inv, '#ffffff', 0.08);
        } catch (e) {
            return '#000000';
        }
    }

    function applyPrimaryColor(hex) {
        const root = document.documentElement;
        root.style.setProperty('--bg', hex);
        const text = contrastColor(hex);
        root.style.setProperty('--text', text);
        // logo use same as text for legibility
        root.style.setProperty('--logo-color', text);
        // primary color (keeps original chosen color available)
        root.style.setProperty('--primary', hex);
        // Button variables: pick a tint derived from primary, but if primary is
        // pure white or very light then use a dark button so it remains visible.
        let btnBg;
        try {
            const rgb = hexToRgb(hex);
            const lum = luminance(rgb);
            // If the chosen color is (almost) pure white or very light, use a dark button
            if ((rgb.r === 255 && rgb.g === 255 && rgb.b === 255) || lum > 0.95) {
                btnBg = '#2f2f2f';
            } else {
                // light tint for normal primaries
                btnBg = mix(hex, '#ffffff', 0.72);
            }
        } catch (e) {
            btnBg = mix(hex, '#ffffff', 0.72);
        }
        root.style.setProperty('--btn-bg', btnBg);
        const btnText = contrastColor(btnBg);
        root.style.setProperty('--btn-text', btnText);
        const btnBorder = rgbaFromHex(hex, 0.14);
        root.style.setProperty('--btn-border', btnBorder);
        // section background: slight mix with white for separation
        const sectionBg = mix(hex, '#ffffff', 0.06);
        root.style.setProperty('--section-bg', sectionBg);
        // muted: color secundario más claro derivado del primario
        const muted = mix(hex, '#ffffff', 0.6);
        root.style.setProperty('--muted', muted);
        // nav background: translucent version of chosen color
        const navBg = rgbaFromHex(hex, 0.12);
        root.style.setProperty('--nav-bg', navBg);
        // nav text should contrast with nav background; prefer text computed earlier
        root.style.setProperty('--nav-text', text);
        // inputs and form accents: small tint and subtle border derived from primary
        const inputBg = mix(hex, '#ffffff', 0.92);
        const inputBorder = rgbaFromHex(hex, 0.16);
        root.style.setProperty('--input-bg', inputBg);
        root.style.setProperty('--input-border', inputBorder);
        // placeholder: elegir negro o blanco según contraste con el fondo del input
        const placeholderColor = contrastColor(inputBg);
        root.style.setProperty('--placeholder-color', placeholderColor);
        try { localStorage.setItem('site-primary', hex); } catch (e) {}
        // Ajustar clase para indicar fondo oscuro/clar o (se usa en CSS para logos raster)
        try {
            const lum = luminance(hexToRgb(hex));
            if (lum < 0.5) document.documentElement.classList.add('theme-dark-bg'); else document.documentElement.classList.remove('theme-dark-bg');
        } catch (e) {}
    }

    function buildSwatches() {
        themePicker.innerHTML = '';

        // ensure we have styles for the circular color input across browsers
        (function insertThemeInputStyles() {
            if (document.getElementById('theme-picker-input-styles')) return;
            const css = `
            .theme-color-input { background-color: #ffffff !important; }
            .theme-color-input::-webkit-color-swatch-wrapper { padding: 0; border-radius: 50%; }
            .theme-color-input::-webkit-color-swatch { border-radius: 50%; background: #ffffff !important; box-shadow: inset 0 0 0 2px #000000; }
            .theme-color-input::-moz-color-swatch { border-radius: 50%; background: #ffffff !important; box-shadow: inset 0 0 0 2px #000000; }
            `;
            const s = document.createElement('style'); s.id = 'theme-picker-input-styles'; s.textContent = css;
            document.head.appendChild(s);
        })();

        // add predefined swatches
        THEMES.forEach(t => {
            const s = document.createElement('button');
            s.type = 'button'; s.className = 'theme-swatch'; s.title = t.name;
            s.dataset.id = t.id; s.style.background = t.color;
            s.addEventListener('click', () => {
                const daltonicOn = localStorage.getItem('site-daltonic') === 'true';
                if (daltonicOn) {
                    // guardar original y aplicar versión invertida
                    localStorage.setItem('site-primary-original', t.color);
                    const d = invertColor(t.color);
                    localStorage.setItem('site-primary-dalt', d);
                    applyPrimaryColor(d);
                } else {
                    applyPrimaryColor(t.color);
                }
                themePicker.classList.add('hidden'); themePicker.setAttribute('aria-hidden','true');
                try { themeToggle.classList.remove('open'); } catch (e) {}
            });
            themePicker.appendChild(s);
        });

        // swatch circular para activar/desactivar la inversión (modo daltónico)
        const invertSwatch = document.createElement('button');
        invertSwatch.type = 'button';
        invertSwatch.className = 'theme-swatch theme-invert-swatch';
        invertSwatch.title = 'Invertir (daltónico)';
        // pequeño icono interno (dos flechas circulares) para indicar inversión
        // SVG: semicírculo blanco / semicírculo negro (lado a la izquierda blanco)
        invertSwatch.innerHTML = '' +
            '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">' +
            '<circle cx="12" cy="12" r="10" fill="#000" />' +
            '<path d="M12 2 A10 10 0 0 0 12 22 L12 2 Z" fill="#fff"/>' +
            '</svg>';

        function setDaltonicState(on) {
            if (on) invertSwatch.classList.add('selected'); else invertSwatch.classList.remove('selected');
        }

        invertSwatch.addEventListener('click', () => {
            const currentPrimary = localStorage.getItem('site-primary') || '#ffffff';
            const isOn = localStorage.getItem('site-daltonic') === 'true';
            if (!isOn) {
                const original = localStorage.getItem('site-primary') || currentPrimary;
                const d = invertColor(original);
                localStorage.setItem('site-primary-original', original);
                localStorage.setItem('site-primary-dalt', d);
                localStorage.setItem('site-daltonic', 'true');
                applyPrimaryColor(d);
                setDaltonicState(true);
            } else {
                const orig = localStorage.getItem('site-primary-original') || '#ffffff';
                localStorage.setItem('site-daltonic', 'false');
                applyPrimaryColor(orig);
                setDaltonicState(false);
            }
        });

        // añadir la swatch de inversión justo después de las paletas
        themePicker.appendChild(invertSwatch);

        // color picker input (libre)
        const pickerWrapper = document.createElement('div');
        pickerWrapper.className = 'theme-picker-footer';
        pickerWrapper.style.display = 'flex';
        pickerWrapper.style.gap = '8px';
        pickerWrapper.style.alignItems = 'center';

        const colorInput = document.createElement('input');
        colorInput.type = 'color';
        colorInput.className = 'theme-color-input';
        colorInput.value = localStorage.getItem('site-primary') || '#ffffff';
        colorInput.title = 'Elegir color de fondo';
        colorInput.setAttribute('aria-label', 'Selector de color');
        // estilos inline para que se vea como una papeleta circular
        // estilos visuales movidos a CSS (.theme-color-input)
        colorInput.addEventListener('input', (e) => {
            const chosen = e.target.value;
            const daltonicOn = localStorage.getItem('site-daltonic') === 'true';
            if (daltonicOn) {
                // cuando está activo, actualizamos el 'original' y aplicamos la versión invertida
                localStorage.setItem('site-primary-original', chosen);
                const d = invertColor(chosen);
                localStorage.setItem('site-primary-dalt', d);
                applyPrimaryColor(d);
            } else {
                applyPrimaryColor(chosen);
            }
        });

        const resetBtn = document.createElement('button');
        resetBtn.type = 'button'; resetBtn.className = 'theme-reset-btn'; resetBtn.textContent = 'Restaurar'; resetBtn.title = 'Restaurar defecto';
        resetBtn.setAttribute('aria-label', 'Restaurar tema');
        // estilos visuales movidos a CSS (.theme-reset-btn)
        resetBtn.addEventListener('click', () => {
            // restaurar y limpiar modo daltónico si existía
            applyPrimaryColor('#ffffff');
            colorInput.value = '#ffffff';
            localStorage.removeItem('site-primary-original');
            localStorage.removeItem('site-primary-dalt');
            localStorage.setItem('site-daltonic', 'false');
        });

        pickerWrapper.appendChild(colorInput);
        pickerWrapper.appendChild(resetBtn);
        themePicker.appendChild(pickerWrapper);
        // si existe flag daltónico activado, marcar la swatch de inversión
        try {
            const dal = localStorage.getItem('site-daltonic') === 'true';
            if (dal && typeof invertSwatch !== 'undefined') invertSwatch.classList.add('selected');
        } catch (e) {}
    }

    // alternar vista del panel
    themeToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        themePicker.classList.toggle('hidden');
        const hidden = themePicker.classList.contains('hidden');
        themePicker.setAttribute('aria-hidden', hidden ? 'true' : 'false');
        // añadir/quitar clase visual 'open' en el toggle para animaciones
        if (!hidden) themeToggle.classList.add('open'); else themeToggle.classList.remove('open');
    });

    // cerrar al hacer click fuera
    document.addEventListener('click', function(e) {
        if (!themePicker.classList.contains('hidden') && !themePicker.contains(e.target) && e.target !== themeToggle) {
            themePicker.classList.add('hidden');
            themePicker.setAttribute('aria-hidden', 'true');
            // asegurar que el toggle pierde estado abierto
            themeToggle.classList.remove('open');
        }
    });

    buildSwatches();
    // aplicar color guardado
    try {
        const saved = localStorage.getItem('site-primary');
        if (saved) applyPrimaryColor(saved);
    } catch (e) {}

    // animación incentivadora: pulso único para invitar a personalizar (se quita al terminar)
    try {
        // asegurar que no haya clase previa
        themeToggle.classList.remove('pulse');
        // forzar reflow para garantizar que la animación pueda reiniciarse
        void themeToggle.offsetWidth;
        themeToggle.classList.add('pulse');
        const removePulse = () => { themeToggle.classList.remove('pulse'); themeToggle.removeEventListener('animationend', removePulse); };
        themeToggle.addEventListener('animationend', removePulse);
    } catch (e) {}
});

// Cambia el color del logo usando cualquier valor CSS (hex, rgb, nombre)
window.setLogoHex = function(hex) {
    const logo = document.querySelector('.site-logo');
    if (!logo) return;
    logo.style.color = hex;
};

// Auto-dismiss welcome overlay if present: wait for popin (0.9s) then fade and remove
document.addEventListener('DOMContentLoaded', function() {
    try {
        const overlay = document.querySelector('.welcome-overlay');
        if (!overlay) return;
        // dejar que la animación 'popin' (0.9s) corra, luego ocultar el overlay suavemente
        const waitMs = 950; // ligeramente mayor que 900ms
        setTimeout(() => {
            overlay.classList.add('hidden');
            // remover del DOM después de la transición
            setTimeout(() => { try { overlay.remove(); } catch (e) {} }, 320);
        }, waitMs);
    } catch (e) {}
});

// attach handlers to form-close buttons to hide auth forms
document.addEventListener('DOMContentLoaded', function() {
    try {
        const closes = document.querySelectorAll('.form-close');
        closes.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetCard = btn.closest('.login-card') || btn.closest('.auth-container');
                if (targetCard) targetCard.classList.add('hidden');
            });
        });
    } catch (e) {}
});

// Debug: muestra atributos y estilos computados de los elementos SVG
window.debugLogo = function(limit = 200) {
    const svg = document.querySelector('.site-logo svg');
    if (!svg) { console.log('No se encontró SVG dentro de .site-logo'); return; }
    const nodes = Array.from(svg.querySelectorAll('*'));
    console.log('SVG root element:', svg);
    nodes.slice(0, limit).forEach((el, i) => {
        const cs = window.getComputedStyle(el);
        console.log(i, el.tagName, {
            attrFill: el.getAttribute('fill'),
            attrStroke: el.getAttribute('stroke'),
            computedFill: cs.fill,
            computedStroke: cs.stroke
        });
    });
    if (nodes.length > limit) console.log('... (rest omitted) total nodes =', nodes.length);
};

// Forzar temporalmente un color sobre el SVG para probar (se elimina tras `durationMs` ms si se pasa)
window.forceLogoColor = function(color = 'lime', durationMs) {
    let style = document.getElementById('debug-svg');
    if (!style) {
        style = document.createElement('style');
        style.id = 'debug-svg';
        document.head.appendChild(style);
    }
    style.textContent = `.site-logo svg, .site-logo svg * { fill: ${color} !important; stroke: ${color} !important; }`;
    if (durationMs && typeof durationMs === 'number') {
        setTimeout(() => { style.remove(); }, durationMs);
    }
};