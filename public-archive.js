/* Opt-in shared data read, without deleting local records or overwriting storage. */
let publicArchiveStatus={enabled:false,revision:null,error:null};
function mergePublicArchive(local,remote){
 const result=structuredClone(local),join=(a,b)=>{const rows=new Map((a||[]).map(r=>[r.id,structuredClone(r)]));for(const r of b||[]){const old=rows.get(r.id)||{},merged={...old,...structuredClone(r)};if(old.image&&!r.image)merged.image=old.image;if(r.characters)merged.characters=join(old.characters,r.characters);if(r.guildHistory){const hs=new Map();for(const h of [...(old.guildHistory||[]),...r.guildHistory]){const k=h.changeId||JSON.stringify([h.guildId,h.recordedAt,h.restores]);hs.set(k,{...(hs.get(k)||{}),...h});}merged.guildHistory=[...hs.values()];}rows.set(r.id,merged);}return [...rows.values()];};
 for(const key of ['people','guilds','events','chronicle'])if(Array.isArray(remote[key]))result[key]=join(local[key],remote[key]);
 if(Array.isArray(remote.slots)&&remote.slots.length===20)result.slots=remote.slots.slice();
 if('featuredEvent' in remote)result.featuredEvent=remote.featuredEvent;
 result.settings={...result.settings,...remote.settings};return result;
}
async function loadPublishedArchive(){
 try{
  const m=await fetch('data/publication-manifest.json',{cache:'no-store'});if(!m.ok)return;const manifest=await m.json();
  if(manifest.schema!=='wapobook-publication-manifest-v1'||manifest.enabled!==true)return;
  if(manifest.source!=='data/published-archive.json')throw Error('invalid_public_source');
  const r=await fetch(manifest.source,{cache:'no-store'});if(!r.ok)throw Error('public_data_unavailable');const body=await r.json();
  if(body.schema!=='wapobook-public-archive-v1'||!body.revision||!Array.isArray(body.archive?.people)||!Array.isArray(body.archive?.guilds))throw Error('invalid_public_archive');
  if(publicArchiveStatus.revision===body.revision)return;
  if(route().split('?')[0]==='/admin'&&(document.getElementById('editForm')||adminImportBusy))return;
  data=mergePublicArchive(data,body.archive);publicArchiveStatus={enabled:true,revision:body.revision,error:null};render();
 }catch{publicArchiveStatus.error='공용 데이터 갱신 실패 · 기존 데이터 유지';}
}
loadPublishedArchive();

setInterval(()=>{if(publicArchiveStatus.enabled&&document.visibilityState==='visible')loadPublishedArchive();},60000);
