const toggle=document.querySelector('.nav-toggle');const links=document.querySelector('.nav-links');if(toggle&&links)toggle.onclick=()=>links.classList.toggle('open');

document.querySelectorAll('[data-share]').forEach(el=>el.onclick=async()=>{const url=el.dataset.share;try{await navigator.share({url});}catch{await navigator.clipboard.writeText(url);toast('Link copied')}});

document.querySelectorAll('[data-wishlist]').forEach(el=>el.onclick=async()=>{const r=await fetch(`/wishlist/toggle/${el.dataset.wishlist}`,{method:'POST',headers:{'X-Requested-With':'XMLHttpRequest'}});if(r.status===401){document.getElementById('login-modal')?.showModal();return;}location.reload();});

const main=document.getElementById('gallery-main');const thumbs=[...document.querySelectorAll('.thumb')];let active=0;
function renderMedia(i){if(!main||!thumbs[i])return;active=i;const t=thumbs[i].dataset.type,s=thumbs[i].dataset.src;main.innerHTML=t==='video'?`<video controls muted playsinline preload="metadata"><source src="${s}"></video><button class='fs-btn'>⤢</button>`:`<img loading='lazy' src='${s}'><button class='fs-btn'>⤢</button>`;main.querySelector('.fs-btn').onclick=()=>main.requestFullscreen?.();}
if(thumbs.length){renderMedia(0);thumbs.forEach((t,i)=>t.onclick=()=>renderMedia(i));let start=0;main?.addEventListener('touchstart',e=>start=e.changedTouches[0].clientX);main?.addEventListener('touchend',e=>{const dx=e.changedTouches[0].clientX-start;if(Math.abs(dx)>35){active=dx<0?Math.min(thumbs.length-1,active+1):Math.max(0,active-1);renderMedia(active);}})}

const s=document.getElementById('live-search'),sug=document.getElementById('search-suggest');if(s&&sug){let t;s.oninput=()=>{clearTimeout(t);t=setTimeout(async()=>{const q=s.value.trim();if(!q){sug.style.display='none';return;}const res=await fetch(`/api/search?q=${encodeURIComponent(q)}`);const data=await res.json();sug.innerHTML=data.length?data.map(i=>`<a href='/product/${i.slug}'><img src='${i.thumb||'/static/media/fallback.webp'}'>${i.title}</a>`).join(''):`<a href='/search?q=${encodeURIComponent(q)}'>No matches. Open search page.</a>`;sug.style.display='block';},180)};s.onkeydown=e=>{if(e.key==='Enter')location.href='/search?q='+encodeURIComponent(s.value)};}

function toast(msg){const wrap=document.querySelector('.toast-stack')||Object.assign(document.body.appendChild(document.createElement('div')),{className:'toast-stack'});const t=document.createElement('div');t.className='toast';t.textContent=msg;wrap.appendChild(t);setTimeout(()=>t.remove(),2200)}
