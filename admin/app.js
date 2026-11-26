'use strict';
const $=id=>document.getElementById(id), key=document.querySelector('meta[name="local-key"]')?.content;
let config={sources:[],manualApps:[]}, published={apps:[]};
const message=text=>$('message').textContent=text;
function el(tag,text,parent){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(parent)parent.append(n);return n;}
function button(text,parent,fn){const b=el('button',text,parent);b.type='button';b.onclick=()=>run(fn);return b;}
async function run(fn){try{await fn();}catch(e){message(e.message);}}
async function api(path,body){if(!key)throw Error('저장·서버 조회·업로드는 내 컴퓨터 관리 화면에서 실행하세요. 설정은 내려받아 GitHub에 반영할 수 있습니다.');const r=await fetch('/api/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-Local-Key':key},body:JSON.stringify(body)});const d=await r.json();if(!r.ok)throw Error(d.error||'요청 실패');return d;}
function https(v){const u=new URL(v);if(u.protocol!=='https:'||u.username||u.password)throw Error('공개 HTTPS 주소를 입력하세요.');return v;}
function render(){
 $('count').textContent=published.apps.length;$('apps').replaceChildren();
 for(const a of published.apps){const card=el('article',undefined,$('apps'));card.className='card';const img=el('img',undefined,card);try{img.src=https(a.iconURL);}catch{}img.alt='';img.loading='lazy';el('h3',a.name,card);el('p',a.bundleIdentifier,card);el('p','버전 '+a.versions[0].version,card);const link=el('a','IPA 다운로드',card);link.href=https(a.versions[0].downloadURL);link.rel='noreferrer';}
 if(!published.apps.length)el('p','아직 등록한 앱이 없습니다. 아래에서 선택하거나 직접 등록하세요.',$('apps'));
 $('sources').replaceChildren();
 config.sources.forEach((s,i)=>{const row=el('div',undefined,$('sources'));row.className='row';el('strong',s.name,row);el('p',s.url,row);button('앱 목록 조회',row,()=>browse(s));button('소스 삭제',row,()=>{config.sources.splice(i,1);$('catalog').replaceChildren();render();message('소스를 제거했습니다. 설정을 저장하세요.');});
 for(const [bid,auto] of Object.entries(s.selected)){const lab=el('label',undefined,row);const box=el('input',undefined,lab);box.type='checkbox';box.checked=auto;box.onchange=()=>{s.selected[bid]=box.checked;};lab.append(document.createTextNode(bid+' · 자동 갱신'));button('선택 해제',row,()=>{delete s.selected[bid];$('catalog').replaceChildren();render();});}});
 $('manual').replaceChildren();config.manualApps.forEach((a,i)=>{const row=el('div',undefined,$('manual'));row.className='row';el('span',a.name+' · '+a.bundleIdentifier,row);button('등록 삭제',row,()=>{config.manualApps.splice(i,1);render();});});
}
async function browse(s){message('소스 조회 중…');let data;
 if(key)data=await api('browse',{url:s.url});else{const r=await fetch(s.url,{credentials:'omit',referrerPolicy:'no-referrer'});if(!r.ok)throw Error('소스 응답 '+r.status);data=await r.json();}
 if(!Array.isArray(data.apps))throw Error('apps 배열이 없습니다.');$('catalog').replaceChildren();el('h3',s.name+' · '+data.apps.length+'개 앱',$('catalog'));
 for(const a of data.apps){if(typeof a.bundleIdentifier!=='string')continue;const label=el('label',undefined,$('catalog'));label.className='row';const box=el('input',undefined,label);box.type='checkbox';box.checked=Object.hasOwn(s.selected,a.bundleIdentifier);box.onchange=()=>{if(box.checked)s.selected[a.bundleIdentifier]=true;else delete s.selected[a.bundleIdentifier];render();};label.append(document.createTextNode(a.name+' · '+a.bundleIdentifier));}
 message('원하는 앱을 선택한 뒤 설정을 저장하세요. 조회가 차단되면 로컬 관리 화면을 사용하세요.');}
