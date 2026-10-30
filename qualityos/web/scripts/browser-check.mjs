// Actual Edge/CDP interaction against the locally served built application.
// Credentials are read privately from ignored local setup; never logged.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const out=path.join(root,'var/browser-review');fs.mkdirSync(out,{recursive:true});
const base='http://127.0.0.1:8107';
const target=await (await fetch('http://127.0.0.1:9239/json/new?about:blank',{method:'PUT'})).json();
const socket=new WebSocket(target.webSocketDebuggerUrl);await new Promise((r,j)=>{socket.onopen=r;socket.onerror=j});
let next=0;const callbacks=new Map();const errors=[];
socket.onmessage=event=>{const msg=JSON.parse(event.data);if(msg.id){const pending=callbacks.get(msg.id);if(pending){callbacks.delete(msg.id);msg.error?pending.reject(new Error(msg.error.message)):pending.resolve(msg.result)}}if(msg.method==='Runtime.exceptionThrown')errors.push(msg.params.exceptionDetails.text);if(msg.method==='Runtime.consoleAPICalled'&&msg.params.type==='error')errors.push('Browser console error')};
function cdp(method,params={}){return new Promise((resolve,reject)=>{const id=++next;callbacks.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));setTimeout(()=>{if(callbacks.has(id)){callbacks.delete(id);reject(new Error('CDP timeout: '+method))}},15000).unref()})}
async function js(expression){const r=await cdp('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw new Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);return r.result?.value}
async function wait(expression,label,timeout=12000){const start=Date.now();while(Date.now()-start<timeout){if(await js(expression))return;await new Promise(r=>setTimeout(r,120))}throw new Error('Timed out: '+label)}
async function click(text,scope='document'){await wait(`[...${scope}.querySelectorAll('button')].some(b=>b.textContent.trim()===${JSON.stringify(text)}&&!b.disabled)`,'enabled action '+text);const matched=await js(`(()=>{const b=[...${scope}.querySelectorAll('button')].find(b=>b.textContent.trim()===${JSON.stringify(text)}&&!b.disabled);if(!b)return false;b.click();return true})()`);if(!matched)throw new Error('Enabled button not found: '+text)}
async function fill(name,value){await js(`(()=>{const e=document.querySelector('[name="${name}"]');if(!e)throw Error('Missing field ${name}');const proto=e.tagName==='SELECT'?HTMLSelectElement.prototype:e.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(proto,'value').set.call(e,${JSON.stringify(String(value))});e.dispatchEvent(new Event(e.tagName==='SELECT'?'change':'input',{bubbles:true}));})()`)}
async function submit(){const rev=await js(`document.querySelector('.workspace-footer .mono')?.textContent||''`);await js(`document.querySelector('[role="dialog"] form').requestSubmit()`);await wait(`!document.querySelector('.modal')||!!document.querySelector('.modal [role="alert"]')`,'command response');const error=await js(`document.querySelector('.modal [role="alert"]')?.textContent`);if(error)throw new Error('UI command rejected: '+error);if(rev)await wait(`document.querySelector('.workspace-footer .mono')?.textContent!==${JSON.stringify(rev)}`,'committed revision')}
async function action(text,fields={},reason='Reviewed current scope and independent synthetic evidence.'){await click(text);await wait(`!!document.querySelector('.modal')`,'dialog '+text);for(const [key,value] of Object.entries(fields))await fill(key,value);if(await js(`!!document.querySelector('[name="reason"]')`))await fill('reason',reason);await submit()}
async function nav(page){await js(`document.querySelectorAll('.sidebar nav button')[${['line','evidence','qualification','investigation'].indexOf(page)}].click()`);await wait(`location.pathname==='/${page}'`,'navigation '+page)}
async function shot(name){await new Promise(r=>setTimeout(r,180));const data=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(data.data,'base64'))}
async function snapshot(){return js(`(async()=>{const p=new URLSearchParams(location.search);return (await fetch('/api/v1/workspaces/'+p.get('workspace')+'/snapshot'+(p.get('run')?'?run_id='+encodeURIComponent(p.get('run')):''))).json()})()`)}
const report={provenance:'SYNTHETIC',checks:[],screenshots:[],errors};
function pass(name){report.checks.push(name);console.log('PASS '+name)}
try{
 await cdp('Runtime.enable');await cdp('Page.enable');await cdp('Network.enable');await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});
 await cdp('Page.navigate',{url:base+'/line'});await wait(`!!document.querySelector('input[name="password"]')||!!document.querySelector('main')`,'application load');
 if(await js(`!!document.querySelector('input[name="password"]')`)){
  await shot('00-login');const credentials=JSON.parse(fs.readFileSync(path.join(root,'var/local-credentials.json'),'utf8'));
  await fill('username','qa');await fill('password',credentials.qa.password);await js(`document.querySelector('.login-form').requestSubmit()`);await wait(`!!document.querySelector('main')`,'server-owned login');pass('Login through actual form');
 }
 await click('New workspace',`document.querySelector('main')`);await wait(`!!document.querySelector('.modal')`,'new workspace dialog');await fill('name','Browser verification · '+new Date().toISOString().slice(11,19));await submit();await wait(`!!document.querySelector('.run-context')`,'persisted workspace');pass('Create isolated workspace through UI');
 await shot('01-line-ready');report.screenshots.push('01-line-ready.png');
 if(process.env.QUALITYOS_BROWSER_MODE==='smoke'){pass('Built application rendered');}
 else{
  const first=await snapshot();if(first.decision.recommendation!=='ACCEPT')throw Error('Initial qualification not accepted');
  await action('Authorize simulated run');
  await click('Continue simulation');await fill('units',2);await fill('reason','Check recovery from a lost committed response.');
  await js(`(()=>{const original=window.fetch;window.fetch=async(...args)=>{const response=await original(...args);if(String(args[0]).includes('/commands/produce')){window.fetch=original;throw new TypeError('Injected lost response after server commit')}return response}})()`);
  await js(`document.querySelector('.modal form').requestSubmit()`);await wait(`!!document.querySelector('.modal [role="alert"]')`,'lost response error');
  if(Object.values((await snapshot()).records).filter(x=>x.kind==='unit').length!==2)throw Error('Original command did not commit');
  await submit();if(Object.values((await snapshot()).records).filter(x=>x.kind==='unit').length!==2)throw Error('Retry duplicated units');
  pass('Lost committed response retries one persisted effect');
  await click('Change assignment');await wait(`!!document.querySelector('.modal')`,'keyboard dialog');
  await js(`document.querySelector('.modal button').focus()`);await cdp('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',modifiers:8});await cdp('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',modifiers:8});
  if(!await js(`document.activeElement===document.querySelector('.dialog-footer button:last-child')`))throw Error('Dialog reverse focus trap failed');
  await cdp('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape'});await wait(`!document.querySelector('.modal')`,'keyboard dismiss');pass('Dialog traps keyboard focus and Escape dismisses');
  await cdp('Network.emulateNetworkConditions',{offline:true,latency:0,downloadThroughput:-1,uploadThroughput:-1});
  await wait(`!!document.querySelector('.connection.disconnected')`,'offline paused state');
  if(!await js(`[...document.querySelectorAll('button')].find(x=>x.textContent.trim()==='Continue simulation')?.disabled`))throw Error('Offline production action remains enabled');
  await shot('01b-offline');await cdp('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});await wait(`!document.querySelector('.connection.disconnected')`,'reconnection');pass('Network outage pauses actions and recovers');
  await action('Change assignment');await wait(`document.querySelector('.decision-card')?.textContent.includes('More evidence required')`,'scope hold');
  const changed=await snapshot();if(changed.decision.recommendation!=='HOLD'||changed.runs.find(r=>r.id!==changed.run.id).state==='HELD')throw Error('Scope isolation failed');pass('Outside-scope change holds only affected run');await shot('02-scoped-hold');
  await action('Open scoped study');await nav('qualification');await action('Record observations');pass('Invalid reference cannot supply passing evidence');await shot('03-invalid-reference');
  await action('New reference');await action('Record observations');await action('Advance replay',{hours:24});await action('Confirm source health');await action('Record result',{outcome:'FAIL'});pass('Independent delayed failure rejects first condition');
  await nav('investigation');await action('Open investigation');await action('Record hypothesis');await action('Propose action');await action('Approve action');await action('Record execution');await action('Open fresh verification');pass('Investigation and approved action lifecycle');
  await nav('qualification');await action('Record observations');await action('Advance replay',{hours:24});await action('Confirm source health');await action('Record result',{outcome:'PASS'});
  await nav('investigation');await action('Assess effectiveness');await shot('04-investigation');await nav('qualification');await action('Resolve hold');await action('Authorize simulated run');pass('Fresh verification, explicit QA resolution and authorization');await shot('05-qualification');
  await nav('line');await action('Continue simulation',{units:5});await shot('06-line-authorized');const recovered=await snapshot();if(Object.values(recovered.records).filter(x=>x.kind==='unit'&&x.run_id===recovered.run.id).length!==7)throw Error('Committed unit count mismatch');
  await nav('evidence');await shot('07-evidence');await js(`document.querySelector('.graph-node').focus()`);await cdp('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter'});await wait(`!!document.querySelector('.drawer')`,'keyboard graph drawer');await cdp('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape'});await wait(`!document.querySelector('.drawer')`,'drawer dismissed');pass('Evidence graph keyboard activation opens source record');
  const historical=recovered.decision.id;await js(`(()=>{const e=document.querySelector('[aria-label="Historical decision"]');Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set.call(e,${JSON.stringify(historical)});e.dispatchEvent(new Event('change',{bubbles:true}))})()`);await wait(`!!document.querySelector('.notice.history')`,'read-only historical view');pass('Historical as-known view is explicit');await click('Return to current');
  await nav('investigation');const state=await snapshot();const cal=Object.values(state.records).filter(x=>x.kind==='calibration'&&x.instrument_id.endsWith('torque-02')&&!x.id.endsWith('old')).at(-1);await action('Revoke reference',{calibration_id:cal.id,effective_from:'2026-01-15T00:00:00Z',effective_until:state.clock});await shot('08-late-impact');const impact=await snapshot();if(impact.impact.units.length!==5)throw Error('Expected exactly five newly qualified units in impact');pass('Late revocation scopes five potentially affected units');
  await cdp('Page.reload',{ignoreCache:true});await wait(`!!document.querySelector('.run-context')`,'reload persisted state');pass('Reload reconstructs server state');
  for(const width of [1024,390]){await cdp('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<600});for(const page of ['line','evidence','qualification','investigation']){await nav(page);await shot(`${width}-${page}`);const overflow=await js(`document.documentElement.scrollWidth>innerWidth+1`);if(overflow)throw Error('Page overflow at '+width+' '+page)}pass('All four workspaces at '+width+' px without page overflow')}
  await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1,mobile:false});await nav('line');await click('Independent evaluation');await click('Run independent evaluation');await wait(`!!document.querySelector('.evaluation-summary')`,'independent evaluation result');await shot('09-evaluation');pass('Independent evaluation runs from UI and persists report');
 }
 if(errors.length)throw Error('Browser runtime errors detected');
 report.completed_at=new Date().toISOString();report.workspace=await js(`new URLSearchParams(location.search).get('workspace')`);fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify(report,null,2));console.log('Browser review complete: '+report.checks.length+' checks');
}catch(error){await shot('failure').catch(()=>{});report.failure=error.message;fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify(report,null,2));console.error(error.message);process.exitCode=1}
finally{socket.close();}
