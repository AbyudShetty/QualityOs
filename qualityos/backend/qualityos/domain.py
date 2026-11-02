"""Pure policy. No persistence, scenario generator or evaluator imports."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def instant(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timezone information is required")
    return dt.astimezone(timezone.utc)


def number(value: Any) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("Exact quantities must be decimal strings")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Invalid decimal quantity") from exc
    if not result.is_finite():
        raise ValueError("Nonfinite quantities are forbidden")
    if len(result.as_tuple().digits) > 18 or not -12 <= result.as_tuple().exponent <= 12:
        raise ValueError("Engineering quantities require at most 18 digits and exponent -12 to 12")
    return result


def reliability(m: dict, records: dict, now: str) -> dict:
    try:
        return _reliability(m,records,now)
    except (KeyError,ValueError,TypeError):
        return {'verdict':'UNKNOWN','reasons':['REFERENCE_OR_QUANTITY_MALFORMED']}


def _reliability(m: dict, records: dict, now: str) -> dict:
    reasons = []
    cal = records.get(m.get("calibration_id"), {})
    instrument = records.get(m.get("instrument_id"), {})
    if cal.get('kind')!='calibration' or instrument.get('kind')!='instrument':
        return {"verdict": "UNKNOWN", "reasons": ["REFERENCE_MISSING"]}
    if instant(cal.get("available_at", now)) > instant(now):
        return {"verdict": "UNKNOWN", "reasons": ["REFERENCE_NOT_AVAILABLE"]}
    if m.get("unit") != instrument.get("unit"):
        return {"verdict": "INVALID", "reasons": ["UNIT_MISMATCH"]}
    when = instant(m["occurred_at"])
    if cal.get("instrument_id") != m.get("instrument_id"):
        reasons.append("REFERENCE_IDENTITY_MISMATCH")
    if not instant(cal["valid_from"]) <= when <= instant(cal["valid_until"]):
        reasons.append("REFERENCE_OUTSIDE_VALIDITY")
    for rev in records.values():
        if rev.get("kind") == "revocation" and rev.get("calibration_id") == cal["id"]:
            if instant(rev["available_at"]) <= instant(now) and instant(
                rev["effective_from"]
            ) <= when <= instant(rev["effective_until"]):
                reasons.append("REFERENCE_REVOKED")
    if m.get("raw_quality_flags") or not instrument.get("active", True):
        reasons.append("INSTRUMENT_FAULT")
    if reasons:
        return {"verdict": "INVALID", "reasons": reasons}
    uncertainty = m.get("uncertainty") or {}
    if uncertainty.get("kind") != "ENGINEERING_BOUND" or not uncertainty.get("basis"):
        return {"verdict": "UNKNOWN", "reasons": ["UNCERTAINTY_UNSUPPORTED_OR_MISSING"]}
    if uncertainty.get("unit") != m["unit"]:
        return {"verdict": "INVALID", "reasons": ["UNCERTAINTY_UNIT_MISMATCH"]}
    if number(uncertainty["half_width"]) < 0:
        return {"verdict": "INVALID", "reasons": ["NEGATIVE_UNCERTAINTY"]}
    return {"verdict": "VALID", "reasons": ["MEASUREMENT_TIME_REFERENCE_VALID"]}


SCOPE_FIELDS = ("product_id", "bottle_lot_id", "closure_lot_id", "config_id", "policy_id")


def scope_of(run: dict) -> dict:
    return {key: run.get(key) for key in SCOPE_FIELDS}


def applicable(study: dict, run: dict) -> bool:
    scope = study.get("scope", {})
    if not all(run.get(k) for k in SCOPE_FIELDS):
        return False
    if all(scope.get(k) == run.get(k) for k in SCOPE_FIELDS):
        return True
    # Joint explicitly approved tuples, never the Cartesian product of lists.
    approval = study.get("envelope_approval") or {}
    if not approval.get("approved_by") or not approval.get("basis"):
        return False
    return any(all(item.get(k) == run.get(k) for k in SCOPE_FIELDS)
               for item in study.get("approved_joint_scopes", []))


def policy_problem(policy: dict) -> str | None:
    if not isinstance(policy, dict):
        return "Governing policy is malformed"
    try:
        if policy.get("kind") != "policy" or type(policy.get("revision")) is not int or policy["revision"] < 1:
            return "Missing or invalid versioned governing policy"
        if type(policy.get("minimum_specimens")) is not int or not 1 <= policy["minimum_specimens"] <= 1000:
            return "Policy requires a positive integral specimen count"
        low, high = number(policy["torque_low"]), number(policy["torque_high"])
        if not 0 < low < high:
            return "Policy torque limits are missing or inverted"
        if type(policy.get("dwell_hours")) not in {int, float} or not 0 < policy["dwell_hours"] <= 8760:
            return "Policy requires a valid positive dwell"
    except (ValueError, KeyError, TypeError):
        return "Governing policy is incomplete or malformed"
    return None


def evaluate(run: dict, records: dict, now: str) -> dict:
    requirements = []
    study_checks = []
    def check(code, verdict, reason, refs, next_action):
        requirements.append(dict(type=code, verdict=verdict, reason=reason,
                                 evidence_refs=refs, next_action=next_action))
    def result(details=None, study_ids=None):
        verdicts = {q['verdict'] for q in requirements}
        policy = records.get(run.get('policy_id'), {})
        return dict(run_id=run['id'], recommendation='REJECT' if 'VIOLATED' in verdicts else 'HOLD' if 'UNKNOWN' in verdicts else 'ACCEPT',
                    requirements=requirements, measurements=details or [], study_ids=sorted(study_ids or []),
                    evidence_refs=sorted({i for q in requirements for i in q['evidence_refs']}),
                    applicability_fingerprint=digest({'scope':scope_of(run),'policy':policy}),
                    evaluated_at=now,scope=scope_of(run),provenance='SYNTHETIC',time_basis='SCENARIO_UTC')
    policy = records.get(run.get('policy_id'), {})
    problem = policy_problem(policy)
    if not problem:
        try:
            if policy.get('id')!=run.get('policy_id') or instant(policy['available_at'])>instant(now):
                problem='Governing policy identity or availability is invalid'
        except (KeyError,TypeError,ValueError):
            problem='Governing policy availability is incomplete'
    check('GOVERNING_POLICY','UNKNOWN' if problem else 'SATISFIED',problem or 'Explicit versioned demonstration policy is present',
          [policy['id']] if isinstance(policy,dict) and policy.get('id') else [],'QA must restore a valid governing policy; no default requirements are inferred')
    if problem:
        return result()
    minimum = policy['minimum_specimens']
    low, high = number(policy['torque_low']), number(policy['torque_high'])
    studies = sorted([s for s in records.values() if s.get('kind')=='study' and applicable(s,run)
                      and instant(s['available_at'])<=instant(now)],key=lambda s:s['id'])
    study_ids={s['id'] for s in studies}
    superseded={x.get('supersedes_id') for x in records.values() if x.get('kind')=='correction' and instant(x['available_at'])<=instant(now)}
    ms=[m for m in records.values() if m.get('kind')=='measurement' and m.get('study_id') in study_ids
        and m['id'] not in superseded and instant(m['occurred_at'])<=instant(m['available_at'])<=instant(now)]
    details=[]
    for m in sorted(ms,key=lambda m:m['id']):
        rel=reliability(m,records,now)
        specimen=records.get(m.get('sample_id'),{})
        if specimen.get('kind')!='specimen' or specimen.get('study_id')!=m['study_id'] or m.get('endpoint')!='application_torque' or not m.get('method_id'):
            rel={'verdict':'UNKNOWN','reasons':['SUBJECT_OR_METHOD_MISMATCH']}
        item={**m,'reliability':rel}
        if rel['verdict']=='VALID' and m['unit']=='N_m':
            try:
                v,u=number(m['value']),number(m['uncertainty']['half_width']);a,b=v-u,v+u
                item['interval']=[str(a),str(b)]
                item['conformance']='SATISFIED' if low<=a<=b<=high else 'VIOLATED' if b<low or a>high else 'UNKNOWN'
            except (ValueError,KeyError,TypeError):
                item['reliability']={'verdict':'UNKNOWN','reasons':['MALFORMED_QUANTITY']}
        details.append(item)
    fs=[f for f in records.values() if f.get('kind')=='functional' and f.get('study_id') in study_ids
        and f['id'] not in superseded and instant(f['occurred_at'])<=instant(f['available_at'])<=instant(now)]
    observed={(m['study_id'],m['sample_id']):m for m in ms
              if records.get(m.get('sample_id'),{}).get('study_id')==m['study_id']}
    qualified=[]
    for f in fs:
        try:
            m=observed.get((f['study_id'],f['sample_id']))
            if m and f.get('endpoint')=='leak_integrity' and f.get('method_id') and instant(m['occurred_at'])<=instant(f['condition_start']) and instant(f['condition_end'])<=instant(f['occurred_at']) and (instant(f['condition_end'])-instant(f['condition_start'])).total_seconds()>=policy['dwell_hours']*3600:
                qualified.append(f)
        except (KeyError,TypeError,ValueError):
            continue
    stats={}
    for study in studies:
        sd=[m for m in details if m['study_id']==study['id']]
        valid={m['sample_id'] for m in sd if m['reliability']['verdict']=='VALID'}
        tests=[f for f in qualified if f['study_id']==study['id']]
        outcomes={f['outcome'] for f in tests}
        passes={f['sample_id'] for f in tests if f['outcome']=='PASS'} & valid
        numeric=len(valid)>=minimum and all(m.get('conformance')=='SATISFIED' for m in sd if m['reliability']['verdict']=='VALID')
        complete=len({m['sample_id'] for m in sd})>=minimum and len({f['sample_id'] for f in tests})>=minimum
        stats[study['id']]={'valid':valid,'passes':passes,'outcomes':outcomes,'numeric':numeric,
                            'complete':complete,'passing':numeric and len(passes)>=minimum and outcomes=={'PASS'}}
        study_checks.append({'study_id':study['id'],'purpose':study.get('purpose','LEGACY_BASELINE'),
            'eligible_specimens':len(valid),'passing_specimens':len(passes),'complete':complete,
            'passing':stats[study['id']]['passing'],'outcomes':sorted(outcomes)})
    disposed=set()
    disposition_refs=[]
    for d in records.values():
        if d.get('kind')!='study_disposition' or d.get('scope')!=scope_of(run) or instant(d['available_at'])>instant(now):
            continue
        verification=stats.get(d.get('verification_study_id'),{})
        action=records.get(d.get('action_id'),{})
        verification_record=records.get(d.get('verification_study_id'),{})
        if verification.get('passing') and action.get('kind')=='action' and action.get('status')=='VERIFIED' and verification_record.get('action_id')==action.get('id') and d.get('study_id')!=d.get('verification_study_id'):
            disposed.add(d['study_id']);disposition_refs.append(d['id'])
    active=[s for s in studies if s['id'] not in disposed]
    required=[s for s in active if s.get('purpose')=='REQUIRED']
    candidates=required or active
    independently_enough=bool(candidates) and (all(len(stats[s['id']]['valid'])>=minimum for s in required) if required else any(len(stats[s['id']]['valid'])>=minimum for s in candidates))
    complete=bool(candidates) and (all(stats[s['id']]['complete'] for s in required) if required else any(stats[s['id']]['complete'] for s in candidates))
    check('EXACT_SCOPE_MATCH','SATISFIED' if complete else 'UNKNOWN',
          'Completed test records target this configuration' if complete else 'No completed required test set covers this configuration; a planned set is not qualification',
          [s['id'] for s in candidates]+disposition_refs,'Collect complete observations and independent results for the required test set')
    valid=[m for m in details if m['reliability']['verdict']=='VALID' and m['study_id'] not in disposed]
    check('MEASUREMENT_RELIABILITY','SATISFIED' if independently_enough else 'UNKNOWN',
          f'{len({m["sample_id"] for m in valid})} eligible specimens; each required set needs {minimum}; no cross-set pooling',
          [m['id'] for m in valid],'Collect enough fresh observations with eligible references in one required set')
    violated=any(m.get('conformance')=='VIOLATED' for m in valid)
    numeric=bool(candidates) and (all(stats[s['id']]['numeric'] for s in required) if required else any(stats[s['id']]['numeric'] for s in candidates))
    unknown_interval=any(m.get('conformance')=='UNKNOWN' for m in valid)
    check('ENDPOINT_CONFORMANCE','VIOLATED' if violated else 'SATISFIED' if numeric and not unknown_interval else 'UNKNOWN',
          'A reliable interval is outside the demonstration tolerance' if violated else 'Complete required intervals are within the demonstration limits' if numeric and not unknown_interval else 'Required numeric proof is incomplete or overlaps a limit',
          [m['id'] for m in valid],'Review the numeric intervals and obtain appropriate fresh evidence')
    active_tests=[f for f in qualified if f['study_id'] not in disposed]
    outcomes={f['outcome'] for f in active_tests};conflict='PASS' in outcomes and 'FAIL' in outcomes
    functional=bool(candidates) and (all(stats[s['id']]['passing'] for s in required) if required else any(stats[s['id']]['passing'] for s in candidates))
    fv='UNKNOWN' if conflict else 'VIOLATED' if 'FAIL' in outcomes else 'SATISFIED' if functional else 'UNKNOWN'
    check('FUNCTIONAL_ENDPOINT',fv,'Conflicting results need scoped QA determination; no latest-pass override' if conflict else 'Independent leak test failed' if 'FAIL' in outcomes else 'Each required test set independently passes its numeric and functional checks' if functional else 'Required independent functional proof is incomplete or inconclusive',
          [f['id'] for f in active_tests]+disposition_refs,'Record a valid independent result after the declared dwell; genuine failures require QA investigation')
    source=records.get(run.get('source_id'),{})
    try:
        fresh=source.get('kind')=='source' and source.get('complete') is True and 0<source['ttl_seconds'] and 0<=(instant(now)-instant(source['last_seen_at'])).total_seconds()<=source['ttl_seconds']
    except (KeyError,TypeError,ValueError):fresh=False
    check('REQUIRED_SOURCE_HEALTH','SATISFIED' if fresh else 'UNKNOWN','Required source is complete and fresh' if fresh else 'Required record feed is stale or incomplete',
          [source['id']] if source.get('id') else [],'Inspect the declared synthetic record-feed status')
    kinds={'product_id':'product','bottle_lot_id':'lot','closure_lot_id':'lot','config_id':'config'}
    identity=run.get('lineage')=='COMPLETE' and all(records.get(run.get(k),{}).get('kind')==kind and records[run[k]].get('id')==run[k] for k,kind in kinds.items()) and records.get(run.get('bottle_lot_id'),{}).get('component')=='BOTTLE' and records.get(run.get('closure_lot_id'),{}).get('component')=='CLOSURE'
    check('IDENTITY_COMPLETENESS','SATISFIED' if identity else 'UNKNOWN','Referenced product, bottle, cap and setup identities are complete' if identity else 'Material/setup identity is missing, wrong-kind or incomplete',
          [run['id']],'Reconcile exact material and configuration identities')
    value=result(details,study_ids)
    value['study_checks']=study_checks
    return value
