/* Pure import planner. Never writes storage or replaces existing non-empty fields. */
(function(root){
'use strict';
const CLASSES=['전사','성기사','사냥꾼','도적','사제','주술사','마법사','흑마법사','드루이드','미확인'];
const RACES=['인간','드워프','노움','나이트 엘프','드레나이','오크','언데드','타우렌','트롤','블러드 엘프','미확인'];
const ROLES=['탱커','딜러','힐러','미확인'];
const text=v=>String(v??'').trim();
function account(value){
 if(!text(value))return '';
 if(/^[a-zA-Z0-9_]{2,25}$/.test(text(value)))return text(value).toLowerCase();
 let u;try{u=new URL(text(value));}catch{throw Error('올바른 SOOP 방송국 URL을 입력하세요.');}
 const hosts=['ch.sooplive.co.kr','ch.sooplive.com','bj.afreecatv.com'];
 const m=['www.sooplive.com','www.sooplive.co.kr'].includes(u.hostname)?u.pathname.match(/^\/station\/([a-zA-Z0-9_]{2,25})(?:\/.*)?$/):u.pathname.match(/^\/([a-zA-Z0-9_]{2,25})(?:\/.*)?$/);
 if(!['https:','http:'].includes(u.protocol)||u.username||u.password||u.port||![...hosts,'www.sooplive.com','www.sooplive.co.kr'].includes(u.hostname)||!m)throw Error('지원하는 SOOP 방송국 주소가 아닙니다.');
 return m[1].toLowerCase();
}
function imageURL(value,id){
 try{const u=new URL(value);const hosts=['profile.img.sooplive.co.kr','profile.img.sooplive.com','stimg.sooplive.co.kr','stimg.sooplive.com','profile.img.afreecatv.com'];
 return u.protocol==='https:'&&!u.username&&!u.password&&!u.port&&hosts.includes(u.hostname)&&new RegExp('^/LOGO/'+id.slice(0,2)+'/'+id+'/(?:m/)?'+id+'\\.(?:jpg|jpeg|png|webp|gif)$','i').test(u.pathname)?u.href:'';}catch{return '';}
}
function plan(base,sheets){
 const next=structuredClone(base),results=[];let serial=0;
 const id=prefix=>{let s;do{s=prefix+'-'+(root.crypto?.randomUUID?.()||Date.now().toString(36)+'-'+(++serial));}while([...next.people,...next.guilds].some(x=>x.id===s));return s;};
 const result=(sheet,row,status,detail)=>results.push({sheet,row:row._row||0,name:text(row['버튜버명']||row['길드명']),status,detail});
 const blank=v=>v==null||v===''||v==='미확인'||v==='unknown';
 const fill=(obj,key,value)=>{if(blank(obj[key])&&!blank(value)){obj[key]=value;return true;}return false;};
 const integer=(v,label)=>{if(!text(v))return '';if(!/^\d+$/.test(text(v))||Number(v)<1||!Number.isSafeInteger(Number(v)))throw Error(label+'은 양의 정수여야 합니다.');return text(v);};
 const choose=(v,options,label)=>{v=text(v);if(v&&!options.includes(v))throw Error(label+' 선택값을 확인하세요.');return v==='미확인'?'':v;};
 function findPerson(name,url){
  const aid=account(url);const byAccount=aid?next.people.filter(p=>{try{return account(p.soop)===aid;}catch{return false;}}):[];
  const byName=next.people.filter(p=>text(p.name)===name);
  if(byAccount.length>1||byName.length>1)throw Error('기존 중복 정보가 있습니다. 먼저 수동으로 정리하세요.');
  if(byAccount.length&&byName.length&&byAccount[0].id!==byName[0].id)throw Error('이름과 방송국이 서로 다른 모험가를 가리킵니다.');
  const p=byAccount[0]||byName[0];
  if(p&&aid&&p.soop&&account(p.soop)!==aid)throw Error('같은 이름에 다른 SOOP 계정이 등록되어 있습니다.');
  if(p&&byAccount.length&&p.name!==name)throw Error('같은 SOOP 계정에 다른 버튜버명이 있습니다. 이름을 확인하세요.');
  return p;
 }
 for(const r of sheets['길드 정보']||[]){try{
  const name=text(r['길드명']);if(!name)throw Error('길드명이 필요합니다.');
  const total=integer(r['전체 길드원 수'],'길드원 수'),date=text(r['최종 확인일']);if(date&&!/^\d{4}-\d{2}-\d{2}$/.test(date))throw Error('최종 확인일은 YYYY-MM-DD 형식입니다.');
  const matches=next.guilds.filter(g=>g.name===name);if(matches.length>1)throw Error('기존 길드명이 중복되어 있습니다.');
  let g=matches[0],changed=!g;if(!g){g={id:id('guild'),name,leader:'',total:'',description:'',verified:''};next.guilds.push(g);}
  for(const [k,v] of Object.entries({leader:text(r['길드장']),total,description:text(r['길드 소개']),verified:date}))changed=fill(g,k,v)||changed;
  result('길드 정보',r,changed?'성공':'중복',changed?'새 정보 병합 예정':'기존 정보 유지');
 }catch(e){result('길드 정보',r,'실패',e.message);}}
 for(const r of sheets['모험가 정보']||[]){try{
  const name=text(r['버튜버명']),url=text(r['SOOP 방송국 주소']);if(!name)throw Error('버튜버명이 필요합니다.');
  const aid=account(url),level=integer(r['레벨'],'레벨'),race=choose(r['종족'],RACES,'종족'),className=choose(r['직업'],CLASSES,'직업'),role=choose(r['역할'],ROLES,'역할');
  const charName=text(r['캐릭터명']),guildName=text(r['소속 길드']),primary=text(r['대표 캐릭터']);if(primary&&!['예','아니오'].includes(primary))throw Error('대표 캐릭터는 예/아니오로 선택하세요.');
  const matches=guildName?next.guilds.filter(g=>g.name===guildName):[];if(guildName&&matches.length!==1)throw Error('소속 길드를 길드 정보 시트에 먼저 등록하세요.');
  if(!charName&&[level,race,className,role,guildName,text(r['전문화'])].some(Boolean))throw Error('캐릭터 정보가 있다면 캐릭터명도 필요합니다.');
  let p=findPerson(name,url),changed=!p;
  if(!p){p={id:id('person'),name,soop:'',image:'',returning:'unknown',characters:[],past:{participated:'unknown',raids:[]}};next.people.push(p);}
  changed=fill(p,'soop',aid?'https://www.sooplive.com/station/'+aid:'')||changed;
  if(charName){p.characters=p.characters||[];let c=p.characters.find(c=>c.name===charName);if(!c){c={id:id('char'),name:charName,main:!p.characters.length,level:'',race:'',className:'',spec:'',role:'',guildId:''};p.characters.push(c);changed=true;}
   // An existing representative is never displaced by an import.
   if(primary==='예'&&!p.characters.some(x=>x.main)){c.main=true;changed=true;}
   for(const [k,v] of Object.entries({level,race,className,spec:text(r['전문화']),role,guildId:matches[0]?.id||''}))changed=fill(c,k,v)||changed;
  }
  result('모험가 정보',r,changed?'성공':'중복',changed?'빈 항목만 병합 예정 · 사진은 별도 승인 조회':'기존 정보·사진 유지');
 }catch(e){result('모험가 정보',r,'실패',e.message);}}
 for(const r of sheets['이전 시즌 참여 기록']||[]){try{
  const name=text(r['버튜버명']);if(!name)throw Error('버튜버명이 필요합니다.');const p=findPerson(name,'');if(!p)throw Error('해당 버튜버를 모험가 정보에 먼저 등록하세요.');
  const val=text(r['참여 여부']);if(val&&!['참가','미참가','미확인'].includes(val))throw Error('참여 여부 선택값을 확인하세요.');
  const level=integer(r['당시 레벨'],'당시 레벨'),className=choose(r['당시 직업'],CLASSES,'당시 직업');
  p.past=p.past||{participated:'unknown',raids:[]};let changed=false;
  for(const [k,v] of Object.entries({participated:({참가:'yes',미참가:'no',미확인:'unknown'})[val]||'unknown',level,className,spec:text(r['당시 전문화'])}))changed=fill(p.past,k,v)||changed;
  if(!p.past.raids?.length&&text(r['확인된 레이드 (쉼표 구분)'])){p.past.raids=text(r['확인된 레이드 (쉼표 구분)']).split(',').map(text).filter(Boolean);changed=true;}
  result('이전 시즌 참여 기록',r,changed?'성공':'중복',changed?'빈 이전 시즌 기록 병합 예정':'기존 참여 기록 유지');
 }catch(e){result('이전 시즌 참여 기록',r,'실패',e.message);}}
 return {next,results};
}
function profilePlan(base,report){
 if(report.schema!=='wapobook-soop-profiles-v1'||!Array.isArray(report.results))throw Error('지원하지 않는 프로필 결과 파일입니다.');
 const next=structuredClone(base),results=[];const seen=new Set();
 for(const row of report.results){const aid=text(row.accountId).toLowerCase();let status=row.status,detail='',name=aid;
  if(!/^[a-z0-9_]{2,25}$/.test(aid)){results.push({name,status:'실패',detail:'잘못된 계정 ID'});continue;}
  if(seen.has(aid)){results.push({name,status:'중복',detail:'결과 파일의 중복 계정'});continue;}seen.add(aid);
  const matches=next.people.filter(p=>{try{return account(p.soop)===aid;}catch{return false;}});
  if(matches.length!==1){status='실패';detail='등록된 모험가를 하나로 연결할 수 없습니다.';}
  else{const p=matches[0];name=p.name;
   if(p.image){status='중복';detail='기존 프로필 사진 유지';}
   else if(status==='success'){
    const image=imageURL(row.imageUrl,aid);
    if(!image||row.sourceType!=='station-profile'){status='실패';detail='방송국 프로필 URL만 허용합니다.';}
    else{p.image=image;status='성공';detail='프로필 원본 URL 연결 예정';}
   }else{status=status==='no_image'?'이미지 없음':'실패';detail=text(row.message)||'기본 이미지 유지 · 관리자에서 수동 등록 가능';}
  }results.push({name,status,detail,imageUrl:status==='성공'?imageURL(row.imageUrl,aid):''});
 }
 return {next,results};
}
function directoryRequests(people){
 const accounts=[],results=[],groups=new Map();
 for(const p of people){
  if(!text(p.soop)){results.push({name:p.name,status:'실패',detail:'SOOP 계정 ID 또는 방송국 주소가 없습니다.'});continue;}
  try{const aid=account(p.soop);if(!groups.has(aid))groups.set(aid,[]);groups.get(aid).push(p);}catch(e){results.push({name:p.name,status:'실패',detail:e.message});}
 }
 for(const [aid,items] of groups){
  if(items.length!==1){for(const p of items)results.push({name:p.name,status:'중복',detail:'같은 SOOP ID가 여러 모험가에 연결되어 있습니다. 수동 확인 필요'});continue;}
  const p=items[0];accounts.push({accountId:aid,stationUrl:'https://www.sooplive.com/station/'+aid,requested:{nickname:true,profileImage:!p.image,live:{status:true,title:true,thumbnail:true,viewerCount:true,category:true}},preserveExistingImage:Boolean(p.image),preserveDisplayName:true});
  results.push({name:p.name,status:'성공',detail:aid+' · 프로필/닉네임/LIVE 조회 대상 준비 · 실제 API 조회 아님'});
 }
 return {request:{schema:'wapobook-soop-directory-requests-v1',accounts},results};
}
const api={account,imageURL,plan,profilePlan,directoryRequests,CLASSES,RACES,ROLES};root.WapoImport=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
