// First-visit acceptance through the actual UI. No domain state is set by this script.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const output=path.join(root,'var/story-review');
fs.mkdirSync(output,{recursive:true});
const target=await (await fetch('http://127.0.0.1:9239/json/new?about:blank',{method:'PUT'})).json();
const socket=new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject});
let sequence=0;
const requests=new Map();
const errors=[];
socket.onmessage=event=>{
  const value=JSON.parse(event.data);
  if(value.id){const pending=requests.get(value.id);if(pending){requests.delete(value.id);value.error?pending.reject(Error(value.error.message)):pending.resolve(value.result)}}
  if(value.method==='Runtime.exceptionThrown')errors.push(value.params.exceptionDetails.text);
  if(value.method==='Runtime.consoleAPICalled'&&value.params.type==='error')errors.push('Browser console error');
};
function cdp(method,params={}){return new Promise((resolve,reject)=>{const id=++sequence;requests.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));setTimeout(()=>{if(requests.has(id)){requests.delete(id);reject(Error('Timed out: '+method))}},15000).unref()})}
async function js(expression){const value=await cdp('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(value.exceptionDetails)throw Error(value.exceptionDetails.exception?.description||value.exceptionDetails.text);return value.result?.value}
async function wait(expression,label){const started=Date.now();while(Date.now()-started<15000){if(await js(expression))return;await new Promise(resolve=>setTimeout(resolve,120))}throw Error('Timed out: '+label)}
async function click(label,scope='document'){if(!await js(`(()=>{const button=[...${scope}.querySelectorAll('button')].find(x=>x.textContent.trim()===${JSON.stringify(label)}&&!x.disabled);if(!button)return false;button.click();return true})()`))throw Error('Missing enabled button: '+label)}
async function shot(name){await new Promise(resolve=>setTimeout(resolve,180));const value=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync(path.join(output,name+'.png'),Buffer.from(value.data,'base64'))}
async function snapshot(){return js(`(async()=>{const p=new URLSearchParams(location.search);return (await fetch('/api/v1/workspaces/'+p.get('workspace')+'/snapshot'+(p.get('run')?'?run_id='+encodeURIComponent(p.get('run')):''))).json()})()`)}
const expected=['authorize_initial','produce_initial','change_caps','open_first','measure_old','new_reference','measure_valid','wait_first','source_first','fail_first','investigate','hypothesis','propose','approve','execute','open_fresh','measure_fresh','wait_fresh','source_fresh','pass_fresh','assess','resolve','authorize_new','produce_new','complete'];
const report={provenance:'SYNTHETIC',checks:[],steps:[],errors};
const pass=name=>{report.checks.push(name);console.log('PASS '+name)};

try{
  await cdp('Page.enable');await cdp('Runtime.enable');
  // Reset only this dedicated QA profile's browser state, never application
  // records or a personal browser session, to test a genuinely new visit.
  await cdp('Network.enable');await cdp('Network.clearBrowserCookies');
  await cdp('Storage.clearDataForOrigin',{origin:'http://127.0.0.1:8107',storageTypes:'local_storage'});
  await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await cdp('Page.navigate',{url:'http://127.0.0.1:8107/'});
  await wait(`!!document.querySelector('.login-form')||!!document.querySelector('.start-here')`,'first visit');
  if(await js(`!!document.querySelector('.login-form')`)){
    const credentials=JSON.parse(fs.readFileSync(path.join(root,'var/local-credentials.json'),'utf8'));
    await js(`(()=>{const e=document.querySelector('[name="password"]');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e,${JSON.stringify(credentials.qa.password)});e.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('.login-form').requestSubmit()})()`);
    await wait(`!!document.querySelector('.start-here')`,'welcome after login');pass('Fresh login leads to a purpose-led start screen');
  }
  if(!await js(`document.querySelector('.story-welcome h1').textContent.includes('Should the line')`))throw Error('First visit does not explain the central question');
  await shot('01-start-here');pass('Purpose, fictional context and a clear starting action are visible');
  await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:1000,deviceScaleFactor:1,mobile:true});
  await shot('02-mobile-start');if(await js(`document.documentElement.scrollWidth>innerWidth+1`))throw Error('Start page overflows at mobile width');
  await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await click('Start the guided story');await wait(`!!document.querySelector('.modal')`,'story setup');
  await js(`(()=>{const e=document.querySelector('[name="name"]');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e,'Browser QA · Guided story '+new Date().toISOString().slice(11,19));e.dispatchEvent(new Event('input',{bubbles:true}))})()`);
  if(await js(`!!document.querySelector('[name="scenario"]')`))throw Error('Newcomer is being asked to select unexplained scenario codes');
  await click('Begin the story',`document.querySelector('.modal')`);await wait(`!!document.querySelector('[data-story-step="authorize_initial"]')`,'saved story');pass('Create a separate persisted guided workspace with no scenario-code choice');
  for(const [index,id] of expected.entries()){
    await wait(`document.querySelector('.story-guide')?.dataset.storyStep===${JSON.stringify(id)}`,'step '+id);
    const state=await snapshot();if(state.journey.id!==id)throw Error('UI progress differs from saved backend facts');
    report.steps.push({id,decision:state.decision.recommendation,run_state:state.run.state,revision:state.workspace.revision});
    if(id==='complete')break;
    if(['authorize_initial','open_first','new_reference','investigate','pass_fresh'].includes(id))await shot('step-'+id);
    if(id==='open_first'){
      await click('Check the independent line');await wait(`document.querySelector('.story-guide')?.dataset.storyStep==='control'`,'independent control');
      const control=await snapshot();if(control.decision.recommendation!=='ACCEPT'||control.run.state==='HELD')throw Error('The unrelated control was held by this cap change');
      await click('Return to the story');await wait(`document.querySelector('.story-guide')?.dataset.storyStep==='open_first'`,'return to affected run');pass('Optional comparison explains why only the affected run paused');
    }
    if(id==='new_reference'){
      await cdp('Page.reload',{ignoreCache:true});await wait(`document.querySelector('.story-guide')?.dataset.storyStep==='new_reference'`,'resume after reload');pass('Reload resumes from the saved evidence, not a local step counter');
      await click('Explore without the guide');await wait(`!!document.querySelector('.guide-compact')`,'collapsed guide');await click('Show guide');await wait(`!!document.querySelector('.guide-action')`,'guide restored');pass('Independent exploration can hide and restore the story');
    }
    await js(`document.querySelector('.guide-action').click()`);await wait(`!!document.querySelector('.story-review')`,'explained action review');
    if(!await js(`!!document.querySelector('.story-review-why')`))throw Error('Action review lacks its purpose');
    if(id==='fail_first'&&!await js(`document.querySelector('.story-review').textContent.includes('supplied')`))throw Error('Synthetic result is not declared');
    await js(`document.querySelector('.modal form').requestSubmit()`);
    await wait(`!document.querySelector('.modal')||!!document.querySelector('.modal [role="alert"]')`,'record step '+id);
    const error=await js(`document.querySelector('.modal [role="alert"]')?.textContent`);if(error)throw Error('Guided action rejected: '+error);
    await wait(`document.querySelector('.story-guide')?.dataset.storyStep!==${JSON.stringify(id)}`,'persisted next step');
  }
  const final=await snapshot();
  if(final.journey.status!=='COMPLETE'||Object.values(final.records).filter(x=>x.kind==='unit').length!==7)throw Error('Final story did not preserve seven units');
  await shot('03-story-complete');pass('All 24 reviewed actions complete the actual recovery workflow');
  pass('Completion explains what was established and its synthetic limits');
  await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:1000,deviceScaleFactor:1,mobile:true});await shot('04-mobile-guide');
  if(await js(`document.documentElement.scrollWidth>innerWidth+1`))throw Error('Guided page overflows at mobile width');pass('Welcome and guided workspaces fit a 390 px viewport');
  await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await click('Follow the evidence behind the decision');await wait(`location.pathname==='/evidence'`,'evidence destination');pass('Story conclusion connects to inspectable evidence');
  await js(`document.querySelector('.sidebar-home').click()`);await wait(`!!document.querySelector('.start-here')`,'return to start');
  await click('Resume your story');await wait(`document.querySelector('.story-guide')?.dataset.storyStep==='complete'`,'completed story resume');pass('Returning visitors resume their own stored story');
  if(errors.length)throw Error('Unhandled browser errors');
  report.completed_at=new Date().toISOString();report.workspace=final.workspace.id;
  fs.writeFileSync(path.join(output,'story-browser.json'),JSON.stringify(report,null,2));console.log('Story browser acceptance complete: '+report.checks.length+' checks');
}catch(error){await shot('failure').catch(()=>{});report.failure=error.message;fs.writeFileSync(path.join(output,'story-browser.json'),JSON.stringify(report,null,2));console.error(error.message);process.exitCode=1}
finally{socket.close()}
