/* Approved ten-screen book UI. Presentation state never writes archive records. */
let bookFilters={className:'',race:'',guildId:'',faction:'',style:'',size:''};
let bookView='grid',favoriteType='people',modalOrigin=route().startsWith('/guild/')?'/guilds':'/adventurers',pendingSearch=null;
let bookReturnState=null;
const baseLayout=layout;
const emptyBook=(text='등록된 기록이 없습니다.')=>`<div class="bookEmpty"><span aria-hidden="true">✧</span><p>${esc(text)}</p></div>`;
const imageArt=(url,cls='')=>url?`<img class="${cls} archiveImage" src="${esc(url)}" alt="" loading="lazy" onload="this.classList.add('imageReady')" onerror="this.hidden=true;this.parentElement.classList.add('imageMissing')">`:`<span class="artPlaceholder" aria-hidden="true">✧</span>`;
const recordLink=(type,id)=>`#/${type}/${encodeURIComponent(id)}`;
const action=(fn,value)=>`${fn}(${esc(JSON.stringify(value))})`;
layout=function(body){
 baseLayout(body);
 const hero=document.querySelector('.pageHero');
 if(hero){hero.insertAdjacentHTML('beforeend','<span class="frameGem" aria-hidden="true"></span>');}
 const search=document.querySelector('.wapControls .bookSearch');
 if(hero&&search)hero.appendChild(search);
 const book=document.querySelector('.wapBook');
 if(book){
  const toolbar=document.querySelector('.wapControls,.wapChronTabs');
  if(toolbar)book.prepend(toolbar);
  book.insertAdjacentHTML('beforeend','<span class="frameGem bookGem" aria-hidden="true"></span>');
 }
 document.querySelectorAll('.wapPortrait img,.wapDetailPhoto img,.wapMemberGrid img,.avatar img').forEach(img=>{img.loading='lazy';img.onerror=()=>{img.hidden=true;img.parentElement.classList.add('imageMissing')}});
}
function bookFrame(left,right){return `<div class="wrap wapBook"><div class="wapLeaf">${left}</div><div class="wapLeaf">${right}</div></div>`}
function resetBookFilters(){bookIndex=0;bookQuery='';Object.keys(bookFilters).forEach(k=>bookFilters[k]='')}
function setBookFilter(key,value){bookFilters[key]=value;bookIndex=0;render()}
function setBookQuery(value){
 const input=document.activeElement,at=input?.selectionStart,id=input?.id;
 bookQuery=value;bookIndex=0;render();
 if(id){const next=document.getElementById(id);next?.focus();if(next?.type==='search')next.setSelectionRange(at,at)}
}
function bookControls(type){
 const people=type!=='guild';
 const options=(key,label,values)=>`<select class="field" aria-label="${label}" onchange="setBookFilter('${key}',this.value)"><option value="">전체 ${label}</option>${[...new Set(values.filter(Boolean))].sort((a,b)=>a.localeCompare(b,'ko')).map(v=>`<option value="${esc(v)}" ${bookFilters[key]===v?'selected':''}>${esc(key==='guildId'?guild(v)?.name||v:v)}</option>`).join('')}</select>`;
 const chars=data.people.map(main);
 const filters=people?options('className','직업',chars.map(c=>c.className))+options('race','종족',chars.map(c=>c.race))+options('guildId','길드',chars.map(c=>c.guildId)):options('faction','진영',data.guilds.map(g=>g.faction))+options('style','성향',data.guilds.map(g=>g.style))+options('size','규모',['소규모','중규모','대규모']);
 return `<div class="wapControls"><div class="bookFilters">${filters}</div><label class="bookSearch"><span aria-hidden="true">⌕</span><input id="bookSearch" type="search" aria-label="${people?'모험가':'길드'} 검색" placeholder="${people?'이름, 캐릭터명, 길드명':'길드명'}으로 검색해 보세요" value="${esc(bookQuery)}" oninput="setBookQuery(this.value)"></label><div class="bookSort"><label for="bookSort">정렬:</label><select id="bookSort" class="field" onchange="bookSort=this.value;bookIndex=0;render()">${[['name','이름순'],['recent','최근 등록순'],...(people?[['level','레벨 높은 순']]:[['members','길드원 많은 순']])].map(([v,t])=>`<option value="${v}" ${bookSort===v?'selected':''}>${t}</option>`).join('')}</select><div class="viewSwitch" role="group" aria-label="보기 방식">${[['grid','▦','격자 보기'],['list','☷','목록 보기']].map(([v,icon,label])=>`<button aria-label="${label}" aria-pressed="${bookView===v}" class="${bookView===v?'active':''}" onclick="bookView='${v}';render()">${icon}</button>`).join('')}</div></div></div>`;
}
function leafPager(total,perLeaf,side){
 const pages=Math.max(1,Math.ceil(total/perLeaf)),spreads=Math.max(1,Math.ceil(pages/2));
 return `<div class="leafPager"><button aria-label="이전 펼침" ${bookIndex===0?'disabled':''} onclick="bookIndex--;render()">‹</button><span>${Math.min(bookIndex*2+side+1,pages)} / ${pages}</span><button aria-label="다음 펼침" ${bookIndex>=spreads-1?'disabled':''} onclick="bookIndex++;render()">›</button></div>`;
}
function pagedBook(items,perLeaf,cls,card,empty='검색 결과가 없습니다.'){
 bookIndex=Math.min(bookIndex,Math.max(0,Math.ceil(items.length/(perLeaf*2))-1));const start=bookIndex*perLeaf*2;
 return bookFrame(...[0,1].map(side=>`<div class="wapGrid ${cls} ${bookView==='list'?'bookListView':''}">${items.slice(start+side*perLeaf,start+(side+1)*perLeaf).map(card).join('')||emptyBook(items.length?'이 페이지의 기록이 없습니다.':empty)}</div>${leafPager(items.length,perLeaf,side)}`));
}
function filteredPeople(items=data.people){
 const q=bookQuery.trim().toLocaleLowerCase();
 return items.filter(p=>{const c=main(p);return ['className','race','guildId'].every(k=>!bookFilters[k]||c[k]===bookFilters[k])&&[p.name,...(p.characters||[]).flatMap(c=>[c.name,c.className,c.race,guild(c.guildId)?.name])].join(' ').toLocaleLowerCase().includes(q)}).sort((a,b)=>bookSort==='level'?Number(main(b).level||0)-Number(main(a).level||0):bookSort==='recent'?data.people.indexOf(b)-data.people.indexOf(a):a.name.localeCompare(b.name,'ko'));
}
function filteredGuilds(items=data.guilds){return items.filter(g=>(g.name+' '+(g.description||'')).toLowerCase().includes(bookQuery.toLowerCase())&&['faction','style'].every(k=>!bookFilters[k]||g[k]===bookFilters[k])&&(!bookFilters.size||(g.total!==''&&g.total!=null&&((Number(g.total)<20?'소규모':Number(g.total)<50?'중규모':'대규모')===bookFilters.size)))).sort((a,b)=>bookSort==='members'?Number(b.total||0)-Number(a.total||0):bookSort==='recent'?data.guilds.indexOf(b)-data.guilds.indexOf(a):a.name.localeCompare(b.name,'ko'))}
function personCard(p){const c=main(p);return `<article class="wapPerson"><a href="${recordLink('adventurer',p.id)}" class="personLink"><div class="wapPortrait">${imageArt(p.image)}</div><strong>${esc(p.name)}</strong><small>${esc(c.name||'캐릭터 미확인')} · ${c.level?'Lv. '+esc(c.level):'레벨 미확인'}</small><small>${esc(c.race||'종족 미확인')} | ${esc(c.className||'직업 미확인')}</small><small class="cardGuild">◈ ${esc(guild(c.guildId)?.name||'길드 미확인')}</small>${p.past?.participated==='no'?'<span class="wapNew">NEW</span>':''}</a><button class="cardFavorite ${isFav('people',p.id)?'on':''}" aria-label="${esc(p.name)} 즐겨찾기" aria-pressed="${isFav('people',p.id)}" onclick="${action('togglePersonFavorite',p.id)}">${isFav('people',p.id)?'★':'☆'}</button></article>`}
function togglePersonFavorite(id){toggleFav('people',id)}
function toggleGuildFavorite(id){toggleFav('guilds',id)}
function guildCardBook(g){const n=data.people.filter(p=>p.characters?.some(c=>c.guildId===g.id)).length;return `<article class="wapGuild"><a href="${recordLink('guild',g.id)}"><div class="wapGuildArt" style="${g.image?'background-image:url(&quot;'+esc(g.image)+'&quot;)':''}"><span class="guildStandard" aria-hidden="true"></span><h3>${esc(g.name)}</h3><p>${esc(g.description||'길드 소개 미등록')}</p></div><div class="wapGuildNumbers"><span>총 길드원 수<b>${g.total!==''&&g.total!=null?esc(g.total)+'명':'미확인'}</b></span><span>VTuber 수<b>${n}명</b></span></div><span class="wapView">상세 보기 ›</span></a><button class="cardFavorite ${isFav('guilds',g.id)?'on':''}" aria-label="${esc(g.name)} 즐겨찾기" aria-pressed="${isFav('guilds',g.id)}" onclick="${action('toggleGuildFavorite',g.id)}">${isFav('guilds',g.id)?'★':'☆'}</button></article>`}
function peopleList(){layout(head('모험가 도감','아제로스를 누비는 모든 모험가들의 기록입니다.')+bookControls('people')+pagedBook(filteredPeople(),16,'peopleGrid',personCard))}
function guildList(){layout(head('길드 도감','아제로스에서 활동하는 모든 길드들의 기록입니다.')+bookControls('guild')+pagedBook(filteredGuilds(),4,'guildGrid',guildCardBook))}
function favorites(){const f=fav(),isPeople=favoriteType==='people';const items=isPeople?filteredPeople(data.people.filter(p=>f.people.includes(p.id))):filteredGuilds(data.guilds.filter(g=>f.guilds.includes(g.id)));layout(head('즐겨찾기','관심 있는 모험가와 길드를 모아 빠르게 확인할 수 있습니다.')+bookControls(isPeople?'people':'guild')+pagedBook(items,isPeople?12:4,isPeople?'peopleGrid favoriteGrid':'guildGrid',isPeople?personCard:guildCardBook,(isPeople?f.people.length:f.guilds.length)?'검색 조건에 맞는 즐겨찾기가 없습니다.':'아직 저장한 즐겨찾기가 없습니다. 도감에서 별을 눌러 보세요.'));document.querySelector('.bookFilters').insertAdjacentHTML('beforebegin',`<div class="favoriteTabs"><button class="${isPeople?'active':''}" onclick="favoriteType='people';resetBookFilters();render()">♟ 모험가 즐겨찾기</button><button class="${!isPeople?'active':''}" onclick="favoriteType='guilds';resetBookFilters();render()">♜ 길드 즐겨찾기</button></div>`)}
function livePage(){const items=filteredPeople();layout(head('라이브','지금 아제로스에서 모험 중인 방송을 확인하세요.')+bookControls('people')+pagedBook(items,8,'liveGrid',p=>{const c=main(p);return `<article class="wapLiveCard"><div class="liveScenery"><span class="liveUnknown">방송 상태 미연동</span></div><a href="${recordLink('adventurer',p.id)}" class="liveIdentity"><div class="liveAvatar">${imageArt(p.image)}</div><div><b>${esc(p.name)}</b><small>${esc(c.name||'캐릭터 미확인')} | ${c.level?'Lv. '+esc(c.level):'레벨 미확인'} | ${esc(guild(c.guildId)?.name||'길드 미확인')}</small></div></a>${p.soop?`<a class="stationLink" href="${esc(p.soop)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(p.name)} SOOP 방송국">↗</a>`:''}</article>`}));document.querySelector('.wapBook').insertAdjacentHTML('afterend','<p class="wapLiveNotice">SOOP 실시간 상태와 시청자 수는 아직 연동되지 않았습니다. 등록된 방송국으로 이동할 수 있습니다.</p>')}
function goSearch(value){pendingSearch=value;resetBookFilters();bookQuery=value;location.hash='/adventurers';render()}
function chartBook(values,kind='bar'){
 const entries=Object.entries(values),total=entries.reduce((s,[,v])=>s+v,0);
 if(!total)return emptyBook('확인된 데이터가 없습니다.');
 if(kind==='level')return `<div class="levelChart">${entries.map(([k,v],i)=>`<div class="levelColumn" style="--chart-color:${['#69adc7','#388bd0','#8bbd59','#e4bd43','#e88b42','#cf5357','#df82b5'][i%7]}"><b>${v}</b><div class="levelTrack"><i style="height:${v/Math.max(...entries.map(e=>e[1]))*100}%"></i></div><span>${esc(k)}</span></div>`).join('')}</div>`;
 return `<div class="bookChart ${kind==='level'?'levelChart':''}">${entries.map(([k,v],i)=>`<div class="chartRow" style="--chart-color:${['#cf5357','#df82b5','#8bbd59','#e4bd43','#69adc7','#388bd0','#9c69bc','#e88b42'][i%8]};--value:${v/Math.max(...entries.map(e=>e[1]))*100}%"><span>${esc(k)}</span><div class="chartTrack"><i></i></div><b>${v} <small>(${(v/total*100).toFixed(1)}%)</small></b></div>`).join('')}</div>`;
}
function world(){
 const chars=data.people.map(main),counts=key=>chars.reduce((o,c)=>{if(c[key]&&c[key]!=='미확인')o[c[key]]=(o[c[key]]||0)+1;return o},{});
 const levels=chars.reduce((o,c)=>{const n=Number(c.level);if(n>0){const k=n>=60?'60+':`${Math.floor(n/10)*10}–${Math.floor(n/10)*10+9}`;o[k]=(o[k]||0)+1}return o},{});
 const season={'신규 모험가':data.people.filter(p=>p.past?.participated==='no').length,'이전 시즌 참여자':data.people.filter(p=>p.past?.participated==='yes').length,'참여 여부 미확인':data.people.filter(p=>!['yes','no'].includes(p.past?.participated)).length};
 const block=(title,content)=>`<section class="statSection"><h2>${title}</h2>${content}</section>`;
 layout(head('월드 현황','아제로스 곳곳에 남겨진 모험의 기록입니다.')+bookFrame(`<div class="wapStatPair"><div><span>♟ 등록된 모험가</span><strong>${data.people.length}<small> 명</small></strong></div><div><span>⚑ 등록된 길드</span><strong>${data.guilds.length}<small> 개</small></strong></div></div>`+block('⚔ 직업 분포',chartBook(counts('className')))+block('Lv. 레벨 분포',chartBook(Object.fromEntries(Object.entries(levels).sort((a,b)=>parseInt(a[0])-parseInt(b[0]))),'level')),block('✧ 이전 시즌 참여 현황',chartBook(season))+block('◉ 종족 분포',chartBook(counts('race')))+block('⛨ 역할 비율',chartBook(counts('role')))))
}
let journalQuery='',journalCategory=route()==='/events'?'event':'all',journalIndex=0,journalPage=0;
function setJournalQuery(value){const pos=document.activeElement?.selectionStart;journalQuery=value;journalIndex=0;journalPage=0;render();const n=document.getElementById('journalSearch');n?.focus();n?.setSelectionRange(pos,pos)}
function journalControls(mode){const categories=mode==='chronicle'?[['all','전체'],['주요 사건','주요 사건'],['레이드','레이드 기록']]:[['all','전체'],['official','공식 소식'],['패치노트','패치노트'],['event','이벤트']];return `<div class="journalTabs">${categories.map(([v,t])=>`<button class="${journalCategory===v?'active':''}" onclick="journalCategory='${v}';journalIndex=0;journalPage=0;render()">${t}</button>`).join('')}</div><label class="journalSearch"><span>⌕</span><input id="journalSearch" type="search" aria-label="기록 검색" placeholder="제목, 내용으로 검색하세요..." value="${esc(journalQuery)}" oninput="setJournalQuery(this.value)"></label>`}
function journalBook(mode){
 let items=mode==='chronicle'?data.chronicle.map(c=>({...c,kind:c.category||'주요 사건'})):[...newsItems().map(n=>({...n,kind:n.category==='패치노트'?'패치노트':'official',source:n.url})),...data.events.map(e=>({...e,kind:'event'}))];
 items=items.filter(x=>(journalCategory==='all'||x.kind===journalCategory)&&((x.title||'')+' '+(x.description||'')).toLowerCase().includes(journalQuery.toLowerCase())).sort((a,b)=>(b.date||'').localeCompare(a.date||''));
 journalIndex=Math.min(journalIndex,Math.max(0,items.length-1));journalPage=Math.min(journalPage,Math.max(0,Math.ceil(items.length/6)-1));const chosen=items[journalIndex];
 const title=mode==='chronicle'?'연대기':'포에버 소식 · 이벤트',hero=mode==='chronicle'?'아제로스에서 이어지는 모험들의 기록입니다.':'아제로스에서 전해지는 새로운 소식과 이벤트를 한눈에 확인하세요.';
 const thumb=x=>`<div class="journalThumb ${x.kind==='event'?'eventThumb':x.kind==='레이드'?'raidThumb':''}">${x.image?imageArt(x.image):''}</div>`;
 layout(head(title,hero)+bookFrame(journalControls(mode)+`<div class="wapTimeline">${items.slice(journalPage*6,journalPage*6+6).map((x,i)=>`<button class="${journalIndex===journalPage*6+i?'active':''}" onclick="journalIndex=${journalPage*6+i};render()">${thumb(x)}<span><small>${esc(x.date||'날짜 미확인')} · ${esc(x.kind==='official'?'공식 소식':x.kind==='event'?'이벤트':x.kind)}</small><strong>${esc(x.title)}</strong><p>${esc(x.description||'기록의 자세한 내용을 확인하세요.')}</p></span></button>`).join('')||emptyBook('등록된 기록이 없습니다.')}</div><div class="journalPager"><button aria-label="이전 기록 페이지" ${journalPage===0?'disabled':''} onclick="journalPage--;journalIndex=journalPage*6;render()">‹</button><span>${journalPage+1} / ${Math.max(1,Math.ceil(items.length/6))}</span><button aria-label="다음 기록 페이지" ${(journalPage+1)*6>=items.length?'disabled':''} onclick="journalPage++;journalIndex=journalPage*6;render()">›</button></div>`,chosen?`<article class="journalDetail"><small class="wapDate">${esc(chosen.date||'일정 미정')}</small><span class="journalBadge">${esc(chosen.kind==='event'?'이벤트':chosen.kind==='official'?'공식 소식':chosen.kind)}</span><h2>${esc(chosen.title)}</h2>${thumb(chosen)}<p class="wapLongText">${esc(chosen.description||(chosen.kind==='official'||chosen.kind==='패치노트'?'공식 발표의 자세한 내용은 원문에서 확인할 수 있습니다.':'상세 설명 미등록'))}</p>${chosen.result?`<h3>결과</h3><p class="wapLongText">${esc(chosen.result)}</p>`:''}${chosen.status?`<div class="wapDetailRow"><span>진행 상태</span><b>${esc(chosen.status)}</b></div>`:''}${chosen.source?`<a class="wapView" target="_blank" rel="noopener noreferrer" href="${esc(chosen.source)}">${chosen.kind==='official'||chosen.kind==='패치노트'?'공식 원문 보기':'기록 출처'} ↗</a>`:''}</article>`:emptyBook('왼쪽에서 기록을 선택하세요.')))
}
function chronicle(){journalBook('chronicle')}
function newsPage(){journalBook('news')}
function eventsHub(){journalBook('news')}
function eventDetail(id){const index=data.events.findIndex(e=>e.id===id);if(index<0)return notFound();journalCategory='event';const sorted=[...data.events].sort((a,b)=>(b.date||'').localeCompare(a.date||''));journalIndex=sorted.findIndex(e=>e.id===id);journalBook('news')}
function showBookModal(markup,kind){
 const background=document.querySelector('main');background?.setAttribute('inert','');background?.setAttribute('aria-hidden','true');
 document.body.insertAdjacentHTML('beforeend',`<div class="bookModalBackdrop" onclick="if(event.target===this)closeBookModal()"><section class="${kind==='guild'?'guildBookModal':'personBookModal'}" role="dialog" aria-modal="true" aria-labelledby="detailTitle"><button class="wapClose" onclick="closeBookModal()" aria-label="상세 닫기">×</button>${markup}</section></div>`);
 document.body.classList.add('modalOpen');document.querySelector('.wapClose')?.focus();
}
function closeBookModal(){location.hash=modalOrigin;}
function modalBackground(kind){if(modalOrigin==='/favorites')favorites();else if(modalOrigin==='/live')livePage();else if(kind==='guilds')guildList();else peopleList()}
function profile(id){
 const p=data.people.find(x=>x.id===id);if(!p)return notFound();const c=main(p),g=guild(c.guildId);modalBackground('people');
 const row=(k,v)=>`<div class="wapDetailRow"><span>${k}</span><b>${esc(v||'미확인')}</b></div>`;
 showBookModal(`<div class="wapDetailPhoto">${imageArt(p.image)}</div><div class="wapDetailInfo"><h1 id="detailTitle">${esc(p.name)} <button class="heart ${isFav('people',id)?'on':''}" aria-label="즐겨찾기" aria-pressed="${isFav('people',id)}" onclick="${action('togglePersonFavorite',id)}">${isFav('people',id)?'★':'☆'}</button></h1>${row('인게임 닉네임',c.name)}${row('레벨',c.level)}${row('종족',c.race)}${row('직업',c.className)}${row('전문화',(c.spec||'미확인')+(c.role?' ('+c.role+')':''))}<div class="wapDetailRow"><span>현 길드</span>${g?`<a href="${recordLink('guild',g.id)}">${esc(g.name)} ›</a>`:'<b>미확인</b>'}</div>${p.soop?`<div class="wapDetailRow"><span>SOOP 방송국</span><a class="wapSoop" target="_blank" rel="noopener noreferrer" href="${esc(p.soop)}">↗ 바로가기</a></div>`:''}${row('정보 최종 확인일',p.verified)}</div>${p.past?.participated==='no'?'<span class="detailNew"><span>NEW</span></span>':''}<section class="wapSeason"><h2>이전 시즌 참여 기록</h2><p>${esc(({yes:'이전 시즌 참여',no:'신규 모험가',unknown:'참여 여부 미확인'})[p.past?.participated||'unknown'])}</p>${p.past?.participated==='yes'?`<p>Lv. ${esc(p.past.level||'미확인')} · ${esc(p.past.className||'직업 미확인')} · ${esc(p.past.spec||'전문화 미확인')}</p><p>${esc((p.past.raids||[]).join(' · ')||'레이드 기록 미등록')}</p>`:''}${(p.characters||[]).length>1?`<h2>다른 캐릭터</h2>${p.characters.filter(x=>x!==c).map(x=>`<div class="wapDetailRow"><span>${esc(x.name)}</span><b>Lv. ${esc(x.level||'?')} · ${esc(x.className||'미확인')} · ${esc(guild(x.guildId)?.name||'길드 미확인')}</b></div>`).join('')}`:''}<a class="detailReport" href="#/report">정보 수정 제보 ›</a></section>`,'person');
}
function guildDetail(id){
 const g=guild(id);if(!g)return notFound();modalBackground('guilds');const members=data.people.filter(p=>p.characters?.some(c=>c.guildId===id)),records=data.chronicle.filter(c=>c.guildId===id||c.guildIds?.includes(id)||((c.title||'')+' '+(c.description||'')).includes(g.name)).sort((a,b)=>(b.date||'').localeCompare(a.date||'')).slice(0,5);
 showBookModal(`<div class="wapLeaf"><div class="guildDetailScenery"><span class="guildStandard"></span></div><h1 id="detailTitle">${esc(g.name)} <button class="heart ${isFav('guilds',id)?'on':''}" aria-label="길드 즐겨찾기" aria-pressed="${isFav('guilds',id)}" onclick="${action('toggleGuildFavorite',id)}">${isFav('guilds',id)?'★':'☆'}</button></h1><div class="wapDetailRow"><span>길드장</span><b>${esc(g.leader||'미확인')}</b></div><div class="wapDetailRow"><span>전체 길드원 수</span><b>${g.total!==''&&g.total!=null?esc(g.total)+'명':'미확인'}</b></div><div class="wapDetailRow"><span>등록 VTuber 수</span><b>${members.length}명</b></div><p>${esc(g.description||'길드 소개 미등록')}</p><h2>⚑ 길드 활동 기록</h2><div class="wapActivity">${records.map(c=>`<div><small>${esc(c.date||'날짜 미확인')}</small><b>${esc(c.title)}</b></div>`).join('')||emptyBook('아직 등록된 활동 기록이 없습니다.')}</div><a class="detailReport" href="#/chronicle">전체 기록 보기 ›</a></div><div class="wapLeaf"><h2>♟ 길드원 목록 (${members.length}명)</h2><div class="wapMemberGrid">${members.map(p=>`<a href="${recordLink('adventurer',p.id)}"><div class="memberPortrait">${imageArt(p.image)}</div><strong>${esc(p.name)}</strong><small>${esc(main(p).className||'직업 미확인')}</small></a>`).join('')||emptyBook('등록된 모험가가 없습니다.')}</div></div>`,'guild');
}
const oldRender=render;
render=function(){document.querySelector('.bookModalBackdrop')?.remove();document.body.classList.remove('modalOpen');oldRender()};
let previousBookRoute=route();
window.removeEventListener('hashchange',onArchiveHashChange);
window.addEventListener('hashchange',()=>{
 const current=route(),previous=previousBookRoute;
 const isDetail=/^\/(adventurer|guild)\//.test(current),wasDetail=/^\/(adventurer|guild)\//.test(previous);
 const returning=wasDetail&&!isDetail&&current===modalOrigin&&bookReturnState;
 if(isDetail&&!wasDetail){
  modalOrigin=['/favorites','/live','/guilds','/adventurers'].includes(previous)?previous:current.startsWith('/guild/')?'/guilds':'/adventurers';
  bookReturnState={bookIndex,bookQuery,bookSort,bookView,favoriteType,filters:{...bookFilters},scrollY};
 }
 if(!isDetail){
  if(returning){
   ({bookIndex,bookQuery,bookSort,bookView,favoriteType}=bookReturnState);
   bookFilters={...bookReturnState.filters};
  }else if(previous!==current){
   resetBookFilters();filter='';journalQuery='';journalCategory=current==='/events'?'event':'all';journalPage=0;journalIndex=0;
  }
 }
 if(pendingSearch!==null){bookQuery=pendingSearch;pendingSearch=null}
 profileTab='character';previousBookRoute=current;render();
 if(returning){
  window.scrollTo(0,bookReturnState.scrollY);
  [...document.querySelectorAll('a[href]')].find(a=>a.getAttribute('href')==='#'+previous)?.focus({preventScroll:true});
 }else if(!isDetail)window.scrollTo(0,0);
});
document.addEventListener('keydown',e=>{const modal=document.querySelector('[role="dialog"]');if(!modal)return;if(e.key==='Escape'){closeBookModal();return}if(e.key==='Tab'){const all=[...modal.querySelectorAll('a[href],button,input,select,[tabindex="0"]')].filter(n=>!n.disabled);const first=all[0],last=all.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus()}}});
render();
