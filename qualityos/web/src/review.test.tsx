import {afterEach,describe,it,expect,vi} from 'vitest';
import {renderToStaticMarkup} from 'react-dom/server';
import {api,ApiError,qaRequired,definiteCommandFailure} from './api';
import {ChangeDecision} from './ChangeDecision';
import {evidenceLabel} from './decisionLabels';
import type {Snapshot,PackagingTask} from './api';

afterEach(()=>vi.unstubAllGlobals());
describe('independent review error and state boundaries',()=>{
 it('keeps an HTML proxy/server error from becoming a JSON parse error',async()=>{
  vi.stubGlobal('document',{cookie:''});vi.stubGlobal('fetch',vi.fn(async()=>new Response('<html>private error trace</html>',{status:500})));
  try{await api('/workspaces');throw Error('Expected failure')}catch(e){expect(e).toBeInstanceOf(ApiError);expect((e as ApiError).code).toBe('UNEXPECTED_SERVER_RESPONSE');expect((e as Error).message).not.toContain('private error trace')}
 });
 it('requires QA for recording-error correction and genuine-study determination',()=>{
  expect(qaRequired('correct_evidence')).toBe(true);expect(qaRequired('disposition_study')).toBe(true);
 });
 it('retains the retry key when an opaque error cannot establish whether the command committed',()=>{
  expect(definiteCommandFailure(new ApiError(500,{code:'INTERNAL_ERROR'}))).toBe(false);
  expect(definiteCommandFailure(new ApiError(502,{code:'UNEXPECTED_SERVER_RESPONSE'}))).toBe(false);
  expect(definiteCommandFailure(new ApiError(409,{code:'STALE_CONTEXT'}))).toBe(true);
  expect(definiteCommandFailure(new TypeError('network response lost'))).toBe(false);
 });
 it('does not present passing evidence with an active pause as production permission',()=>{
  const task:PackagingTask={product:'Fictional lotion',quantity:'100 g',previous_study:{id:'old',label:'Old test',date:'2026-01-14T08:00:00Z',applies:false,recorded_results:3},rows:[],changed:true,physical_context:'Changed cap condition',coverage_reason:'Old tests cover C01',affected_scope:{run:'Run A',line:'Line A',planned_units:20,description:'Only selected run'},title:'Tests complete; production still awaits QA',evidence:'ACCEPT',permission_granted:false,next:{operation:'resolve_hold',label:'Review the production pause',why:'QA review remains',payload:{},qa_required:true},hold_reason:'Pause unresolved',containment_scope:'Separate historical population'};
  const s={packaging_change:task,decision:{recommendation:'ACCEPT',requirements:[]},records:{},historical:false} as unknown as Snapshot;
  const html=renderToStaticMarkup(<ChangeDecision s={s} open={()=>{}} allowed={()=>true}/>);
  expect(html).toContain('QA permission not granted');expect(html).toContain('Review the production pause');expect(html).not.toContain('QA permission granted');
 });
 it('labels evidence with its value, specimen and packaging condition',()=>{
  const s={records:{spec:{label:'Specimen 2'},set:{scope:{closure_lot_id:'cap',config_id:'cfg'}},cap:{label:'C02 caps'},cfg:{label:'Setup v1'}}} as unknown as Snapshot;
  const label=evidenceLabel({id:'opaque',kind:'measurement',study_id:'set',sample_id:'spec',value:'0.98',unit:'N_m',occurred_at:'2026-01-15T08:00:00Z'},s);
  expect(label).toContain('0.98 N·m');expect(label).toContain('Specimen 2');expect(label).toContain('C02 caps');expect(label).toContain('Setup v1');expect(label).not.toContain('opaque');
 });
});
