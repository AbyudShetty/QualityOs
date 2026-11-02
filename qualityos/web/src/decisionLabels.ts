import {date} from './api';
import type {Entity,Snapshot} from './api';

export function evidenceLabel(e:Entity,s:Snapshot):string {
 const study=s.records[e.study_id];
 const scope=study?.scope;
 const specimen=s.records[e.sample_id]?.label||'Specimen not recorded';
 const result=e.kind==='measurement'?`${e.value} ${e.unit==='N_m'?'N·m':e.unit}`:e.outcome||e.label||'Record';
 const condition=scope?[s.records[scope.closure_lot_id]?.label,s.records[scope.config_id]?.label].filter(Boolean).join(' / '):'Condition not recorded';
 return [result,specimen,condition,e.occurred_at?date(e.occurred_at):''].filter(Boolean).join(' · ');
}
