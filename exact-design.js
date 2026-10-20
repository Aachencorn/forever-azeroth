/* Book-only artwork. Home and shared exterior are independently rendered in tavern-home.js. */
const approvedPages={adventurers:'adventurers',guilds:'guilds',world:'world',news:'news',events:'news',chronicle:'chronicle',favorites:'favorites',live:'live'};
const approvedLayout=layout;
const classSeals={'전사':['⚔','#a48960'],'성기사':['✦','#d97ac0'],'사냥꾼':['➶','#80aa46'],'도적':['➶','#c5aa29'],'사제':['✧','#ece2b2'],'주술사':['ϟ','#368ace'],'마법사':['ϟ','#5aaed4'],'흑마법사':['ϟ','#9c59c5'],'드루이드':['☀','#d98b31']};
layout=function(body){approvedLayout(body);applyApprovedArtwork()};
function applyApprovedArtwork(){
 const page=document.querySelector('main'),key=page?.className.match(/page-(\w+)/)?.[1],asset=approvedPages[key];
 document.body.classList.toggle('approvedDesign',Boolean(asset));
 document.body.classList.add('tavernDesign');
 document.body.classList.toggle('tavernHomeView',key==='home');
 applyUnifiedHeader();
 if(!asset)return;
 const root=document.getElementById('app');root.style.setProperty('--approved',`url('${new URL('assets/approved/'+asset+'.webp',document.baseURI).href}')`);root.dataset.reference=asset;
 // Only the scenery/title band changes. Every route shares the complete blank book.
 const crop=asset==='home'?[80,145,1395,173]:asset==='favorites'?[80,120,1395,143]:asset==='live'?[80,120,1395,129]:[80,145,1395,156];
 const mobileScene=asset==='live'||asset==='home'?'world':asset==='news'?'events':asset;
 root.style.setProperty('--mobile-banner',`url('${new URL('assets/banner-'+mobileScene+'.jpg',document.baseURI).href}')`);
 const [x,y,w,h]=crop;
 root.style.setProperty('--banner-size',`${1536/w*100}% ${1024/h*100}%`);
 root.style.setProperty('--banner-position',`${x/(1536-w)*100}% ${y/(1024-h)*100}%`);
 root.insertAdjacentHTML('afterbegin','<div class="approvedPaper" aria-hidden="true"></div><div class="approvedArtwork" aria-hidden="true"></div>');
 root.querySelectorAll('img').forEach(img=>{img.classList.add('archiveImage');if(img.complete&&img.naturalWidth>0)img.classList.add('imageReady');else img.addEventListener('load',()=>img.classList.add('imageReady'),{once:true})});
 const controls=document.querySelector('.wapControls');if(controls){
  if(matchMedia('(min-width:1100px)').matches)page.appendChild(controls);
  else page.querySelector('.wapBook')?.prepend(controls);
 }
 document.querySelectorAll('.wapLeaf').forEach(leaf=>leaf.classList.add('approvedLeaf'));

 document.querySelectorAll('.wapPerson').forEach(card=>{
  const href=card.querySelector('a')?.getAttribute('href')||'',id=decodeURIComponent(href.split('/').at(-1)||''),p=data.people.find(p=>p.id===id),c=p?main(p):{};
  const [symbol,color]=classSeals[c.className]||['?', '#6e7768'];
  card.insertAdjacentHTML('beforeend',`<span class="classSeal" style="--seal:${color}" aria-hidden="true">${symbol}</span>`);
 });
 applyBookTurnControls(root);
 const search=document.querySelector('.bookSearch input');if(search)search.placeholder=asset==='guilds'?'길드명을 검색해보세요.':'이름, 캐릭터명, 길드명으로 검색해보세요.';
}
// Reuse the actual paging actions; only their desktop placement is shared.
function applyBookTurnControls(root){
 const sources=[...root.querySelectorAll('.wapBook>.wapLeaf>.leafPager')];
 const journal=root.querySelector('.journalPager');
 if(!sources.length&&!journal)return;
 const bar=document.createElement('nav');bar.className='bookTurnBar';bar.setAttribute('aria-label','책 넘기기');
 for(const source of (journal?[journal,journal]:sources)){
  const pager=source.cloneNode(true);pager.className='leafPager';bar.append(pager);
 }
 root.append(bar);
}
// Every route uses the home navigation, including detail and administrator routes.
function applyUnifiedHeader(){
 document.body.classList.add('unifiedHeader');
 const links=document.querySelector('.tavernHeader .links'),menu=document.querySelector('.tavernHeader .menu');
 menu.onclick=()=>{const open=links.classList.toggle('open');menu.setAttribute('aria-expanded',String(open))};
 document.querySelector('.tavernHeader').addEventListener('keydown',e=>{if(e.key==='Escape'){links.classList.remove('open');menu.setAttribute('aria-expanded','false');menu.focus()}});
}
const approvedShowModal=showBookModal;
showBookModal=function(markup,kind){
 approvedShowModal(markup,kind);
 const modal=document.querySelector('[role="dialog"]');
 if(modal){modal.classList.add('approvedModal');modal.insertAdjacentHTML('afterbegin',`<div class="approvedModalPaper" aria-hidden="true"></div><div class="approvedModalArtwork ${kind==='guild'?'guildModalArt':'personModalArt'}" aria-hidden="true"></div>`);}
};
matchMedia('(min-width:1100px)').addEventListener('change',()=>render());
render();
