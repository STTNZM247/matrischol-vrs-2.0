(function(){
  const track = document.querySelector('.testimonial-carousel');
  const dots = Array.from(document.querySelectorAll('.testimonial-dots .owl-dot'));
  if(!track) return;
  let cards = Array.from(track.children);
  const originalCount = cards.length;
  const groupSize = 3; // mostrar en grupos de 3
  // Clonar items para loop infinito hacia adelante
  cards.forEach(card => {
    const clone = card.cloneNode(true);
    clone.classList.add('is-clone');
    track.appendChild(clone);
  });
  cards = Array.from(track.children);
  let index = 0;
  let autoplay = true;
  const INTERVAL = 3000; // tiempo entre desplazamientos automáticos
  let timer; let rafId=0; let isAnimating=false; let didDrag=false;

  function easeInOut(t){return t<0.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;}

  function activeDotForIndex(i){
    if(!dots.length) return 0;
    return Math.floor((i % originalCount)/groupSize) % dots.length;
  }

  function setActive(i){
    cards.forEach((c,idx)=>c.classList.toggle('active', idx===i));
    const dIdx = activeDotForIndex(i);
    dots.forEach((d,idx)=>d.classList.toggle('active', idx===dIdx));
  }

  function animateScroll(to,duration=700,onDone){
    to = Math.round(to);
    if(rafId) cancelAnimationFrame(rafId);
    const start = track.scrollLeft; const change = to - start; const t0 = performance.now(); isAnimating=true;
    function step(now){
      const p=Math.min(1,(now-t0)/duration); const val=start+change*easeInOut(p); track.scrollLeft=val;
      if(p<1){ rafId=requestAnimationFrame(step);} else { track.scrollLeft=to; isAnimating=false; if(onDone) onDone(); }
    }
    rafId=requestAnimationFrame(step);
  }

  function normalize(){
    if(index>=originalCount){ index = index % originalCount; track.scrollLeft = cards[index].offsetLeft; }
  }

  function scrollToIndex(i){ if(!cards[i]) return; index=i; const targetLeft = cards[i].offsetLeft; animateScroll(targetLeft,700,()=>{ normalize(); setActive(index); }); setActive(index); }

  function nextGroup(){ scrollToIndex(index + groupSize); }

  // Dot navegación por grupos
  dots.forEach((dot,i)=>dot.addEventListener('click',e=>{ if(e.button!==0) return; const base = (index < originalCount)?0:originalCount; scrollToIndex(base + i*groupSize); }));

  // Clic tarjeta
  cards.forEach((card,i)=>card.addEventListener('click',e=>{ if(e.button!==0) return; if(didDrag){ didDrag=false; return;} scrollToIndex(i); }));

  // Drag manual
  let isDown=false, startX=0, startScroll=0;
  function down(e){ if(e.pointerType==='mouse' && e.button!==0) return; isDown=true; autoplay=false; clearInterval(timer); startX=e.clientX; startScroll=track.scrollLeft; track.classList.add('dragging'); }
  function move(e){ if(!isDown) return; const dx=e.clientX-startX; track.scrollLeft=startScroll - dx; if(Math.abs(dx)>6) didDrag=true; }
  function up(){ if(!isDown) return; isDown=false; track.classList.remove('dragging'); setTimeout(()=>{ autoplay=true; startAutoplay(); },2000); settleNearest(); }
  track.addEventListener('pointerdown',down); window.addEventListener('pointermove',move); window.addEventListener('pointerup',up); window.addEventListener('pointerleave',up);

  function settleNearest(){ if(isAnimating) return; // encontrar índice cuyo offsetLeft más cercano a scrollLeft
    let closest=index; let min=Infinity; const current=track.scrollLeft; cards.forEach((c,i)=>{ const dist=Math.abs(c.offsetLeft-current); if(dist<min){min=dist; closest=i;} }); index=closest; normalize(); setActive(index); }
  let scrollT; track.addEventListener('scroll',()=>{ if(isAnimating||isDown) return; clearTimeout(scrollT); scrollT=setTimeout(settleNearest,120); });

  function startAutoplay(){ clearInterval(timer); timer=setInterval(()=>{ if(!autoplay||isAnimating||isDown) return; nextGroup(); }, INTERVAL); }

  // teclado
  track.setAttribute('tabindex','0');
  track.addEventListener('keydown',e=>{ if(e.key==='ArrowRight'){ nextGroup(); e.preventDefault(); } else if(e.key==='ArrowLeft'){ scrollToIndex(Math.max(0,index-groupSize)); e.preventDefault(); } });

  setActive(index); startAutoplay();
  // arranque visual para que el usuario perciba movimiento
  setTimeout(()=>{ if(autoplay) nextGroup(); }, 1200);
})();
