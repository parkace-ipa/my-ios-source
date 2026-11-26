'use strict';
const apps=document.getElementById('apps'), message=document.getElementById('message');
function el(tag,text,parent){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(parent)parent.append(node);return node;}
function https(value){const url=new URL(value);if(url.protocol!=='https:'||url.username||url.password)throw Error('사용할 수 없는 주소입니다.');return url.href;}
async function loadApps(){
 try{
  const response=await fetch('source.json',{cache:'no-cache'});
  if(!response.ok)throw Error('앱 목록을 불러오지 못했습니다. 잠시 후 새로고침해 주세요.');
  const source=await response.json();
  if(!Array.isArray(source.apps))throw Error('앱 목록을 표시할 수 없습니다.');
  document.getElementById('count').textContent=source.apps.length+'개';
  message.textContent=source.apps.length?'':'아직 공개된 앱이 없습니다.';
  for(const app of source.apps){
   const card=el('article',undefined,apps);card.className='card';
   const image=el('img',undefined,card);image.alt='';image.loading='lazy';image.referrerPolicy='no-referrer';image.src='icon.png';
   try{image.src=https(app.iconURL);}catch{}
   image.onerror=()=>{image.onerror=null;image.src='icon.png';};
   const info=el('div',undefined,card);info.className='info';
   el('h3',app.name,info);
   const version=app.versions?.[0];
   if(!version){el('p','다운로드 준비 중',info);continue;}
   el('p','버전 '+version.version+(Number.isFinite(version.size)?' · '+(version.size/1048576).toFixed(1)+' MB':''),info);
   try{const address=https(version.downloadURL);const link=el('a','다운로드',card);link.href=address;link.rel='noreferrer nofollow';link.className='download';link.setAttribute('aria-label',app.name+' IPA 다운로드');}catch{el('p','다운로드 주소를 사용할 수 없습니다.',info);}
  }
 }catch(error){message.textContent=error.message;}
}
loadApps();
