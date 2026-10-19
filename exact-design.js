/* Original artwork is rendered through decorative masks. Mockup records are never displayed or saved. */
const approvedPages={home:'home',adventurers:'adventurers',guilds:'guilds',world:'world',news:'news',events:'news',chronicle:'chronicle',favorites:'favorites',live:'live'};
const approvedLayout=layout;
const classSeals={'전사':['⚔','#a48960'],'성기사':['✦','#d97ac0'],'사냥꾼':['➶','#80aa46'],'도적':['➶','#c5aa29'],'사제':['✧','#ece2b2'],'주술사':['ϟ','#368ace'],'마법사':['ϟ','#5aaed4'],'흑마법사':['ϟ','#9c59c5'],'드루이드':['☀','#d98b31']};
layout=function(body){approvedLayout(body);applyApprovedArtwork()};
function applyApprovedArtwork(){
 const page=document.querySelector('main'),key=page?.className.match(/page-(\w+)/)?.[1],asset=approvedPages[key];
 document.body.classList.toggle('approvedDesign',Boolean(asset));
 if(!asset)return;
 const root=document.getElementById('app');root.style.setProperty('--approved',`url('${new URL('assets/approved/'+asset+'.webp',document.baseURI).href}')`);root.dataset.reference=asset;
 const shapes=asset==='home'?
  '<rect x=".092" y=".551" width=".271" height=".096" rx=".003"/><rect x=".379" y=".551" width=".273" height=".096" rx=".003"/><rect x=".663" y=".551" width=".28" height=".096" rx=".003"/><rect x=".098" y=".716" width=".842" height=".205"/>' : asset==='live'?
  '<rect x=".071" y=".263" width=".416" height=".65" rx=".015"/><rect x=".531" y=".263" width=".424" height=".65" rx=".015"/><rect x=".22" y=".922" width=".2" height=".045"/><rect x=".67" y=".922" width=".2" height=".045"/>' : asset==='favorites'?
  '<rect x=".071" y=".279" width=".427" height=".591" rx=".016"/><rect x=".531" y=".279" width=".424" height=".591" rx=".016"/><rect x=".22" y=".875" width=".2" height=".055"/><rect x=".67" y=".875" width=".2" height=".055"/>' :
  '<rect x=".072" y=".312" width=".414" height=".647" rx=".014"/><rect x=".521" y=".312" width=".414" height=".647" rx=".014"/>';
 const tiles='<div class="paperLeaf"></div>';
 root.insertAdjacentHTML('afterbegin',`<svg class="artMaskDefinitions" aria-hidden="true"><defs><mask id="approvedDecorMask" maskUnits="objectBoundingBox" maskContentUnits="objectBoundingBox" style="mask-type:luminance"><rect width="1" height="1" fill="white"/><g fill="black">${shapes}</g></mask></defs></svg><div class="approvedPaper" aria-hidden="true">${tiles}${tiles}</div><div class="approvedArtwork" aria-hidden="true"></div>`);
 const links=document.querySelector('.header .links');
 // Retain accessible real links over the original navigation artwork.
 const split=['home','adventurers','guilds','world'].includes(asset);
 const items=[['/','⌂ 홈'],['/adventurers','▣ 모험가 도감'],['/guilds','♜ 길드 도감'],['/world','◉ 월드 현황'],['/updates',split?'▤ 포에버 소식':'▤ 포에버 소식 · 이벤트'],...(split?[['/events','♜ 이벤트']]:[]),['/chronicle','▤ 연대기'],['/favorites','☆ 즐겨찾기'],['/live','● 라이브']];
 if(asset==='live')items.splice(-2,2,['/live','● 라이브'],['/favorites','☆ 즐겨찾기']);
 links.innerHTML=items.map(([href,label])=>`<a href="#${href}" title="${label.replace(/^[^ ]+ /,'')}" ${route()===href?'aria-current="page"':''}>${label}</a>`).join('');links.classList.toggle('splitNavigation',split);
 document.querySelector('.logo')?.setAttribute('aria-label','와포북 홈');
 root.querySelectorAll('img').forEach(img=>{img.classList.add('archiveImage');if(img.complete&&img.naturalWidth>0)img.classList.add('imageReady');else img.addEventListener('load',()=>img.classList.add('imageReady'),{once:true})});
 const controls=document.querySelector('.wapControls');if(controls)page.appendChild(controls);
 document.querySelectorAll('.wapLeaf').forEach(leaf=>leaf.classList.add('approvedLeaf'));
 if(asset!=='home'&&asset!=='world')root.insertAdjacentHTML('beforeend','<div class="approvedPagerCover pagerCoverLeft" aria-hidden="true"></div><div class="approvedPagerCover pagerCoverRight" aria-hidden="true"></div>');
 document.querySelectorAll('.wapPerson').forEach(card=>{
  const href=card.querySelector('a')?.getAttribute('href')||'',id=decodeURIComponent(href.split('/').at(-1)||''),p=data.people.find(p=>p.id===id),c=p?main(p):{};
  const [symbol,color]=classSeals[c.className]||['?', '#6e7768'];
  card.insertAdjacentHTML('beforeend',`<span class="classSeal" style="--seal:${color}" aria-hidden="true">${symbol}</span>`);
 });
 const search=document.querySelector('.bookSearch input');if(search)search.placeholder=asset==='guilds'?'길드명을 검색해보세요.':'이름, 캐릭터명, 길드명으로 검색해보세요.';
}
const approvedShowModal=showBookModal;
showBookModal=function(markup,kind){
 approvedShowModal(markup,kind);
 const modal=document.querySelector('[role="dialog"]');
 if(modal){modal.classList.add('approvedModal');modal.insertAdjacentHTML('afterbegin',`<div class="approvedModalPaper" aria-hidden="true"></div><div class="approvedModalArtwork ${kind==='guild'?'guildModalArt':'personModalArt'}" aria-hidden="true"></div>`);}
};
render();
