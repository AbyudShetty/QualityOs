export type Entity={id:string;kind:string;label?:string;[key:string]:any};
export type Actor={id:string;username:string;display_name:string;role:'VIEWER'|'OPERATOR'|'QUALITY_ENGINEER'|'ADMIN'};
export type Requirement={type:string;verdict:string;reason:string;evidence_refs:string[];next_action:string};
export type Decision={id:string;recommendation:string;requirements:Requirement[];measurements:Entity[];study_ids:string[];scope:Record<string,string>;evidence_refs:string[];applicability_fingerprint:string;evaluated_at:string;known_through_seq:number};
export type Workspace={id:string;name:string;clock:string;revision:number;cursor:number;scenario_version:string};
export type Journey={version:string;run_id:string;control_run_id?:string|null;chapters:string[];id:string;chapter:number;step_index:number|null;total_steps:number;title:string;story:string;why:string;action_label:string;page:string;operation:string|null;payload:Record<string,any>;preview:{label:string;value:string}[];expected:string;status:string;reason:string};
export type Snapshot={workspace:Workspace;run:Entity;runs:Entity[];records:Record<string,Entity>;decision:Decision;events:any[];decisions:{id:string;at:string;cut:number;recommendation:string}[];edges:{from_id:string;relation:string;to_id:string;source_event_id:string}[];historical:boolean;view:string;clock:string;impact:{certainty:string;units:Entity[];reason:string};guidance:{operation:string;label:string;qa_required:boolean;reason:string};journey?:Journey|null};
export class ApiError extends Error {code:string;status:number; constructor(status:number,data:any){super(data.message||data.detail?.[0]?.msg||'The request could not be completed');this.code=data.code||'REQUEST_FAILED';this.status=status}}
export function csrf(){return decodeURIComponent(document.cookie.split('; ').find(x=>x.startsWith('qualityos_csrf='))?.split('=')[1]||'')}
export async function api<T=any>(path:string,options:RequestInit={}):Promise<T>{
 const response=await fetch('/api/v1'+path,{credentials:'same-origin',...options,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf(),...options.headers}});
 const data=await response.json();if(!response.ok)throw new ApiError(response.status,data);return data;
}
export function command(wid:string,revision:number,operation:string,payload:Record<string,any>,reason:string,key:string=crypto.randomUUID()){return api(`/workspaces/${wid}/commands/${operation}`,{method:'POST',headers:{'Idempotency-Key':key},body:JSON.stringify({expected_context_revision:revision,payload,reason})})}
export function entities(snapshot:Snapshot,kind:string){return Object.values(snapshot.records).filter(e=>e.kind===kind)}
export function date(value:string,full=false){return new Intl.DateTimeFormat('en-GB',{day:'2-digit',month:'short',...(full?{year:'numeric' as const}:{}),hour:'2-digit',minute:'2-digit',timeZone:'UTC',hour12:false}).format(new Date(value))+' UTC'}
export function pretty(value:string){return value.toLowerCase().replaceAll('_',' ').replace(/^./,x=>x.toUpperCase()).replace(/\bqa\b/g,'QA')}
export function canWrite(actor:Actor){return ['OPERATOR','QUALITY_ENGINEER'].includes(actor.role)}
export function qaRequired(op:string){return ['calibrate','revoke_calibration','resolve_hold','authorize','approve_action','assess_action','disposition'].includes(op)}
