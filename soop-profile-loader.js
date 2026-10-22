/* Public profile image linking, independent of broadcast status. No OAuth/API calls. */
(function(root){
'use strict';
function url(id){id=String(id||'').toLowerCase();if(!/^[a-z0-9_]{2,25}$/.test(id))throw Error('잘못된 SOOP 계정 ID');return 'https://profile.img.sooplive.co.kr/LOGO/'+id.slice(0,2)+'/'+id+'/'+id+'.jpg';}
function probeImage(src,signal){return new Promise(resolve=>{
 const img=new Image();let timer;const done=ok=>{clearTimeout(timer);img.onload=img.onerror=null;signal?.removeEventListener('abort',abort);if(!ok)img.removeAttribute('src');resolve(ok);};
 const abort=()=>done(false);if(signal?.aborted)return resolve(false);
 img.onload=()=>done(img.naturalWidth>1&&img.naturalHeight>1);img.onerror=()=>done(false);signal?.addEventListener('abort',abort,{once:true});timer=setTimeout(()=>done(false),8000);img.referrerPolicy='no-referrer';img.src=src;
 });}
async function resolve(id,{probe=probeImage,signal,cache={},now=Date.now,delay=ms=>new Promise(r=>setTimeout(r,ms))}={}){
 const imageUrl=url(id),stamp=now(),entry=Object.hasOwn(cache,id)?cache[id]:null;
 if(entry&&entry.url===imageUrl&&stamp>=entry.at&&stamp-entry.at<86400000)return {accountId:id,status:'success',sourceType:'station-profile',imageUrl,cached:true};
 for(let attempt=0;attempt<2;attempt++){
  if(signal?.aborted)return {accountId:id,status:'failed',message:'조회 취소'};
  if(attempt)await delay(2000);
  if(signal?.aborted)return {accountId:id,status:'failed',message:'조회 취소'};
  if(await probe(imageUrl,signal)){cache[id]={url:imageUrl,at:now()};return {accountId:id,status:'success',sourceType:'station-profile',imageUrl};}
 }
 return {accountId:id,status:'failed',message:'프로필 이미지 로드 실패 또는 접근 제한 · 기본 이미지 유지 / 수동 등록 가능'};
}
const api={url,resolve};root.SoopProfileLoader=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
