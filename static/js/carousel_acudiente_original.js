(function(){
  const track = document.querySelector('.testimonial-carousel');
  const dots = Array.from(document.querySelectorAll('.testimonial-dots .owl-dot'));
  if(!track) return;
  let cards = Array.from(track.children);
  const originalCount = cards.length;
  // Si menos de 6, duplicar para dar sensación de ciclo largo
  if(originalCount && originalCount < 6){
    const base = cards.slice();
    while(cards.length < 6){
      const clone = base[cards.length % base.length].cloneNode(true);
      clone.classList.add('fill-clone');
      track.appendChild(clone);
      cards.push(clone);
    }
  }
  // Clonar todos para loop infinito
  cards.forEach(card=>{ const clone=card.cloneNode(true); clone.classList.add('loop-clone'); track.appendChild(clone); });
  cards = Array.from(track.children);

  let index=0; let autoplay=true; const INTERVAL=2600; let timer; let animId=0; let isAnimating=false;
  function easeInOut(t){return t<0.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;}
  function setActive(i){ cards.forEach((c,idx)=>c.classList.toggle('active',idx===i)); dots.forEach((d,idx)=>d.classList.toggle('active', idx === (i % dots.length))); }
  function animateTo(target,duration=740,onEnd){ if(animId) cancelAnimationFrame(animId); const start=track.scrollLeft; const change=target-start; const startTime=performance.now(); isAnimating=true; function step(now){ const p=Math.min(1,(now-startTime)/duration); const val=start+change*easeInOut(p); track.scrollLeft=val; if(p<1){ animId=requestAnimationFrame(step); } else { track.scrollLeft=target; isAnimating=false; if(onEnd) onEnd(); } } animId=requestAnimationFrame(step); }
  function scrollToIndex(i){ if(!cards[i]) return; index=i; const card=cards[i]; const center=card.offsetLeft; animateTo(center,740,()=>{ if(index>=originalCount){ index = index % originalCount; track.scrollLeft = cards[index].offsetLeft; } setActive(index); }); setActive(index); }
  function next(){ scrollToIndex(index+1); }
  function startAutoplay(){ clearInterval(timer); timer=setInterval(()=>{ if(!autoplay||isAnimating) return; next(); }, INTERVAL); }
  // Dots navegan primeras "páginas" (modular)
  dots.forEach((dot,i)=>dot.addEventListener('click',()=>{ autoplay=false; clearInterval(timer); scrollToIndex(i); setTimeout(()=>{ autoplay=true; startAutoplay(); },4000); }));
  // Drag básico
  let isDown=false,startX=0,scrollStart=0;
  track.addEventListener('pointerdown',e=>{ if(e.pointerType==='mouse' && e.button!==0) return; isDown=true; autoplay=false; clearInterval(timer); startX=e.clientX; scrollStart=track.scrollLeft; track.classList.add('dragging'); });
  window.addEventListener('pointermove',e=>{ if(!isDown) return; const dx=e.clientX-startX; track.scrollLeft=scrollStart-dx; });
  function pointerUp(){ if(!isDown) return; isDown=false; track.classList.remove('dragging'); autoplay=true; startAutoplay(); }
  window.addEventListener('pointerup',pointerUp); window.addEventListener('pointerleave',pointerUp);
  // Keyboard
  track.setAttribute('tabindex','0'); track.addEventListener('keydown',e=>{ if(e.key==='ArrowRight'){ next(); e.preventDefault(); } else if(e.key==='ArrowLeft'){ scrollToIndex(Math.max(0,index-1)); e.preventDefault(); } });
  setActive(index); startAutoplay();
})();