$('source-form').onsubmit=e=>{e.preventDefault();run(()=>{const address=https($('source-url').value);if(config.sources.some(s=>s.url===address))throw Error('이미 등록된 소스입니다.');config.sources.push({id:'source-'+Date.now(),name:$('source-name').value,url:address,selected:{}});e.target.reset();render();message('소스가 추가되었습니다. 목록 조회 후 선택하세요.');});};
$('manual-form').onsubmit=e=>{e.preventDefault();run(()=>{const d=Object.fromEntries(new FormData(e.target)),app={name:d.name,bundleIdentifier:d.bundleIdentifier,developerName:d.developerName,localizedDescription:d.localizedDescription,iconURL:https(d.iconURL),versions:[{version:d.version,date:new Date().toISOString(),downloadURL:https(d.downloadURL),size:Number(d.size)}]};if(d.buildVersion)app.versions[0].buildVersion=d.buildVersion;addManual(app);e.target.reset();});};
function addManual(app){if(config.manualApps.some(a=>a.bundleIdentifier===app.bundleIdentifier))throw Error('같은 Bundle ID가 직접 등록되어 있습니다. 기존 등록을 삭제한 뒤 추가하세요.');config.manualApps.push(app);render();message('앱을 추가했습니다. 설정을 저장하세요.');}
$('save').onclick=()=>run(async()=>{const r=await api('save',config);published=await(await fetch('source.json?t='+Date.now())).json();render();message(r.message);});
$('refresh').onclick=()=>run(async()=>{const r=await api('refresh',{});published=await(await fetch('source.json?t='+Date.now())).json();render();message(r.message+' 현재 화면에서 편집한 설정은 저장 버튼으로 반영하세요.');});
$('export').onclick=()=>{const u=URL.createObjectURL(new Blob([JSON.stringify(config,null,2)+'\n'],{type:'application/json'}));const a=el('a');a.href=u;a.download='config.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);message('내려받은 config.json을 저장소 루트에 교체하고 commit/push하세요.');};
$('copy').onclick=()=>run(async()=>{await navigator.clipboard.writeText('https://parkace-ipa.github.io/my-ios-source/source.json');message('배포 후 사용할 소스 주소를 복사했습니다.');});
$('upload').onclick=()=>run(async()=>{if(!key)throw Error('Releases 업로드는 내 컴퓨터 관리 화면에서 가능합니다.');const file=$('ipa').files[0];if(!file)throw Error('IPA 파일을 선택하세요.');if(file.size>2_000_000_000)throw Error('2GB 이하의 파일을 선택하세요.');$('upload').disabled=true;message('IPA 분석 및 공개 Release 업로드 중…');try{const r=await fetch('/api/upload',{method:'POST',headers:{'X-Local-Key':key},body:file});const d=await r.json();if(!r.ok)throw Error(d.error);addManual(d.app);message(d.note);}finally{$('upload').disabled=false;}});
run(async()=>{const responses=await Promise.all(['config.json','source.json','status.json'].map(p=>fetch(p+'?t='+Date.now()).then(r=>{if(!r.ok)throw Error('초기 파일 로드 실패');return r.json();})));[config,published]=responses;render();$('mode').textContent=key?'내 컴퓨터 관리 모드 · 공개하려면 ‘저장하고 공개 배포’를 누르세요.':'공개 페이지 · 설정 편집과 내려받기가 가능합니다. 직접 저장·업로드는 내 컴퓨터 관리 모드를 사용하세요.';const st=responses[2];message('마지막 생성: '+new Date(st.updatedAt).toLocaleString('ko-KR')+'\n'+st.messages.filter(m=>!m.ok).map(m=>m.message).join('\n'));});

$('deploy').onclick=()=>run(async()=>{
 const controls=[...document.querySelectorAll('button,input')];
 const disabled=controls.map(n=>n.disabled);
 controls.forEach(n=>n.disabled=true);
 try{
  message('설정 저장 및 GitHub 업로드 중… 잠시 기다려 주세요.');
  const result=await api('deploy',config);
  published=await(await fetch('source.json?t='+Date.now())).json();render();
  const link=$('deploy-link');link.hidden=false;message(result.message);
  for(let attempt=0;attempt<60;attempt++){
   await new Promise(resolve=>setTimeout(resolve,5000));
   const state=await api('deploy-status',{sha:result.sha,startedAt:result.startedAt});
   link.href=state.url;
   if(state.status==='completed'){
    if(state.conclusion==='success'){message('공개 배포가 완료되었습니다. 공개 페이지를 새로고침하세요.');return;}
    throw Error('GitHub 업로드는 완료됐지만 공개 배포가 실패했습니다. ‘배포 진행 보기’에서 확인하세요.');
   }
   message('GitHub 반영 완료 · 공개 페이지 배포 중…');
  }
  message('GitHub 반영은 완료됐습니다. 배포 확인 시간이 초과됐으니 ‘배포 진행 보기’에서 결과를 확인하세요.');
 }finally{controls.forEach((n,i)=>n.disabled=disabled[i]);}
});
