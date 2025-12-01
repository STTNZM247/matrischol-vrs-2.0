(function(){
  const track = document.querySelector('.testimonial-carousel');
  if(!track) return;
  const cards = Array.from(track.children);
  const dots = Array.from(document.querySelectorAll('.testimonial-dots .owl-dot'));
  const navPrev = document.querySelector('.testimonial-nav .nav-btn[data-dir="prev"]');
  const navNext = document.querySelector('.testimonial-nav .nav-btn[data-dir="next"]');
  if(cards.length === 0) return;

  // Asegurar overflow si pocas tarjetas
  if(track.scrollWidth <= track.clientWidth){
    let copies = 0; while(track.scrollWidth <= track.clientWidth && copies < cards.length){
      const clone = cards[copies].cloneNode(true); clone.classList.add('clone'); track.appendChild(clone); copies++;
    }
  }
  const allCards = Array.from(track.children);
  let index = 0;
  const INTERVAL = 3000;
  let timer;

  function setActive(i){ allCards.forEach((c,idx)=> c.classList.toggle('active', idx===i)); dots.forEach((d,idx)=> d.classList.toggle('active', idx === (i % dots.length))); }
  function scrollTo(i){ if(!allCards[i]) return; const target = allCards[i]; const left = target.offsetLeft; track.scrollTo({left, behavior:'smooth'}); index = i; setActive(index); }
  function next(){ let nextIndex = index + 1; if(nextIndex >= allCards.length) nextIndex = 0; scrollTo(nextIndex); }
  function prev(){ let prevIndex = index - 1; if(prevIndex < 0) prevIndex = allCards.length - 1; scrollTo(prevIndex); }
  function start(){ stop(); timer = setInterval(next, INTERVAL); }
  function stop(){ if(timer) clearInterval(timer); }

  // Dots
  dots.forEach((d,i)=> d.addEventListener('click',()=>{ stop(); scrollTo(i); start(); }));
  // Nav buttons
  if(navPrev) navPrev.addEventListener('click',()=>{ stop(); prev(); start(); });
  if(navNext) navNext.addEventListener('click',()=>{ stop(); next(); start(); });
  // Pointer drag (básico)
  let isDown=false, startX=0, scrollStart=0;
  track.addEventListener('pointerdown',e=>{ if(e.button!==0 && e.pointerType==='mouse') return; isDown=true; startX=e.clientX; scrollStart=track.scrollLeft; stop(); track.classList.add('dragging'); });
  window.addEventListener('pointermove',e=>{ if(!isDown) return; const dx=e.clientX-startX; track.scrollLeft=scrollStart-dx; });
  function pointerUp(){ if(!isDown) return; isDown=false; track.classList.remove('dragging'); start(); }
  window.addEventListener('pointerup',pointerUp); window.addEventListener('pointerleave',pointerUp);
  // Keyboard
  track.setAttribute('tabindex','0');
  track.addEventListener('keydown',e=>{ if(e.key==='ArrowRight'){ stop(); next(); start(); } else if(e.key==='ArrowLeft'){ stop(); prev(); start(); } });

  setActive(index); start();
})();
