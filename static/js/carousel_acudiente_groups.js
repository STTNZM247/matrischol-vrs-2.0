(function(){
  const track = document.querySelector('.testimonial-carousel');
  const viewport = document.querySelector('.testimonial-viewport');
  const dots = Array.from(document.querySelectorAll('.testimonial-dots .owl-dot'));
  if(!track || !viewport) return;
  let items = Array.from(track.children);
  const pageSize = 3;
  const LOG_PREFIX='[Carrusel]';
  console.log(LOG_PREFIX,'Inicializando. Items originales:', items.length);
  if(items.length === 0) return;

  // Garantizar 6 items visibles en total (2 páginas de 3)
  if(items.length < 6){
    const base = items.slice();
    while(items.length < 6){
      const clone = base[items.length % base.length].cloneNode(true);
      clone.classList.add('fill');
      track.appendChild(clone);
      items.push(clone);
    }
    console.log(LOG_PREFIX,'Duplicados añadidos hasta 6. Total ahora:', items.length);
  }

  // Clonar primera página al final para bucle suave
  const firstGroup = items.slice(0,pageSize).map(el=>{
    const c = el.cloneNode(true); c.classList.add('loop'); track.appendChild(c); return c;
  });
  items = Array.from(track.children);
  console.log(LOG_PREFIX,'Clon grupo inicial. Total items con clones:', items.length);

  function computePageWidth(){
    const style = getComputedStyle(track);
    // gap puede no estar soportado como property en algunos navegadores antiguos; fallback a 0
    const gap = parseFloat(style.columnGap || style.gap) || 0;
    const sample = items.slice(0,pageSize);
    let w=0; sample.forEach(it=>{ w += it.getBoundingClientRect().width; });
    w += gap*(pageSize-1);
    return w;
  }
  let pageWidth = computePageWidth();
  console.log(LOG_PREFIX,'Ancho página calculado:', pageWidth);
  // Recalcular después de load (por si fuentes / imágenes ajustan)
  window.addEventListener('load',()=>{ pageWidth = computePageWidth(); console.log(LOG_PREFIX,'Ancho página tras load:', pageWidth); });
  window.addEventListener('resize',()=>{ pageWidth = computePageWidth(); console.log(LOG_PREFIX,'Ancho página tras resize:', pageWidth); });

  let pageIndex = 0; // 0,1,2 (2 es clon de 0)
  const TOTAL_PAGES = 3; // 0,1 reales + 2 clon
  const INTERVAL = 3200;
  let timer; let animating=false;

  function setActiveDot(logicalIdx){
    if(dots.length===0) return;
    const mapped = logicalIdx % dots.length;
    dots.forEach((d,i)=> d.classList.toggle('active', i===mapped));
  }

  function goTo(idx){
    if(animating) return;
    animating=true;
    pageIndex = idx;
    const target = pageWidth*idx;
    track.style.transform = `translateX(-${target}px)`;
    setActiveDot(idx);
    console.log(LOG_PREFIX,'Ir a página', idx,'transform', target);
  }

  track.addEventListener('transitionend',()=>{
    animating=false;
    if(pageIndex === TOTAL_PAGES-1){
      // Reset instantáneo a 0
      track.style.transition='none';
      pageIndex = 0;
      track.style.transform='translateX(0)';
      setActiveDot(0);
      console.log(LOG_PREFIX,'Reset loop a página 0');
      // Rehabilitar transición siguiente frame
      requestAnimationFrame(()=>{ track.style.transition='transform .75s cubic-bezier(.22,.61,.36,1)'; });
    }
  });

  function next(){
    if(animating) return;
    const nxt = pageIndex+1 >= TOTAL_PAGES ? TOTAL_PAGES-1 : pageIndex+1;
    goTo(nxt);
  }
  function start(){ clearInterval(timer); timer=setInterval(next, INTERVAL); }

  dots.forEach((dot,i)=> dot.addEventListener('click',()=>{ clearInterval(timer); goTo(i); start(); }));

  // Drag soporte básico
  let isDown=false,startX=0,startPos=0;
  track.addEventListener('pointerdown',e=>{
    if(e.pointerType==='mouse' && e.button!==0) return;
    isDown=true; startX=e.clientX;
    // parse transform actual
    const m = /translateX\(-?(\d+(?:\.\d+)?)px\)/.exec(track.style.transform);
    startPos = m? parseFloat(m[1]): pageWidth*pageIndex;
    track.classList.add('dragging');
    clearInterval(timer);
  });
  window.addEventListener('pointermove',e=>{
    if(!isDown) return;
    const dx = e.clientX - startX;
    const pos = Math.max(0, startPos - dx); // límite izquierdo
    track.style.transform = `translateX(-${pos}px)`;
  });
  function endDrag(){
    if(!isDown) return;
    isDown=false; track.classList.remove('dragging');
    // decidir página más cercana
    const m = /translateX\(-?(\d+(?:\.\d+)?)px\)/.exec(track.style.transform);
    const pos = m? parseFloat(m[1]): pageWidth*pageIndex;
    const approx = Math.round(pos / pageWidth);
    goTo(Math.min(approx, TOTAL_PAGES-1));
    start();
  }
  window.addEventListener('pointerup', endDrag);
  window.addEventListener('pointerleave', endDrag);

  // Inicializar
  setActiveDot(0);
  // asegurar transición definida
  if(!track.style.transition){ track.style.transition='transform .75s cubic-bezier(.22,.61,.36,1)'; }
  goTo(0); start();
})();