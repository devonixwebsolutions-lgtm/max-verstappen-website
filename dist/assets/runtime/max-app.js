(() => {
  'use strict';
  let gallery = [], modal, active = 0, angle = 0, timer, previousFocus;
  const $ = (s, root=document) => root.querySelector(s);
  const $$ = (s, root=document) => [...root.querySelectorAll(s)];
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function stopRotation() { clearInterval(timer); timer=null; if (modal) $('[data-viewer-play]',modal).textContent='Play angles'; }
  function updateAngle(index) {
    const helmet=gallery[active]; if (!helmet) return;
    angle=(index+helmet.frames.length)%helmet.frames.length;
    const img=$('[data-viewer-img]',modal); img.src=helmet.frames[angle]; img.alt=`${helmet.name} · view ${angle+1}`;
    $('[data-viewer-counter]',modal).textContent=`${String(angle+1).padStart(2,'0')} / ${String(helmet.frames.length).padStart(2,'0')}`;
    $$('[data-viewer-angle]',modal).forEach((b,i)=>b.setAttribute('aria-pressed',String(i===angle)));
  }
  function ensureModal() {
    if (modal) return;
    modal=document.createElement('dialog'); modal.className='mv-modal'; modal.setAttribute('aria-labelledby','mv-helmet-modal-title');
    modal.innerHTML='<div class="mv-modal-top"><div><span class="mv-modal-eyebrow">Helmets · Hall of Fame</span><h2 id="mv-helmet-modal-title" class="mv-modal-title"></h2></div><button class="mv-close" data-viewer-close aria-label="Close helmet viewer">×</button></div><div class="mv-helmet-viewer"><div class="mv-viewer-image-w"><img class="mv-viewer-image" data-viewer-img alt=""><button class="mv-viewer-button mv-viewer-previous" data-viewer-step="-1" aria-label="Previous angle">←</button><button class="mv-viewer-button mv-viewer-next" data-viewer-step="1" aria-label="Next angle">→</button></div><div class="mv-helmet-viewer-text"><h3 data-viewer-year></h3><p data-viewer-description></p><div class="mv-viewer-controls"><span data-viewer-counter aria-live="polite"></span><button data-viewer-play>Play angles</button></div><div class="mv-viewer-thumbs" data-viewer-thumbs></div><a class="mv-plain-link" data-viewer-source target="_blank" rel="noopener noreferrer">View the official collection ↗</a></div></div>';
    document.body.append(modal);
    modal.addEventListener('close',()=>{stopRotation(); document.body.classList.remove('mv-viewer-open'); window.lenis?.start?.(); previousFocus?.focus?.();});
    modal.addEventListener('click',event=>{if(event.target===modal){const r=modal.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)modal.close();}});
    let startX=0;const image=$('.mv-viewer-image-w',modal);
    image.addEventListener('pointerdown',e=>startX=e.clientX);
    image.addEventListener('pointerup',e=>{const delta=e.clientX-startX;if(Math.abs(delta)>35){stopRotation();updateAngle(angle+(delta<0?1:-1));}});
  }
  function showHelmet(index,trigger) {
    loadGallery(); if(!gallery[index]) return;
    ensureModal(); stopRotation(); active=index;angle=0;previousFocus=trigger;
    const h=gallery[index];$('#mv-helmet-modal-title',modal).textContent=h.name.replace(/Max Verstappen/gi,'').trim();
    $('[data-viewer-year]',modal).textContent=h.year;
    $('[data-viewer-description]',modal).textContent=h.replicaPhotography ? 'Official scale-replica photography of Max’s helmet design. Explore the design and its official collection.' : 'An original Max Verstappen design, documented in his official photo archive. Use the arrows, thumbnails or swipe to explore the published angles.';
    $('[data-viewer-source]',modal).href=h.source;
    $('[data-viewer-thumbs]',modal).innerHTML=h.frames.map((src,i)=>`<button data-viewer-angle="${i}" aria-label="View angle ${i+1}" aria-pressed="false"><img src="${esc(src)}" alt="" loading="lazy"></button>`).join('');
    $('[data-viewer-play]',modal).hidden=h.frames.length<2;
    $$('[data-viewer-step]',modal).forEach(b=>b.hidden=h.frames.length<2);
    updateAngle(0);modal.showModal();document.body.classList.add('mv-viewer-open');window.lenis?.stop?.();
  }
  function loadGallery() {
    const data=$('#max-gallery-data');if(data)try{gallery=JSON.parse(data.textContent);}catch{}
  }
  function filterHelmets(value) {
    const cards=$$('[data-helmet-grid] > .helmet-grid-item-w');
    cards.forEach(card=>{const i=Number($('[data-max-helmet]',card)?.dataset.maxHelmet);card.hidden=value!=='all'&&String(gallery[i]?.year)!==value;});
    window.dispatchEvent(new Event('resize'));
  }
  function filterWins(value) {
    let count=0;$$('[data-win-year]').forEach(row=>{row.hidden=value!=='all'&&row.dataset.winYear!==value;if(!row.hidden)count++;});
    const label=$('[data-wins-count]');if(label)label.textContent=`${count} ${count===1?'win':'wins'}`;
    window.dispatchEvent(new Event('resize'));
  }
  const sessionDate = s => {
    // Source schedules use Central European local time; convert with the year's DST rules.
    const [day,mon,year]=s.date.split(' '), month=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].indexOf(mon);
    let instant=new Date(Date.UTC(+year,month,+day,...s.time.split(':').map(Number)));
    const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Amsterdam',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(instant);
    const hour=+parts.find(p=>p.type==='hour').value, offset=(hour-instant.getUTCHours()+24)%24;
    instant=new Date(instant.getTime()-offset*3600000);
    return {date:new Intl.DateTimeFormat('en-GB',{timeZone:'UTC',day:'2-digit',month:'short'}).format(instant),time:new Intl.DateTimeFormat('en-GB',{timeZone:'UTC',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(instant)};
  };
  function showSessions(row) {
    let sessions;try{sessions=JSON.parse(row.dataset.maxSessions);}catch{return;}
    const wrap=row.closest('.s');if(!wrap)return;
    let panel=$('.mv-session-panel',wrap);if(!panel){panel=document.createElement('div');panel.className='mv-session-panel';panel.setAttribute('aria-live','polite');const list=row.closest('[data-stat-list]');(list||row.parentElement).insertAdjacentElement('afterend',panel);}
    panel.innerHTML=`<h3>${esc(row.dataset.maxEventName)}</h3><div class="mv-session-grid">${sessions.map(s=>{const d=sessionDate(s);return `<div><strong>${esc(s.name.replace('Sprintrace','Sprint'))}</strong><span>${d.date}</span><span>${d.time} UTC</span></div>`;}).join('')}</div><p class="mv-data-note">Official Verstappen.com schedule · UTC · <a href="https://news.verstappen.com/en/calendar" target="_blank" rel="noopener">View source ↗</a></p>`;
    $$('[data-max-round]',wrap).forEach(r=>r.setAttribute('aria-pressed',String(r===row)));
    const viewer=$('[data-cal-track-wrap]');
    if(viewer){
      let map=$('.mv-circuit-map',viewer);
      if(row.dataset.maxTrackMap){
        if(!map){map=document.createElement('div');map.className='mv-circuit-map';const scene=$('[data-gl="tracks"]',viewer);(scene||viewer).append(map);}
        map.innerHTML=`<img src="${esc(row.dataset.maxTrackMap)}" alt="Sepang International Circuit layout">`;map.hidden=false;
      }else if(map)map.hidden=true;
    }
  }
  document.addEventListener('click',event=>{
    const target=event.target instanceof Element?event.target:null;if(!target)return;
    const helmet=target.closest('[data-max-helmet]');if(helmet){event.preventDefault();showHelmet(Number(helmet.dataset.maxHelmet),helmet);return;}
    if(target.closest('[data-viewer-close]')){modal?.close();return;}
    const step=target.closest('[data-viewer-step]');if(step){stopRotation();updateAngle(angle+Number(step.dataset.viewerStep));return;}
    const thumb=target.closest('[data-viewer-angle]');if(thumb){stopRotation();updateAngle(Number(thumb.dataset.viewerAngle));return;}
    if(target.closest('[data-viewer-play]')){if(timer)stopRotation();else{target.textContent='Pause';timer=setInterval(()=>updateAngle(angle+1),1000);}return;}
    const row=target.closest('[data-max-round]');if(row)showSessions(row);
  });
  document.addEventListener('change',event=>{const t=event.target;if(t.matches('[data-helmet-filter]'))filterHelmets(t.value);if(t.matches('[data-wins-filter]'))filterWins(t.value);});
  document.addEventListener('keydown',event=>{
    if(modal?.open){if(event.key==='ArrowRight'){event.preventDefault();stopRotation();updateAngle(angle+1);}if(event.key==='ArrowLeft'){event.preventDefault();stopRotation();updateAngle(angle-1);}return;}
    if((event.key==='Enter'||event.key===' ')&&event.target.matches('[data-max-helmet],[data-max-round]')){event.preventDefault();event.target.click();}
  });
  document.addEventListener('pointermove',event=>{
    if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
    const hero=$('.mv-hero-portrait');if(hero){hero.style.setProperty('--mv-pointer-x',String((event.clientX/innerWidth-.5)*18));hero.style.setProperty('--mv-pointer-y',String((event.clientY/innerHeight-.5)*9));}
  },{passive:true});
  function init(){loadGallery();const current=$('[data-max-round="17"]');if(current)showSessions(current);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
  window.addEventListener('page-transition-end',()=>{modal?.close();init();});
})();
