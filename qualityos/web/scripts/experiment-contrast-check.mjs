// Deterministic computed-style contrast screen, not a complete WCAG audit.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const storyMode=true;
const session=JSON.parse(fs.readFileSync(path.join(root,'var/qa-session.json'),'utf8'));
if(session.base_url!=='http://127.0.0.1:8112')throw Error('Isolated review server required');
const storyWorkspace=null;
const targets=await (await fetch('http://127.0.0.1:9239/json/list')).json();
const target=targets.find(t=>t.type==='page'&&t.url.startsWith('http://127.0.0.1:8112/')&&(!storyWorkspace||t.url.includes(storyWorkspace)));
if(!target)throw Error('Open the local app in the dedicated QA browser first');
const socket=new WebSocket(target.webSocketDebuggerUrl);await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j});
let id=0;const waiting=new Map();socket.onmessage=e=>{const msg=JSON.parse(e.data);if(msg.id){waiting.get(msg.id)?.(msg.result);waiting.delete(msg.id)}};
const call=(method,params={})=>new Promise(resolve=>{const n=++id;waiting.set(n,resolve);socket.send(JSON.stringify({id:n,method,params}))});
async function evaluate(expression){const result=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});return result.result?.value}
const reports=[];
try{
await call('Page.reload',{ignoreCache:true});await new Promise(r=>setTimeout(r,700));
for(const page of storyMode?['start','line','evidence','qualification','investigation']:['line','evidence','qualification','investigation']){
 await evaluate(page==='start'?`document.querySelector('.sidebar-home').click()`:`document.querySelector('.sidebar nav [data-page="${page}"]').click()`);
 await new Promise(r=>setTimeout(r,350));
 const scan=await evaluate(`(()=>{
 const rgb=s=>{const m=s.match(/[\\d.]+/g);return m?m.slice(0,3).map(Number):[0,0,0]};
 const luminance=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
 const bg=e=>{while(e){const s=getComputedStyle(e);if(s.backgroundColor!=='rgba(0, 0, 0, 0)'&&s.backgroundColor!=='transparent')return rgb(s.backgroundColor);e=e.parentElement}return [245,244,239]};
 const tree=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n,checked=0;const failures=[];const seen=new Set();
 while(n=tree.nextNode()){const e=n.parentElement;if(!n.textContent.trim()||!e||seen.has(e)||e.closest('button:disabled,[aria-hidden="true"],script,style'))continue;seen.add(e);const s=getComputedStyle(e);if(!e.getClientRects().length||s.visibility==='hidden'||s.display==='none')continue;const foreground=e instanceof SVGElement?rgb(s.fill):rgb(s.color);const ls=[luminance(foreground),luminance(bg(e))].sort((a,b)=>b-a);const ratio=(ls[0]+.05)/(ls[1]+.05);const large=parseFloat(s.fontSize)>=24||(parseFloat(s.fontSize)>=18.66&&Number(s.fontWeight)>=700);checked++;if(ratio<(large?3:4.5))failures.push({tag:e.tagName,classes:e.className.baseVal??e.className,text:n.textContent.trim().slice(0,70),color:s.color,background:bg(e),ratio:Math.round(ratio*100)/100,font:s.fontSize})}
 return {checked,failures};})()`);
 reports.push({page,...scan});
}
const result={created_at:new Date().toISOString(),basis:'Computed solid foreground/background colors; excludes disabled and aria-hidden controls; not a complete accessibility certification',reports};
fs.writeFileSync(path.join(root,'var/experiment-review/contrast.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(reports.map(r=>({page:r.page,checked:r.checked,failures:r.failures.length,examples:r.failures.slice(0,5)})),null,2));
if(reports.some(r=>r.failures.length))process.exitCode=1;
}finally{socket.close()}
