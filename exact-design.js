/* Original artwork is rendered through decorative masks. Mockup records are never displayed or saved. */
const approvedPages={home:'home',adventurers:'adventurers',guilds:'guilds',world:'world',news:'news',events:'news',chronicle:'chronicle',favorites:'favorites',live:'live'};
const approvedLayout=layout;
const classSeals={'전사':['⚔','#a48960'],'성기사':['✦','#d97ac0'],'사냥꾼':['➶','#80aa46'],'도적':['➶','#c5aa29'],'사제':['✧','#ece2b2'],'주술사':['ϟ','#368ace'],'마법사':['ϟ','#5aaed4'],'흑마법사':['ϟ','#9c59c5'],'드루이드':['☀','#d98b31']};
layout=function(body){approvedLayout(body);applyApprovedArtwork()};
function applyApprovedArtwork(){
 const page=document.querySelector('main'),key=page?.className.match(/page-(\w+)/)?.[1],asset=approvedPages[key];
 document.body.classList.toggle('approvedDesign',Boolean(asset));
 applyUnifiedHeader();
 if(!asset)return;
 const root=document.getElementById('app');root.style.setProperty('--approved',`url('${new URL('assets/approved/'+asset+'.webp',document.baseURI).href}')`);root.dataset.reference=asset;
 // Replace the whole inner paper surface, following its rounded book edges.
 // Narrow screenshot cut-outs left visible rectangular seams inside the pages.
 const top=asset==='live'?.257:asset==='favorites'?.27:.306;
 const right=['live','favorites'].includes(asset)?.967:.941;
 const sheet=(left,end)=>`<path d="M ${left+.027} ${top} Q ${left} ${top} ${left} ${top+.026} L ${left} .941 Q ${left} .969 ${left+.027} .969 L ${end-.024} .969 Q ${end} .969 ${end} .941 L ${end} ${top+.027} Q ${end} ${top} ${end-.025} ${top} Z"/>`;
 const shapes=asset==='home'?
  '<rect x=".092" y=".551" width=".271" height=".096" rx=".003"/><rect x=".379" y=".551" width=".273" height=".096" rx=".003"/><rect x=".663" y=".551" width=".28" height=".096" rx=".003"/><rect x=".094" y=".671" width=".85" height=".263" rx=".012"/>' : sheet(.066,.491)+sheet(.52,right);
 const tiles='<div class="paperLeaf"></div>';
 root.insertAdjacentHTML('afterbegin',`<svg class="artMaskDefinitions" aria-hidden="true"><defs><filter id="paperEdgeBlend" x="-.05" y="-.05" width="1.1" height="1.1" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation=".003"/></filter><mask id="approvedDecorMask" maskUnits="objectBoundingBox" maskContentUnits="objectBoundingBox" style="mask-type:luminance"><rect width="1" height="1" fill="white"/><rect width="1" height=".125" fill="black"/><g fill="black" filter="url(#paperEdgeBlend)">${shapes}</g></mask></defs></svg><div class="approvedPaper" aria-hidden="true">${tiles}${tiles}</div><div class="approvedArtwork" aria-hidden="true"></div><div class="bookLowerEdge" aria-hidden="true"></div>`);
 root.querySelectorAll('img').forEach(img=>{img.classList.add('archiveImage');if(img.complete&&img.naturalWidth>0)img.classList.add('imageReady');else img.addEventListener('load',()=>img.classList.add('imageReady'),{once:true})});
 const controls=document.querySelector('.wapControls');if(controls)page.appendChild(controls);
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
 const items=[['/','⌂ 홈'],['/adventurers','▣ 모험가 도감'],['/guilds','♜ 길드 도감'],['/world','◉ 월드 현황'],['/updates','▤ 포에버 소식 · 이벤트'],['/chronicle','▤ 연대기'],['/favorites','☆ 즐겨찾기'],['/live','● 라이브']];
 let current=route();
 if(current.startsWith('/adventurer/'))current='/adventurers';
 if(current.startsWith('/guild/'))current='/guilds';
 if(['/news','/events'].includes(current)||current.startsWith('/event/'))current='/updates';
 const links=document.querySelector('.header .links');
 links.classList.remove('splitNavigation');
 links.innerHTML=items.map(([href,label])=>`<a href="#${href}" title="${label.replace(/^[^ ]+ /,'')}" ${current===href?'aria-current="page"':''}>${href==='/live'?'<span class="navLiveDot" aria-hidden="true"></span>라이브':href==='/updates'?'<span>▤ 포에버 소식<br>· 이벤트</span>':label}</a>`).join('');
 document.querySelector('.logo')?.setAttribute('aria-label','와포북 홈');
 const menu=document.querySelector('.header .menu');
 menu.setAttribute('aria-label','전체 메뉴');menu.setAttribute('aria-controls','navlinks');menu.setAttribute('aria-expanded','false');
 menu.onclick=()=>{const open=links.classList.toggle('open');menu.setAttribute('aria-expanded',String(open))};
 links.addEventListener('keydown',e=>{if(e.key==='Escape'){links.classList.remove('open');menu.setAttribute('aria-expanded','false');menu.focus()}});
}
const approvedShowModal=showBookModal;
showBookModal=function(markup,kind){
 approvedShowModal(markup,kind);
 const modal=document.querySelector('[role="dialog"]');
 if(modal){modal.classList.add('approvedModal');modal.insertAdjacentHTML('afterbegin',`<div class="approvedModalPaper" aria-hidden="true"></div><div class="approvedModalArtwork ${kind==='guild'?'guildModalArt':'personModalArt'}" aria-hidden="true"></div>`);}
};
render();
