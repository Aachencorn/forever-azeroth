/* Administrator-reviewed XLSX import; uses the existing data object and storage key. */
let adminImportState=null,adminImportBusy=false;
const importOriginalAdmin=admin;
admin=function(){importOriginalAdmin();const side=document.querySelector('.adminSide');if(!side)return;side.insertAdjacentHTML('beforeend',`<button class="${adminTab==='xlsx'?'active':''}" onclick="adminTab='xlsx';render()">엑셀 일괄 등록</button>`);if(adminTab==='xlsx')renderImportPanel();};
function importDownload(name,value){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function renderImportPanel(){
 const node=document.getElementById('adminContent');if(!node||adminTab!=='xlsx')return;
 const st=adminImportState,counts=st?.results.reduce((o,r)=>(o[r.status]=(o[r.status]||0)+1,o),{})||{};
 node.innerHTML=`<div class="importHeading"><h2>엑셀 일괄 등록</h2><a class="btn secondary" href="downloads/wapobook-admin-template.xlsx" download>엑셀 양식 다운로드</a></div>
 <p>길드·모험가·이전 시즌 기록을 한 번에 확인하고, 기존 정보의 빈 항목만 채웁니다. 기존 사진과 데이터는 유지합니다.</p>
 <p class="notice">병합 결과는 현재 브라우저에 저장됩니다. 다른 방문자에게 공개되는 서버 동기화 기능은 아닙니다.</p>
 <div class="adminActions importTools"><label class="btn">엑셀 파일 업로드<input id="adminWorkbook" type="file" accept=".xlsx" onchange="readAdminWorkbook(this.files[0])" ${adminImportBusy?'disabled':''}></label><button class="btn secondary" onclick="downloadProfileRequests()">사진 조회 요청 JSON 다운로드</button><label class="btn secondary">사진 조회 결과 업로드<input id="adminProfiles" type="file" accept=".json" onchange="readProfileReport(this.files[0])" ${adminImportBusy?'disabled':''}></label></div>
 <p class="muted">SOOP 조회는 관리자 승인형 작업으로 분리됩니다. 현재 실조회 5개 검증·API 이용 권한 확인이 완료되지 않아 자동 수집은 비활성 상태입니다. 조회 실패 시 기본 이미지가 유지되며 기존 ‘모험가 → 수정’에서 사진 URL을 수동 등록할 수 있습니다.</p>
 <p><a href="https://github.com/Aachencorn/forever-azeroth/blob/feat/admin-xlsx-soop-profiles/docs/admin-import.md" target="_blank" rel="noopener noreferrer">입력·사진 동기화 안내 ↗</a></p>
 <div id="importMessage" role="status" aria-live="polite">${adminImportBusy?'파일을 읽고 있습니다…':st?esc(st.message):'양식을 작성하고 업로드해 주세요. 업로드만으로 저장되지 않습니다.'}</div>
 ${st?`<div class="importCounts">${Object.entries(counts).map(([k,v])=>`<span>${esc(k)} <b>${v}</b></span>`).join('')}</div><div class="adminActions"><button class="btn" onclick="applyAdminImport()" ${st.applied||!counts['성공']?'disabled':''}>${st.applied?'병합 완료':'성공 항목 병합 승인'}</button><button class="btn secondary" onclick="importDownload('wapobook-import-result.json',adminImportState.results)">검수 결과 다운로드</button><button class="btn ghost" onclick="adminImportState=null;renderImportPanel()">미리보기 닫기</button></div><p class="muted">실패 행은 제외합니다. 승인 시 병합 전 JSON 백업을 내려받습니다. 사진·길드·슬롯·즐겨찾기는 삭제하지 않습니다.</p><div class="importResultScroll"><table class="importResults"><thead><tr><th>시트 / 행</th><th>이름</th><th>상태</th><th>내용</th></tr></thead><tbody>${st.results.slice(0,300).map(r=>`<tr><td>${esc(r.sheet||'프로필')} ${r.row||''}</td><td>${r.imageUrl?`<img class="importProfilePreview" src="${esc(r.imageUrl)}" alt="${esc(r.name)} 프로필 미리보기" loading="lazy" onerror="this.hidden=true">`:""}${esc(r.name)}</td><td><span class="importBadge" data-status="${esc(r.status)}">${esc(r.status)}</span></td><td>${esc(r.detail)}</td></tr>`).join('')}</tbody></table></div>${st.results.length>300?'<p>화면에는 처음 300행을 표시합니다. 전체 검수 결과는 다운로드할 수 있으며 병합은 모든 성공 행에 적용됩니다.</p>':''}`:''}`;
}
async function ensureWorkbookLibrary(){if(window.ExcelJS)return;await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='vendor/exceljs-4.4.0.min.js';s.onload=resolve;s.onerror=()=>{s.remove();reject(Error('엑셀 처리 모듈을 불러오지 못했습니다. 다시 시도해 주세요.'));};document.head.appendChild(s);});}
function workbookCell(cell){
 if(cell.type===ExcelJS.ValueType.Formula||cell.value?.formula||cell.value?.sharedFormula)throw Error('수식 셀은 허용하지 않습니다. 값으로 붙여 넣어 주세요.');
 const v=cell.value;if(v==null)return '';if(v instanceof Date)return v.toISOString().slice(0,10);
 if(typeof v==='object'){if(v.hyperlink)return String(v.text||v.hyperlink);if(v.richText)return v.richText.map(r=>r.text).join('');throw Error('지원하지 않는 셀 형식입니다.');}return String(v).trim();
}
function inspectWorkbookZip(buffer){
 const view=new DataView(buffer);let end=-1;
 for(let i=view.byteLength-22;i>=Math.max(0,view.byteLength-65557);i--)if(view.getUint32(i,true)===0x06054b50){end=i;break;}
 if(end<0)throw Error('손상되었거나 지원하지 않는 엑셀 압축 형식입니다.');
 const count=view.getUint16(end+10,true),offset=view.getUint32(end+16,true);if(count===65535||count>10000||offset>=end)throw Error('엑셀 파일의 구조가 너무 큽니다.');
 let position=offset,total=0;const decoder=new TextDecoder();
 for(let i=0;i<count;i++){
  if(position+46>end||view.getUint32(position,true)!==0x02014b50)throw Error('엑셀 압축 구조를 확인할 수 없습니다.');
  total+=view.getUint32(position+24,true);const size=view.getUint16(position+28,true),extra=view.getUint16(position+30,true),comment=view.getUint16(position+32,true);
  if(total>80*1024*1024||position+46+size+extra+comment>end)throw Error('압축 해제 크기가 너무 크거나 손상된 파일입니다.');
  const name=decoder.decode(new Uint8Array(buffer,position+46,size));if(/vbaProject|embeddings\//i.test(name)||view.getUint16(position+8,true)&1)throw Error('매크로·포함 개체·암호화 파일은 허용하지 않습니다.');
  position+=46+size+extra+comment;
 }
}
async function readAdminWorkbook(file){
 if(!file||adminImportBusy)return;adminImportBusy=true;adminImportState=null;renderImportPanel();
 try{
  if(!/\.xlsx$/i.test(file.name)||file.size>20*1024*1024)throw Error('.xlsx 파일(최대 20MB)을 선택하세요.');
  const buffer=await file.arrayBuffer();inspectWorkbookZip(buffer);await ensureWorkbookLibrary();const workbook=new ExcelJS.Workbook();await workbook.xlsx.load(buffer,{ignoreNodes:['tableParts','drawing','extLst']});
  const required={'모험가 정보':['버튜버명','캐릭터명','레벨','종족','직업','전문화','역할','소속 길드','SOOP 방송국 주소','대표 캐릭터'],'길드 정보':['길드명','길드장','전체 길드원 수','길드 소개','최종 확인일'],'이전 시즌 참여 기록':['버튜버명','참여 여부','당시 레벨','당시 직업','당시 전문화','확인된 레이드 (쉼표 구분)']};
  const sheets={};
  for(const [name,headers] of Object.entries(required)){
   const ws=workbook.getWorksheet(name);if(!ws)throw Error(name+' 시트가 없습니다. 전용 양식을 사용하세요.');
   const actual=ws.getRow(1).values.slice(1).map(v=>String(v||'').trim());if(headers.some(h=>!actual.includes(h))||new Set(actual).size!==actual.length)throw Error(name+' 시트의 열 이름이 변경되었거나 중복되었습니다.');
   sheets[name]=[];ws.eachRow((row,index)=>{if(index===1)return;const record={_row:index};headers.forEach(h=>record[h]=workbookCell(row.getCell(actual.indexOf(h)+1)));if(headers.some(h=>record[h]))sheets[name].push(record);});
  }
  const snapshot=JSON.stringify(data),planned=WapoImport.plan(data,sheets);adminImportState={...planned,snapshot,storageSnapshot:localStorage.getItem(KEY),message:`${file.name} · ${planned.results.length}행 검수 완료. 아직 저장되지 않았습니다.`,applied:false};
 }catch(e){adminImportState={results:[],message:'파일 확인 실패: '+e.message,applied:false};}
 finally{adminImportBusy=false;renderImportPanel();}
}
async function readProfileReport(file){
 if(!file||adminImportBusy)return;try{if(file.size>20*1024*1024)throw Error('파일이 너무 큽니다.');const report=JSON.parse(await file.text());const snapshot=JSON.stringify(data),planned=WapoImport.profilePlan(data,report);adminImportState={...planned,snapshot,storageSnapshot:localStorage.getItem(KEY),message:'프로필 연결 결과를 검토하세요. 기존 사진은 유지되며 승인 전에는 저장하지 않습니다.',applied:false};}catch(e){adminImportState={results:[],message:'사진 결과 확인 실패: '+e.message};}renderImportPanel();
}
function applyAdminImport(){
 const st=adminImportState;if(!st?.next||st.applied||!st.results.some(r=>r.status==='성공'))return;
 if(JSON.stringify(data)!==st.snapshot||localStorage.getItem(KEY)!==st.storageSnapshot){alert('미리보기 이후 데이터가 변경되었습니다. 파일을 다시 업로드해 주세요.');return;}
 if(!confirm('성공 항목을 기존 데이터에 병합할까요? 기존 값은 유지하며, 실패 행은 제외합니다.'))return;
 importDownload('wapobook-before-import-'+new Date().toISOString().slice(0,10)+'.json',data);
 const previous=data;try{data=st.next;save();st.applied=true;st.message='병합 완료. 현재 브라우저의 모험가 도감·길드 도감에 반영되었습니다.';}catch(e){data=previous;alert('저장하지 못했습니다. 기존 데이터는 유지됩니다. 브라우저 저장 공간을 확인하세요.');}renderImportPanel();
}
function downloadProfileRequests(){
 const rows=[],seen=new Set(),errors=[];
 for(const p of data.people){if(p.image||!p.soop)continue;try{const id=WapoImport.account(p.soop);if(id&&!seen.has(id)){rows.push({accountId:id,stationUrl:'https://www.sooplive.com/station/'+id});seen.add(id);}}catch{errors.push(p.name);}}
 if(!rows.length){alert('사진이 없고 SOOP 주소가 등록된 모험가가 없습니다. 먼저 엑셀을 병합해 주세요.');return;}
 importDownload('wapobook-profile-requests.json',{schema:'wapobook-soop-requests-v1',accounts:rows});if(errors.length)alert('잘못된 방송국 URL은 제외했습니다: '+errors.join(', '));
}
if(route().split('?')[0]==='/admin')render();
