// Calcula el brillo de un color y ajusta variables CSS para contraste
(function(){
    function parseColor(s){
        if(!s) return null;
        s = s.trim();
        // hex
        if(s[0] === '#'){
            let hex = s.slice(1);
            if(hex.length === 3) hex = hex.split('').map(c=>c+c).join('');
            const r = parseInt(hex.slice(0,2),16);
            const g = parseInt(hex.slice(2,4),16);
            const b = parseInt(hex.slice(4,6),16);
            return [r,g,b];
        }
        // rgb(...) or rgba(...)
        const m = s.match(/rgba?\(([^)]+)\)/);
        if(m){
            const parts = m[1].split(',').map(p=>p.trim());
            return [parseInt(parts[0],10)||0, parseInt(parts[1],10)||0, parseInt(parts[2],10)||0];
        }
        return null;
    }
    function luminance(r,g,b){
        // r,g,b in 0..255
        const srgb = [r,g,b].map(v=>v/255);
        const lin = srgb.map(c => c <= 0.03928 ? c/12.92 : Math.pow((c+0.055)/1.055,2.4));
        return 0.2126*lin[0] + 0.7152*lin[1] + 0.0722*lin[2];
    }
    function toRGBA(hexOrRgb, alpha){
        const rgb = parseColor(hexOrRgb) || [0,0,0];
        return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${alpha})`;
    }

    function applyContrast(){
        const root = getComputedStyle(document.documentElement);
        let bg = root.getPropertyValue('--bg') || '';
        bg = bg.trim();
        if(!bg){
            // try body background
            bg = getComputedStyle(document.body).backgroundColor || '#ffffff';
        }
        const rgb = parseColor(bg) || [255,255,255];
        const lum = luminance(rgb[0], rgb[1], rgb[2]);
        // threshold 0.5 (can be tuned)
        const contrastColor = lum > 0.5 ? '#000000' : '#ffffff';
        // muted color (60% opacity)
        const muted = toRGBA(contrastColor, 0.6);
        document.documentElement.style.setProperty('--text', contrastColor);
        document.documentElement.style.setProperty('--muted', muted);
        // also set button-text variable for buttons/icons
        document.documentElement.style.setProperty('--button-text', contrastColor);
        // for elements that should invert (if needed) expose inverse
        document.documentElement.style.setProperty('--text-inverse', lum > 0.5 ? '#ffffff' : '#000000');
    }

    if(document.readyState === 'loading'){
        document.addEventListener('DOMContentLoaded', applyContrast);
    } else {
        applyContrast();
    }

    // Observe changes to inline styles or theme toggles that modify --bg
    const obs = new MutationObserver(muts=>{
        applyContrast();
    });
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['style', 'class'] });
})();
