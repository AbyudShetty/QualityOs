from __future__ import annotations

import json
from copy import deepcopy
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import text

from .domain import applicable, canonical, digest, evaluate, instant, number, reliability, scope_of
from .scenarios import START, seed_records
from .security import utcnow


class Problem(Exception):
    def __init__(self, code, message, status=409, refs=None):
        self.code, self.message, self.status, self.refs = code, message, status, refs or []


def uid(kind):
    return kind + "-" + uuid4().hex[:12]


QA = {
    "correct_evidence",
    "disposition_study",
    "calibrate",
    "revoke_calibration",
    "resolve_hold",
    "authorize",
    "approve_action",
    "assess_action",
    "disposition",
}
OPERATIONS = QA | {
    "change_context",
    "open_study",
    "measure",
    "measure_batch",
    "functional",
    "advance",
    "refresh_source",
    "investigate",
    "hypothesis",
    "propose_action",
    "execute_action",
    "produce",
    "comment",
    "correct_evidence",
    "complete_run",
}


class Service:
    def __init__(self, store):
        self.store = store

    @staticmethod
    def _recovery_blockers(run, records):
        blockers=[]
        for a in records.values():
            if a.get('kind')!='action' or a.get('run_id')!=run['id'] or not a.get('required_for_release',True) or a.get('status') not in {'APPROVED','EXECUTED','VERIFYING'}:
                continue
            incident=records.get(a.get('investigation_id'),{})
            scope=a.get('execution_scope') or a.get('scope') or incident.get('scope',{})
            if a.get('status') in {'EXECUTED','VERIFYING'}:
                scope={**scope,'config_id':a.get('config_id')}
            if scope==scope_of(run):blockers.append(a)
        return blockers

    @classmethod
    def _evaluate(cls, run, records, now):
        ev=evaluate(run,records,now)
        blockers=cls._recovery_blockers(run,records)
        if blockers:
            ev['requirements'].append({'type':'REQUIRED_ACTION_VERIFICATION','verdict':'UNKNOWN',
                'reason':'A QA-approved required recovery action still needs independently complete fresh verification and QA assessment',
                'evidence_refs':[a['id'] for a in blockers], 'next_action':'Complete and review the required post-action verification'})
            ev['evidence_refs']=sorted(set(ev['evidence_refs'])|{a['id'] for a in blockers})
            if ev['recommendation']=='ACCEPT':ev['recommendation']='HOLD'
        return ev

    @staticmethod
    def _affected(records, now):
        bad={m['id'] for m in records.values() if m['kind']=='measurement' and reliability(m,records,now)['verdict']!='VALID'}
        superseded={x['supersedes_id'] for x in records.values() if x['kind']=='correction'}
        units=[u for u in records.values() if u['kind']=='unit']
        conservative=any(x['kind']=='run' and x.get('lineage')!='COMPLETE' for x in records.values()) and bool(bad or superseded)
        return (units if conservative else [u for u in units if set(u['evidence_ids']) & (bad|superseded)]),conservative

    @staticmethod
    def _impact_cause(unit, records, now, conservative):
        # Bind handling to the actual discovery chain. A second discovery must
        # not inherit a disposition of an earlier, different evidence cut.
        support=set(unit['evidence_ids'])
        causes=set()
        if conservative:
            causes.update(x['id'] for x in records.values() if x['kind'] in {'revocation','correction'})
        for key in list(support):
            m=records.get(key,{})
            if m.get('kind')=='measurement' and reliability(m,records,now)['verdict']!='VALID':
                causes.add(key)
                for rev in records.values():
                    if rev['kind']=='revocation' and rev.get('calibration_id')==m.get('calibration_id') and instant(rev['effective_from'])<=instant(m['occurred_at'])<=instant(rev['effective_until']):causes.add(rev['id'])
        changed=True
        while changed:
            changed=False
            for correction in records.values():
                if correction['kind']=='correction' and correction.get('supersedes_id') in support and correction['id'] not in causes:
                    causes.add(correction['id']);support.add(correction['replacement_id']);changed=True
        return digest(sorted(causes))

    @staticmethod
    def can(actor, operation):
        role = actor["role"]
        if operation in QA:
            return role == "QUALITY_ENGINEER"
        return operation in OPERATIONS and role in {"OPERATOR", "QUALITY_ENGINEER"}

    def _workspace(self, c, wid):
        row = c.execute(text("SELECT * FROM workspaces WHERE id=:w"), {"w": wid}).mappings().first()
        if not row:
            raise Problem("NOT_FOUND", "Workspace not found", 404)
        return dict(row)

    def _audit(self, c, wid, actor, action, outcome, detail):
        c.execute(
            text(
                "INSERT INTO audit(workspace_id,actor_id,action,outcome,system_at,detail) VALUES (:w,:a,:op,:out,:at,:d)"
            ),
            {
                "w": wid,
                "a": actor["id"],
                "op": action,
                "out": outcome,
                "at": utcnow(),
                "d": detail[:2000],
            },
        )

    def create_workspace(self, actor, name="Packaging qualification", scenario="S1", guided=False, purpose='USER_EXPERIMENT', setup=None):
        if actor["role"] not in {"OPERATOR", "QUALITY_ENGINEER", "ADMIN"}:
            raise Problem(
                "ROLE_REQUIRED", "A demo operator or administrator must create a workspace", 403
            )
        wid = uid("workspace")
        records = seed_records(wid[-6:] + "-")
        if purpose not in {'USER_EXPERIMENT','AUTOMATION_TEST'}:
            raise Problem('INVALID_PURPOSE','Unsupported experiment category',422)
        if setup:
            if guided: raise Problem('SETUP_CONFLICT','Choose custom inputs without the legacy guided sequence',422)
            self._configure_experiment(records,setup)
        if guided:
            if scenario != "S1":
                raise Problem(
                    "GUIDED_SCENARIO_REQUIRED", "The guided packaging story uses scenario S1", 422
                )

            def named(suffix):
                return next(x for x in records.values() if x["id"].endswith(suffix))

            anchor = named("run-1")
            gid = uid("guide")
            records[gid] = {
                "id": gid,
                "kind": "guide",
                "label": "The cap changed. Can the line continue?",
                "run_id": anchor["id"],
                "version": "packaging-story-v1",
                "initial_scope": scope_of(anchor),
                "replacement_closure_id": named("closure-c02")["id"],
                "alternate_config_id": named("capper-v2")["id"],
                "teaching_instrument_id": named("torque-02")["id"],
                "expired_reference_id": named("calibration-02-old")["id"],
                "available_at": START,
                "created_at": START,
                "provenance": "SYNTHETIC",
            }
        with self.store.transaction() as c:
            c.execute(
                text("INSERT INTO workspaces(id,name,clock,mode,revision,cursor,scenario_version,purpose,created_by) VALUES (:w,:n,:clock,'SYNTHETIC_DEMO',0,0,:v,:purpose,:actor)"),
                {
                    "w": wid,
                    "n": name,
                    "clock": START,
                    "v": "packpair-v1/" + scenario + ("/guided-story-v1" if guided else ""),
                    'purpose':purpose,
                    'actor':actor['id'],
                },
            )
            ws = self._workspace(c, wid)
            response = self._commit(
                c,
                ws,
                {},
                records,
                actor,
                "WORKSPACE_CREATED",
                uid("seed"),
                "local-scenario",
                {"scenario": scenario, "guided": guided, 'setup':setup, 'purpose':purpose},
            )
        return {"workspace_id": wid, **response}

    @staticmethod
    def _configure_experiment(records,setup):
        def named(suffix): return next(x for x in records.values() if x['id'].endswith(suffix))
        run=named('run-1')
        def custom(kind,label,**data):
            if len(label.strip())<2: raise ValueError('Give each custom input a name of at least two characters')
            key=uid(kind)
            records[key]={'id':key,'kind':kind,'label':label.strip(),'provenance':'SYNTHETIC','created_at':START,'available_at':START,**data}
            return key
        bottle=setup.get('bottle','ORIGINAL');cap=setup.get('cap','ORIGINAL');machine=setup.get('machine','BASELINE')
        if bottle=='CUSTOM':
            run['bottle_lot_id']=custom('lot',setup.get('bottle_name',''),component='BOTTLE',supplier='User-defined fictional supplier',composition='Unknown',specification='User-specified demonstration batch')
        else:run['bottle_lot_id']=named('bottle-b01' if bottle=='ORIGINAL' else 'bottle-b02')['id']
        if cap=='CUSTOM':
            run['closure_lot_id']=custom('lot',setup.get('cap_name',''),component='CLOSURE',supplier='User-defined fictional supplier',composition='Unknown',specification='User-specified demonstration batch')
        else:run['closure_lot_id']=named({'ORIGINAL':'closure-c01','UNTESTED':'closure-c02','COVERED':'closure-c03'}[cap])['id']
        if machine=='CUSTOM':
            setting=number(setup.get('machine_torque','1.00'))
            if not 0<setting<=1000:raise ValueError('The fictional machine setting must be greater than 0 and at most 1000 N·m')
            run['config_id']=custom('config',setup.get('machine_name',''),revision=1,torque_setting=str(setting),unit='N_m')
        else:run['config_id']=named('capper-v1' if machine=='BASELINE' else 'capper-v2')['id']

    def _commit(self, c, ws, before, records, actor, operation, key, source, detail):
        now = ws["clock"]
        evaluations = {}
        for run in [r for r in records.values() if r["kind"] == "run"]:
            ev = self._evaluate(run, records, now)
            evaluations[run["id"]] = ev
            active_holds = [
                h
                for h in records.values()
                if h["kind"] == "hold" and h["run_id"] == run["id"] and h["status"] == "ACTIVE"
            ]
            if ev["recommendation"] != "ACCEPT" and not active_holds:
                hid = uid("hold")
                records[hid] = {
                    "id": hid,
                    "kind": "hold",
                    "run_id": run["id"],
                    "status": "ACTIVE",
                    "scope": scope_of(run),
                    "certainty": "EXACT" if run["lineage"] == "COMPLETE" else "CONSERVATIVE",
                    "reason": next(
                        q["reason"] for q in ev["requirements"] if q["verdict"] != "SATISFIED"
                    ),
                    "created_at": now,
                    "available_at": now,
                    "provenance": "SYNTHETIC",
                }
                active_holds = [records[hid]]
            for permit in [
                p
                for p in records.values()
                if p["kind"] == "permit" and p["run_id"] == run["id"] and p["status"] == "ACTIVE"
            ]:
                if instant(now) >= instant(permit["expires_at"]):
                    permit["status"] = "EXPIRED"
                elif (
                    ev["recommendation"] != "ACCEPT"
                    or permit["fingerprint"] != ev["applicability_fingerprint"]
                    or active_holds
                    or not self._support_valid(permit, records, now)
                ):
                    permit["status"] = "REVOKED"
            live = any(
                p["kind"] == "permit"
                and p["run_id"] == run["id"]
                and p["status"] == "ACTIVE"
                and p["used_units"] < p["max_units"]
                for p in records.values()
            )
            if run.get("state") != "COMPLETED":
                run["state"] = (
                    "HELD"
                    if active_holds or ev["recommendation"] != "ACCEPT"
                    else "AUTHORIZED"
                    if live
                    else "READY_FOR_QA"
                )
            ev["id"] = uid("decision")
            run["current_decision_id"] = ev["id"]
        affected,conservative=self._affected(records,now)
        covered={(i,h.get('trigger_by_unit',{}).get(i)) for h in records.values() if h['kind']=='containment' for i in h['unit_ids']}
        causes={u['id']:self._impact_cause(u,records,now,conservative) for u in affected}
        new_units=[u['id'] for u in affected if (u['id'],causes[u['id']]) not in covered]
        if new_units:
            hid=uid('containment')
            records[hid]={'id':hid,'kind':'containment','unit_ids':new_units,'status':'ACTIVE',
                'trigger_by_unit':{i:causes[i] for i in new_units},
                'certainty':'CONSERVATIVE' if conservative else 'EXACT',
                'reason':'Later evidence requires QA review of these historical units; independent current scope is evaluated separately',
                'created_at':now,'available_at':now,'provenance':'SYNTHETIC'}
        changes = {
            i: r
            for i, r in records.items()
            if i not in before or canonical(r) != canonical(before[i])
        }
        event_id = uid("event")
        payload = {
            "changes": changes,
            "detail": detail,
            "schema_version": 1,
            "provenance": "SYNTHETIC",
            "time_basis": "SCENARIO_UTC",
        }
        result = c.execute(
            text(
                "INSERT INTO events(id,workspace_id,source_id,source_event_id,type,occurred_at,available_at,recorded_at,received_at_system_utc,actor_id,payload,payload_sha256) VALUES (:id,:w,:s,:key,:type,:t,:t,:t,:system,:a,:p,:hash)"
            ),
            {
                "id": event_id,
                "w": ws["id"],
                "s": source,
                "key": key,
                "type": operation,
                "t": now,
                "system": utcnow(),
                "a": actor["id"],
                "p": canonical(payload),
                "hash": digest(payload),
            },
        )
        seq = result.lastrowid
        for r in changes.values():
            self.store.put(c, ws["id"], r)
        for r in changes.values():
            references = []
            for field, relation in [
                ("instrument_id", "MEASURED_BY"),
                ("calibration_id", "CALIBRATED_BY"),
                ("study_id", "SUPPORTS"),
                ("run_id", "USED_IN"),
                ("bottle_lot_id", "USED_IN"),
                ("closure_lot_id", "USED_IN"),
                ("config_id", "USED_IN"),
                ("permit_id", "AUTHORIZED_BY"),
                ("action_id", "VERIFIES"),
                ("supersedes_id", "SUPERSEDES"),
            ]:
                target = r.get(field)
                if target and target in records:
                    references.append((r["id"], relation, target))
            for a, relation, b in references:
                c.execute(
                    text(
                        "INSERT OR IGNORE INTO edges(workspace_id,from_id,relation,to_id,source_event_id) VALUES (:w,:a,:r,:b,:e)"
                    ),
                    {"w": ws["id"], "a": a, "r": relation, "b": b, "e": event_id},
                )
        for rid, ev in evaluations.items():
            ev["known_through_seq"] = seq
            snapshot = {
                "decision": ev,
                "records": deepcopy(records),
                "clock": now,
                "revision": ws["revision"] + 1,
                "cursor": seq,
            }
            c.execute(
                text("INSERT INTO decisions VALUES (:id,:w,:r,:cut,:at,:p)"),
                {
                    "id": ev["id"],
                    "w": ws["id"],
                    "r": rid,
                    "cut": seq,
                    "at": now,
                    "p": canonical(snapshot),
                },
            )
            self._audit(c, ws["id"], actor, "DECISION_CREATED", ev["recommendation"], ev["id"])
        c.execute(
            text("UPDATE workspaces SET clock=:clock,revision=revision+1,cursor=:seq WHERE id=:w"),
            {"clock": now, "seq": seq, "w": ws["id"]},
        )
        self._audit(c, ws["id"], actor, operation, "COMMITTED", canonical(detail))
        return {
            "event_id": event_id,
            "domain_cursor": seq,
            "context_revision": ws["revision"] + 1,
            "entity_ids": list(changes),
            "provenance": "SYNTHETIC",
        }

    @staticmethod
    def _proof_fingerprint(supporting_ids, records):
        proof = {
            key: records[key]
            for key in supporting_ids
            if key in records and records[key]["kind"] not in {"run", "source"}
        }
        for item in list(proof.values()):
            for field in ("calibration_id", "instrument_id"):
                if item.get(field) in records:
                    proof[item[field]] = records[item[field]]
        return digest(proof)

    @staticmethod
    def _support_valid(permit, records, now):
        if permit.get("evidence_fingerprint") and permit[
            "evidence_fingerprint"
        ] != Service._proof_fingerprint(permit["supporting_ids"], records):
            return False
        superseded = {
            r.get("supersedes_id") for r in records.values() if r.get("kind") == "correction"
        }
        for key in permit.get("supporting_ids", []):
            item = records.get(key, {})
            if key in superseded:
                return False
            if (
                item.get("kind") == "measurement"
                and reliability(item, records, now)["verdict"] != "VALID"
            ):
                return False
        return True

    def command(self, wid, actor, operation, body, key):
        if not self.can(actor, operation):
            with self.store.transaction() as c:
                self._audit(c, wid, actor, operation, "DENIED", "Role cannot perform this command")
            raise Problem(
                "ROLE_REQUIRED",
                "This action requires an authorized "
                + ("quality engineer" if operation in QA else "operator"),
                403,
            )
        fingerprint = digest(body)
        try:
            with self.store.transaction() as c:
                ws = self._workspace(c, wid)
                receipt = (
                    c.execute(
                        text(
                            "SELECT * FROM receipts WHERE workspace_id=:w AND actor_id=:a AND namespace=:n AND key=:k"
                        ),
                        {"w": wid, "a": actor["id"], "n": operation, "k": key},
                    )
                    .mappings()
                    .first()
                )
                if receipt:
                    if receipt["request_hash"] != fingerprint:
                        raise Problem(
                            "IDEMPOTENCY_COLLISION",
                            "Same command key was used with different content",
                        )
                    return {
                        **json.loads(receipt["response"]),
                        "replayed": True,
                        "current_revision": ws["revision"],
                    }
                if body["expected_context_revision"] != ws["revision"]:
                    raise Problem(
                        "STALE_CONTEXT", "Context changed. Refresh and review before trying again."
                    )
                records = self.store.records(c, wid)
                before = deepcopy(records)
                self._apply(operation, body["payload"], records, ws, actor, body.get("reason", ""))
                response = self._commit(
                    c,
                    ws,
                    before,
                    records,
                    actor,
                    operation.upper(),
                    key,
                    actor["id"] + ":" + operation,
                    {"reason": body.get("reason", ""), "payload": body["payload"]},
                )
                c.execute(
                    text("INSERT INTO receipts VALUES (:w,:a,:n,:k,:h,:r)"),
                    {
                        "w": wid,
                        "a": actor["id"],
                        "n": operation,
                        "k": key,
                        "h": fingerprint,
                        "r": canonical(response),
                    },
                )
                return response
        except Problem as exc:
            with self.store.transaction() as c:
                self._audit(c, wid, actor, operation, "DENIED", exc.code + ": " + exc.message)
            raise

    def _apply(self, op, p, r, ws, actor, reason):
        now = ws["clock"]
        if op=='measure_batch':
            for value in p['values']: number(value)
            base={k:v for k,v in p.items() if k!='values'}
            for value in p['values']:
                self._apply('measure',{**base,'value':value,'count':1},r,ws,actor,reason)
            return

        def get(key, kind=None):
            item = r.get(key)
            if not item or (kind and item["kind"] != kind):
                raise Problem(
                    "IDENTITY_MISMATCH",
                    "Referenced object is absent, wrong type or belongs to another workspace",
                    422,
                    [key],
                )
            return item

        def add(kind, **data):
            key = uid(kind)
            r[key] = {
                "id": key,
                "kind": kind,
                "available_at": now,
                "created_at": now,
                "recorded_revision": ws["revision"] + 1,
                "provenance": "SYNTHETIC",
                **data,
            }
            return r[key]

        def decision(run):
            return self._evaluate(run, r, now)

        def check_qa_snapshot(run):
            if self._recovery_blockers(run,r):
                raise Problem('REQUIRED_VERIFICATION_PENDING','QA-required recovery verification must be complete and assessed before resolving a pause or authorizing production')
            ev = decision(run)
            if (
                p.get("decision_id") != run.get("current_decision_id")
                or p.get("fingerprint") != ev["applicability_fingerprint"]
            ):
                raise Problem(
                    "STALE_DECISION", "The reviewed decision no longer matches the current context"
                )
            if ev["recommendation"] != "ACCEPT":
                raise Problem(
                    "EVIDENCE_NOT_READY", "Applicable evidence is incomplete or nonconforming"
                )
            return ev

        if op == "advance":
            hours = p["hours"]
            ws["clock"] = (instant(now) + timedelta(hours=hours)).isoformat()
            return
        if op == "calibrate":
            inst = get(p["instrument_id"], "instrument")
            add(
                "calibration",
                label=inst["label"] + " · new reference",
                instrument_id=inst["id"],
                valid_from=now,
                valid_until=(instant(now) + timedelta(days=90)).isoformat(),
                method_id=p["method_id"],
                basis=p["basis"],
                issued_by=actor["id"],
            )
            return
        if op == "revoke_calibration":
            cal = get(p["calibration_id"], "calibration")
            if instant(p["effective_from"]) > instant(p["effective_until"]):
                raise Problem("INVALID_INTERVAL", "Revocation interval is inverted", 422)
            add(
                "revocation",
                label="Reference revocation",
                calibration_id=cal["id"],
                effective_from=p["effective_from"],
                effective_until=p["effective_until"],
                reason=reason,
            )
            return
        if op == "comment":
            add("note", label="Review note", text=p["text"], run_id=get(p["run_id"], "run")["id"])
            return
        if op == "hypothesis":
            incident = get(p["investigation_id"], "investigation")
            for key in p["supporting_ids"] + p["refuting_ids"]:
                get(key)
            add(
                "hypothesis",
                label=p["statement"],
                statement=p["statement"],
                mechanism=p["mechanism"],
                investigation_id=incident["id"],
                supporting_ids=p["supporting_ids"],
                refuting_ids=p["refuting_ids"],
                status="UNDER_TEST",
            )
            return
        if op == "propose_action":
            incident = get(p["investigation_id"], "investigation")
            target = get(p["config_id"], "config")
            add(
                "action",
                label="Verify alternative application configuration",
                investigation_id=incident["id"],
                run_id=incident["run_id"],
                config_id=target["id"],
                status="PROPOSED",
                rationale=reason,
                verification_plan=p["verification_plan"],
                required_for_release=p.get('required_for_release',True),
                scope=incident['scope'],
                hold_ids=[h['id'] for h in r.values() if h['kind']=='hold' and h['run_id']==incident['run_id'] and h['status']=='ACTIVE'],
            )
            return
        if op in {"approve_action", "execute_action", "assess_action"}:
            action = get(p["action_id"], "action")
            run = get(action["run_id"], "run")
            if op == "approve_action":
                if action["status"] != "PROPOSED":
                    raise Problem("INVALID_TRANSITION", "Only proposed actions can be approved")
                action.update(status="APPROVED", approved_by=actor["id"], approved_at=now)
            elif op == "execute_action":
                if action["status"] != "APPROVED":
                    raise Problem(
                        "INVALID_TRANSITION", "Execution requires a prior approved action"
                    )
                action.update(status="EXECUTED", executed_at=now, executed_by=actor["id"])
                run.update(
                    config_id=action["config_id"], context_revision=run["context_revision"] + 1
                )
                action['execution_scope']=scope_of(run)
            else:
                if action["status"] not in {"EXECUTED", "VERIFYING"}:
                    raise Problem(
                        "INVALID_TRANSITION",
                        "Execute the action and collect new verification first",
                    )
                ev = evaluate(run,r,now)
                fresh = [
                    s
                    for s in r.values()
                    if s["kind"] == "study"
                    and s.get("action_id") == action["id"]
                    and s["id"] in ev["study_ids"]
                    and instant(s["created_at"]) >= instant(action["executed_at"])
                ]
                fresh_ids = {s["id"] for s in fresh}
                fresh_records = {
                    key: item
                    for key, item in r.items()
                    if item["kind"] != "study" or key in fresh_ids
                }
                fresh_ev=evaluate(run,fresh_records,now)
                if not fresh or fresh_ev['recommendation']!='ACCEPT':
                    raise Problem(
                        "NEW_VERIFICATION_REQUIRED",
                        "A complete independently sufficient post-action qualification is required; old proof cannot fill its gaps",
                    )
                proof = [
                    r[i]
                    for i in fresh_ev["evidence_refs"]
                    if i in r and r[i].get("study_id") in {s["id"] for s in fresh}
                ]
                if not any(x["kind"] == "functional" for x in proof) or not any(
                    x["kind"] == "measurement"
                    and instant(x["occurred_at"]) >= instant(action["executed_at"])
                    for x in proof
                ):
                    raise Problem(
                        "NEW_VERIFICATION_REQUIRED", "Old observations cannot verify an action"
                    )
                action.update(
                    status="VERIFIED",
                    assessment="SUPPORTED_IN_SIMULATION",
                    assessed_at=now,
                    reviewed_by=actor["id"],
                    new_evidence_ids=[x["id"] for x in proof],
                    verified_study_ids=sorted(fresh_ids),
                )
                add(
                    "effectiveness",
                    label="Scoped simulation effectiveness",
                    action_id=action["id"],
                    result="SUPPORTED_IN_SIMULATION",
                    evidence_ids=[x["id"] for x in proof],
                    comparison="Prior rejected configuration versus new scoped verification; no physical causal claim",
                    reviewed_by=actor["id"],
                )
            return
        if op == 'disposition_study':
            old=get(p['study_id'],'study');new=get(p['verification_study_id'],'study');a=get(p['action_id'],'action')
            run=get(old['run_id'],'run')
            if old['id']==new['id'] or new.get('action_id')!=a['id'] or a.get('status')!='VERIFIED' or new['id'] not in a.get('verified_study_ids',[]) or new.get('scope')!=scope_of(run) or a.get('execution_scope')!=scope_of(run) or not applicable(old,run):
                raise Problem('DISPOSITION_SCOPE_MISMATCH','A separate passing verification from the reviewed action must cover this exact current condition')
            only={k:v for k,v in r.items() if v['kind']!='study' or k==new['id']}
            if evaluate(run,only,now)['recommendation']!='ACCEPT':
                raise Problem('NEW_VERIFICATION_REQUIRED','The named verification must independently meet every evidence requirement')
            if any(d['kind']=='study_disposition' and d.get('study_id')==old['id'] and d.get('scope')==scope_of(run) for d in r.values()):
                raise Problem('ALREADY_DISPOSITIONED','This study already has a determination for the current condition')
            add('study_disposition',label='QA determination of prior study',study_id=old['id'],verification_study_id=new['id'],action_id=a['id'],
                scope=scope_of(run),reason=reason,qa_actor=actor['id'],
                failed_observation_ids=[f['id'] for f in r.values() if f['kind']=='functional' and f.get('study_id')==old['id'] and f.get('outcome')=='FAIL'])
            return
        if op == "disposition":
            for unit_id in p["unit_ids"]:
                unit = get(unit_id, "unit")
                add(
                    "disposition",
                    label="QA simulation disposition",
                    unit_id=unit["id"],
                    run_id=unit["run_id"],
                    disposition=p["disposition"],
                    reason=reason,
                    qa_actor=actor["id"],
                )
                for h in r.values():
                    if h['kind']=='containment' and unit_id in h['unit_ids']:
                        h.setdefault('reviewed_units',{})[unit_id]={'disposition':p['disposition'],'qa_actor':actor['id'],'at':now}
                        if all(i in h['reviewed_units'] for i in h['unit_ids']):
                            h['status']='HELD' if any(d['disposition']=='HELD' for d in h['reviewed_units'].values()) else 'DISPOSITIONED'
            return
        run = get(p["run_id"], "run") if "run_id" in p else None
        if op == "change_context":
            if run["state"] == "COMPLETED":
                raise Problem(
                    "RUN_COMPLETED", "Create a new run rather than changing completed production"
                )
            if p["field"] == "lineage":
                if p["value"] not in {"COMPLETE", "PARTIAL", "UNKNOWN"}:
                    raise Problem("INVALID_LINEAGE", "Use COMPLETE, PARTIAL or UNKNOWN", 422)
                run["lineage"] = p["value"]
            else:
                target = get(p["value"], "config" if p["field"] == "config_id" else "lot")
                if p["field"] == "closure_lot_id" and target.get("component") != "CLOSURE":
                    raise Problem(
                        "COMPONENT_MISMATCH", "A closure assignment requires a closure lot", 422
                    )
                if p["field"] == "bottle_lot_id" and target.get("component") != "BOTTLE":
                    raise Problem(
                        "COMPONENT_MISMATCH", "A bottle assignment requires a bottle lot", 422
                    )
                run[p["field"]] = target["id"]
            run["context_revision"] += 1
        elif op == "refresh_source":
            source = get(run["source_id"], "source")
            source.update(complete=p["complete"], last_seen_at=now, sequence=source["sequence"] + 1)
        elif op == "open_study":
            action_id = p.get("action_id")
            if action_id:
                action = get(action_id, "action")
                if (
                    action["run_id"] != run["id"]
                    or action["status"] != "EXECUTED"
                    or action["config_id"] != run["config_id"]
                ):
                    raise Problem(
                        "ACTION_SCOPE_MISMATCH",
                        "Study must follow the executed action in the same run/configuration",
                    )
                action["status"] = "VERIFYING"
            add(
                "study",
                label="Test set · "
                + get(run["closure_lot_id"])["label"]
                + " / "
                + get(run["config_id"])["label"],
                run_id=run["id"],
                scope=scope_of(run),
                approved_envelope={},
                condition_start=now,
                action_id=action_id,
                purpose=p.get('purpose','REQUIRED'),
                sequence=1+sum(s['kind']=='study' and s.get('run_id')==run['id'] for s in r.values()),
            )
        elif op == "investigate":
            add(
                "investigation",
                label=p["title"],
                run_id=run["id"],
                scope=scope_of(run),
                problem_definition=p["problem_definition"],
                status="OPEN",
                owner=actor["id"],
            )
        elif op == "resolve_hold":
            check_qa_snapshot(run)
            for h in r.values():
                if h["kind"] == "hold" and h["run_id"] == run["id"] and h["status"] == "ACTIVE":
                    h.update(
                        status="RESOLVED",
                        resolved_at=now,
                        resolved_by=actor["id"],
                        resolution_reason=reason,
                    )
        elif op == "authorize":
            ev = check_qa_snapshot(run)
            if any(
                h["kind"] == "hold" and h["run_id"] == run["id"] and h["status"] == "ACTIVE"
                for h in r.values()
            ):
                raise Problem(
                    "HOLD_ACTIVE", "Resolve the active hold through QA before authorization"
                )
            for old in r.values():
                if (
                    old["kind"] == "permit"
                    and old["run_id"] == run["id"]
                    and old["status"] == "ACTIVE"
                ):
                    old["status"] = "REVOKED"
            add(
                "permit",
                label="Bounded simulation permission",
                run_id=run["id"],
                decision_id=p["decision_id"],
                fingerprint=ev["applicability_fingerprint"],
                supporting_ids=ev["evidence_refs"],
                evidence_fingerprint=self._proof_fingerprint(ev["evidence_refs"], r),
                scope=scope_of(run),
                status="ACTIVE",
                issued_at=now,
                expires_at=(instant(now) + timedelta(minutes=p["minutes"])).isoformat(),
                max_units=p["max_units"],
                used_units=0,
                qa_actor=actor["id"],
            )
        elif op == "produce":
            if run["state"] == "COMPLETED":
                raise Problem("RUN_COMPLETED", "This run has already completed")
            ev = decision(run)
            holds = [
                h
                for h in r.values()
                if h["kind"] == "hold" and h["run_id"] == run["id"] and h["status"] == "ACTIVE"
            ]
            permits = [
                pmt
                for pmt in r.values()
                if pmt["kind"] == "permit"
                and pmt["run_id"] == run["id"]
                and pmt["status"] == "ACTIVE"
                and instant(now) < instant(pmt["expires_at"])
                and pmt["fingerprint"] == ev["applicability_fingerprint"]
                and self._support_valid(pmt, r, now)
            ]
            if ev["recommendation"] != "ACCEPT" or holds or not permits:
                raise Problem(
                    "PRODUCTION_BLOCKED",
                    "Simulation requires current applicable evidence, no active hold, and a live QA permission",
                )
            permit = permits[-1]
            if permit["used_units"] + p["units"] > permit["max_units"]:
                raise Problem(
                    "UNIT_BUDGET_EXCEEDED",
                    "Requested units exceed the remaining QA-authorized budget",
                )
            ordinal = sum(x["kind"] == "unit" and x["run_id"] == run["id"] for x in r.values())
            for index in range(p["units"]):
                add(
                    "unit",
                    label=f"{run['label']} · unit {ordinal+index+1:03}",
                    run_id=run["id"],
                    ordinal=ordinal + index + 1,
                    produced_at=now,
                    permit_id=permit["id"],
                    scope=scope_of(run),
                    evidence_ids=permit["supporting_ids"],
                    disposition="UNASSESSED",
                )
            permit["used_units"] += p["units"]
        elif op == "complete_run":
            if not any(x["kind"] == "unit" and x["run_id"] == run["id"] for x in r.values()):
                raise Problem("NO_PRODUCTION", "A run with no units cannot be completed")
            if decision(run)["recommendation"] != "ACCEPT" or any(
                x["kind"] == "hold" and x["run_id"] == run["id"] and x["status"] == "ACTIVE"
                for x in r.values()
            ):
                raise Problem(
                    "HOLD_ACTIVE", "Resolve evidence and hold before completing this simulation"
                )
            run["state"] = "COMPLETED"
            for x in r.values():
                if x["kind"] == "permit" and x["run_id"] == run["id"]:
                    x["status"] = "REVOKED"
        elif op in {"measure", "functional"}:
            study = get(p["study_id"], "study")
            run = get(study["run_id"], "run")
            if op == "measure":
                cal = get(p["calibration_id"], "calibration")
                inst = get(cal["instrument_id"], "instrument")
                number(p["value"])
                number(p["half_width"])
                if p["unit"] != inst["unit"] or number(p["half_width"]) < 0:
                    raise Problem(
                        "INVALID_QUANTITY",
                        "Compatible units and nonnegative engineering bounds are required",
                        422,
                    )
                occurred = p.get("occurred_at") or now
                if instant(occurred) > instant(now) or instant(occurred) < instant(
                    study["condition_start"]
                ):
                    raise Problem(
                        "INVALID_TIME",
                        "Observation must occur after study start and by the replay clock",
                        422,
                    )
                for index in range(p["count"]):
                    specimen = add(
                        "specimen",
                        label="Fictional specimen " + str(1 + sum(x["kind"]=="specimen" and x.get("study_id")==study["id"] for x in r.values())),
                        study_id=study["id"],
                        fresh_or_reused="FRESH",
                        preparation_group=study["id"],
                    )
                    add(
                        "measurement",
                        label="Application torque",
                        study_id=study["id"],
                        sample_id=specimen["id"],
                        endpoint="application_torque",
                        value=p["value"],
                        unit=p["unit"],
                        instrument_id=inst["id"],
                        calibration_id=cal["id"],
                        uncertainty={
                            "kind": p["uncertainty_kind"],
                            "half_width": p["half_width"],
                            "unit": p["unit"],
                            "basis": p["basis"],
                        },
                        occurred_at=occurred,
                        method_id="synthetic-torque-v1",
                        raw_quality_flags=[],
                    )
            else:
                specimens = [
                    s
                    for s in r.values()
                    if s["kind"] == "specimen" and s.get("study_id") == study["id"]
                ]
                if not specimens:
                    raise Problem(
                        "SPECIMENS_MISSING",
                        "Record distinct scoped specimens before functional results",
                    )
                observed = {
                    m["sample_id"]: m["occurred_at"]
                    for m in r.values()
                    if m["kind"] == "measurement" and m.get("study_id") == study["id"]
                }
                if any(
                    s["id"] not in observed
                    or (instant(now) - instant(observed[s["id"]])).total_seconds() < 24 * 3600
                    for s in specimens
                ):
                    raise Problem(
                        "DWELL_INCOMPLETE",
                        "Every identified specimen requires 24 replay hours after its observation; study age is insufficient",
                    )
                if any(
                    f["kind"] == "functional" and f.get("study_id") == study["id"]
                    for f in r.values()
                ):
                    raise Problem(
                        "DUPLICATE_SPECIMEN_ENDPOINT",
                        "Functional results for these specimens already exist; use correction history",
                    )
                for specimen in specimens:
                    add(
                        "functional",
                        label="Delayed leak integrity",
                        study_id=study["id"],
                        sample_id=specimen["id"],
                        endpoint="leak_integrity",
                        outcome=p["outcome"],
                        method_id="synthetic-leak-v1",
                        condition_start=observed[specimen["id"]],
                        condition_end=now,
                        occurred_at=now,
                        attestor=actor["id"],
                        note=reason,
                        input_basis=p.get('input_basis','SYNTHETIC_ALL_SPECIMENS_SAME_OUTCOME'),
                    )
        elif op == "correct_evidence":
            old = get(p["evidence_id"])
            if any(
                x["kind"] == "correction" and x.get("supersedes_id") == old["id"]
                for x in r.values()
            ):
                raise Problem(
                    "ALREADY_SUPERSEDED",
                    "Correct the latest replacement; the earlier result already has a successor",
                )
            if old["kind"] not in {"measurement", "functional"}:
                raise Problem(
                    "UNSUPPORTED_CORRECTION",
                    "Only observation/result corrections are supported",
                    422,
                )
            if old["kind"] == "measurement":
                raise Problem(
                    "NEW_OBSERVATION_REQUIRED",
                    "Record a new measurement; do not rewrite a historical numeric value",
                    422,
                )
            replacement = add(
                "functional",
                **{
                    k: v
                    for k, v in old.items()
                    if k not in {"id", "kind", "available_at", "created_at", "provenance", "recorded_revision", "supersedes_id", "attestor", "original_attestor", "corrected_by", "note", "correction_basis"}
                },
                supersedes_id=old["id"],
                original_attestor=old.get('original_attestor',old.get('attestor')),
                attestor=actor['id'],
                corrected_by=actor['id'],
                correction_basis=p.get('correction_basis','RECORDING_ERROR'),
                note=reason,
            )
            replacement["outcome"] = p["outcome"]
            add(
                "correction",
                label="Late functional correction",
                supersedes_id=old["id"],
                replacement_id=replacement["id"],
                reason=reason,
            )
        else:
            raise Problem("UNKNOWN_COMMAND", "Unsupported workflow command", 422)

    def snapshot(self, wid, run_id=None, decision_id=None):
        with self.store.engine.connect() as c:
            # SQLite's legacy driver does not begin a transaction for SELECT.
            # Pin every constituent query to one coherent read snapshot.
            c.exec_driver_sql("BEGIN")
            ws = self._workspace(c, wid)
            records = self.store.records(c, wid)
            runs = [r for r in records.values() if r["kind"] == "run"]
            run = records.get(run_id) if run_id else sorted(runs, key=lambda r: r["label"])[0]
            if not run or run["kind"] != "run":
                raise Problem("NOT_FOUND", "Run not found in this workspace", 404)
            did = decision_id or run["current_decision_id"]
            row = c.execute(
                text("SELECT payload FROM decisions WHERE id=:d AND workspace_id=:w AND run_id=:r"),
                {"d": did, "w": wid, "r": run["id"]},
            ).first()
            if not row:
                raise Problem("NOT_FOUND", "Decision not found in this run", 404)
            past = json.loads(row.payload)
            if decision_id:
                records = past["records"]
                run = records[run["id"]]
            decision = (
                past["decision"]
                if decision_id
                else {
                    **self._evaluate(run, records, ws["clock"]),
                    "id": did,
                    "known_through_seq": ws["cursor"],
                }
            )
            events = [
                dict(x)
                for x in c.execute(
                    text(
                        "SELECT seq,id,type,occurred_at,available_at,recorded_at,received_at_system_utc,actor_id,payload FROM events WHERE workspace_id=:w AND seq<=:cut ORDER BY seq DESC LIMIT 100"
                    ),
                    {"w": wid, "cut": past["cursor"] if decision_id else ws["cursor"]},
                ).mappings()
            ]
            for event in events:
                event['detail']=json.loads(event.pop('payload')).get('detail',{})
            decisions = [
                {
                    "id": x.id,
                    "cut": x.cut,
                    "at": x.evaluated_at,
                    "recommendation": json.loads(x.payload)["decision"]["recommendation"],
                }
                for x in c.execute(
                    text(
                        "SELECT id,cut,evaluated_at,payload FROM decisions WHERE workspace_id=:w AND run_id=:r ORDER BY cut DESC LIMIT 100"
                    ),
                    {"w": wid, "r": run["id"]},
                )
            ]
            edges = [
                dict(x)
                for x in c.execute(
                    text(
                        "SELECT e.from_id,e.relation,e.to_id,e.source_event_id FROM edges e JOIN events v ON v.id=e.source_event_id WHERE e.workspace_id=:w AND v.seq<=:cut ORDER BY e.id DESC LIMIT 120"
                    ),
                    {"w": wid, "cut": past["cursor"] if decision_id else ws["cursor"]},
                ).mappings()
            ]
            affected,broaden=self._affected(records,past['clock'] if decision_id else ws['clock'])
            active_holds = [
                h
                for h in records.values()
                if h["kind"] == "hold" and h["run_id"] == run["id"] and h["status"] == "ACTIVE"
            ]
            permits = [
                p
                for p in records.values()
                if p["kind"] == "permit"
                and p["run_id"] == run["id"]
                and p["status"] == "ACTIVE"
                and p["used_units"] < p["max_units"]
                and instant(ws['clock'])<instant(p['expires_at'])
                and p.get('fingerprint')==decision['applicability_fingerprint']
                and self._support_valid(p,records,ws['clock'])
            ]
            if active_holds or decision['recommendation']!='ACCEPT':permits=[]
            op = "produce" if permits else "authorize"
            label = "Continue simulation" if permits else "Authorize simulated run"
            if active_holds:
                op, label = "resolve_hold", "Review and resolve hold"
            if decision["recommendation"] != "ACCEPT":
                if any(
                    q["type"] == "REQUIRED_SOURCE_HEALTH" and q["verdict"] == "UNKNOWN"
                    for q in decision["requirements"]
                ):
                    op, label = "refresh_source", "Confirm source health"
                elif not decision["study_ids"]:
                    op, label = "open_study", "Open scoped study"
                elif decision["recommendation"] == "REJECT":
                    op, label = "investigate", "Investigate this condition"
                elif any(
                    q["type"] == "MEASUREMENT_RELIABILITY" and q["verdict"] == "UNKNOWN"
                    for q in decision["requirements"]
                ):
                    bad = any(
                        m["reliability"]["verdict"] == "INVALID" for m in decision["measurements"]
                    )
                    fresh = any(
                        x["kind"] == "calibration"
                        and x.get("instrument_id", "").endswith("torque-02")
                        and instant(x["valid_from"])
                        <= instant(ws["clock"])
                        <= instant(x["valid_until"])
                        for x in records.values()
                    )
                    op, label = (
                        ("calibrate", "Record a valid reference")
                        if bad and not fresh
                        else ("measure", "Record torque observations")
                    )
                else:
                    op, label = "functional", "Complete independent test"
            if run["state"] == "COMPLETED":
                op, label = "comment", "Review completed run"
            guidance = {
                "operation": op,
                "label": label,
                "qa_required": op in QA,
                "reason": next(
                    (q["reason"] for q in decision["requirements"] if q["verdict"] != "SATISFIED"),
                    "Evidence checks satisfied; QA authorization remains a separate decision",
                ),
            }
            result = {
                "workspace": ws,
                "run": run,
                "runs": runs
                if not decision_id
                else [x for x in records.values() if x["kind"] == "run"],
                "records": records,
                "decision": decision,
                "events": events,
                "decisions": decisions,
                "edges": edges,
                "guidance": guidance,
                "historical": bool(decision_id),
                "view": "AS_KNOWN" if decision_id else "CURRENT_REASSESSMENT",
                "clock": past["clock"] if decision_id else ws["clock"],
                "impact": {
                    "certainty": "CONSERVATIVE" if broaden else "EXACT",
                    "units": affected,
                    "reason": "Incomplete genealogy broadens the possible population"
                    if broaden
                    else "Explicit produced-unit evidence dependencies; potential impact is not a defect verdict",
                },
                "provenance": "SYNTHETIC",
                "time_basis": "SCENARIO_UTC",
            }
            from .journey import describe_journey

            result["journey"] = describe_journey(
                run,
                records,
                decision,
                result["clock"],
                result["impact"],
                historical=bool(decision_id),
            )
            result['test_sets']=[]
            for study_id in decision['study_ids']:
                observations=[x for x in records.values() if x['kind']=='measurement' and x.get('study_id')==study_id and instant(x['available_at'])<=instant(result['clock'])]
                tests=[x for x in records.values() if x['kind']=='functional' and x.get('study_id')==study_id and instant(x['available_at'])<=instant(result['clock'])]
                remaining=max(0,24-(instant(result['clock'])-max(instant(x['occurred_at']) for x in observations)).total_seconds()/3600) if observations else None
                check=next((x for x in decision.get('study_checks',[]) if x['study_id']==study_id),{})
                result['test_sets'].append({'study_id':study_id,'specimens':len({x['sample_id'] for x in observations}),'wait_hours_remaining':remaining,'has_results':bool(tests),
                    'purpose':records[study_id].get('purpose','LEGACY_BASELINE'),'status':'PLANNED' if not observations else 'IN_PROGRESS' if not tests else 'EVIDENCE_READY' if check.get('passing') else 'NEEDS_REVIEW'})
            cut=past['cursor'] if decision_id else ws['cursor']
            result['history_limits']={'events':100,'decisions':100,'edges':120,
                'events_total':c.execute(text('SELECT count(*) FROM events WHERE workspace_id=:w AND seq<=:cut'),{'w':wid,'cut':cut}).scalar(),
                'export':'Complete workspace records are available via Export experiment; on-screen lists are bounded recent views'}
            result['release']={'allowed':bool(permits) and not decision_id,'permit_ids':[p['id'] for p in permits],
                'active_hold_count':len(active_holds),'required_recovery_actions':[a['id'] for a in self._recovery_blockers(run,records)]}
            result['packaging_change']=self._packaging_task(result)
            return result

    @staticmethod
    def _packaging_task(s):
        """Explain persisted scope/evidence; never grants or invents permission."""
        r=s['records'];run=s['run'];ev=s['decision'];now=s['clock']
        studies=sorted([x for x in r.values() if x['kind']=='study' and x.get('run_id')==run['id']],
                       key=lambda x:(x.get('created_at',x.get('condition_start',x['available_at'])),x.get('recorded_revision',0),x['id']))
        previous=next((x for x in studies if not x.get('action_id') and not x.get('purpose')),studies[0] if studies else None)
        previous_scope=previous.get('scope',{}) if previous else {}
        changes=[]
        for field,label in [('bottle_lot_id','Bottle batch'),('closure_lot_id','Cap batch'),('config_id','Machine setup')]:
            old=r.get(previous_scope.get(field),{});current=r.get(run.get(field),{})
            changes.append({'field':field,'label':label,'previous_id':old.get('id'),'current_id':current.get('id'),
                'previous':old.get('label','Not recorded'),'current':current.get('label','Missing identity'),
                'previous_supplier':old.get('supplier'),'current_supplier':current.get('supplier'),
                'changed':old.get('id')!=current.get('id')})
        changed=any(x['changed'] for x in changes)
        prior_applies=bool(previous and applicable(previous,run))
        required=[x for x in studies if x['id'] in ev['study_ids'] and x.get('purpose')=='REQUIRED']
        required.sort(key=lambda x:(x.get('recorded_revision',0),x.get('created_at',''),x['id']))
        current=required[-1] if required else None
        state=next((x for x in s['test_sets'] if current and x['study_id']==current['id']),None)
        actions=[x for x in r.values() if x['kind']=='action' and x.get('run_id')==run['id'] and x.get('required_for_release',True)
                 and x.get('execution_scope',x.get('scope',{}))==scope_of(run)]
        actions.sort(key=lambda x:(x.get('recorded_revision',0),x.get('created_at',''),x['id']))
        a=next((x for x in reversed(actions) if x.get('status')!='VERIFIED'),None)
        incidents=[x for x in r.values() if x['kind']=='investigation' and x.get('run_id')==run['id']]
        q={x['type']:x for x in ev['requirements']}
        def next_action(op,title,why,payload=None):
            return {'operation':op,'label':title,'why':why,'payload':payload or {},'qa_required':op in QA}
        nxt=next_action(None,'Review the unresolved requirement','No automatic physical outcome or approval is supplied.')
        if s['historical']:
            nxt=next_action(None,'Return to the current view','Historical decisions are read-only.')
        elif run.get('state')=='COMPLETED':
            nxt=next_action(None,'This run is complete','Inspect its history or create another experiment.')
        elif q.get('GOVERNING_POLICY',{}).get('verdict')!='SATISFIED':
            nxt=next_action(None,'QA must restore the governing policy','The backend will not infer missing limits or grant permission.')
        elif ev['recommendation']=='ACCEPT' and not changed and not required and not actions and not s['release']['allowed']:
            target=next((x['id'] for x in r.values() if x['kind']=='lot' and x['id'].endswith('closure-c02')),None)
            nxt=next_action('change_context','Try a new-supplier cap batch','The original example tests cover this baseline. Make the packaging change explicit, then inspect what remains covered.',{'run_id':run['id'],'field':'closure_lot_id','value':target})
        elif a and a['status']=='PROPOSED':
            nxt=next_action('approve_action','Review the change plan','QA reviews the proposed comparison and the fresh-test plan before execution.',{'action_id':a['id']})
        elif a and a['status']=='APPROVED':
            nxt=next_action('execute_action','Apply the approved setup','This records the approved fictional setup; it does not predict a better seal.',{'action_id':a['id']})
        elif a and a['status']=='EXECUTED':
            nxt=next_action('open_study','Start the required fresh verification','Old tests cannot complete a separately required post-action verification.',{'run_id':run['id'],'action_id':a['id']})
        elif a and a['status']=='VERIFYING' and any(x['study_id'] in a.get('verified_study_ids',[]) for x in ev.get('study_checks',[])):
            nxt=next_action('assess_action','Review the new verification','QA must assess the independently complete new evidence.',{'action_id':a['id']})
        elif a and a['status']=='VERIFYING' and any(x.get('passing') and r[x['study_id']].get('action_id')==a['id'] for x in ev.get('study_checks',[])) and q.get('REQUIRED_SOURCE_HEALTH',{}).get('verdict')=='SATISFIED':
            nxt=next_action('assess_action','Review the new verification','Passing evidence is not yet a completed QA recovery review.',{'action_id':a['id']})
        elif ev['recommendation']!='ACCEPT' and (ev['recommendation']=='REJECT' or (q.get('FUNCTIONAL_ENDPOINT',{}).get('verdict')=='UNKNOWN' and any(x['kind']=='functional' and x.get('outcome')=='FAIL' and x['id'] in q.get('FUNCTIONAL_ENDPOINT',{}).get('evidence_refs',[]) for x in r.values()))):
            verified=next((x for x in reversed(actions) if x['status']=='VERIFIED'),None)
            failed=next((x for x in reversed(studies) if x['id'] in ev['study_ids'] and any(f['kind']=='functional' and f.get('study_id')==x['id'] and f.get('outcome')=='FAIL' and f['id'] in q.get('FUNCTIONAL_ENDPOINT',{}).get('evidence_refs',[]) for f in r.values())),None)
            if verified and failed and verified.get('verified_study_ids'):
                nxt=next_action('disposition_study','Review the prior failed study','Retain the genuine failure and record a scoped QA determination supported by the verified fresh study.',{'study_id':failed['id'],'verification_study_id':verified['verified_study_ids'][-1],'action_id':verified['id']})
            elif not incidents:
                nxt=next_action('investigate','Describe the observed failure','A supplied failure needs an investigation; a new PASS cannot erase it.',{'run_id':run['id']})
            elif not any(x['kind']=='hypothesis' and x.get('investigation_id')==incidents[-1]['id'] for x in r.values()):
                nxt=next_action('hypothesis','Record a possible explanation','Compare possibilities before claiming a cause.',{'investigation_id':incidents[-1]['id']})
            elif not a:
                nxt=next_action('propose_action','Plan a controlled comparison','Choose a reviewed alternate setup and define fresh verification; the app has not discovered an optimal setting.',{'investigation_id':incidents[-1]['id']})
            else:
                nxt=next_action(None,'Verification remains unresolved','The current trial did not establish recovery. Review the recorded problem and plan an appropriate further comparison.')
        elif not current and not prior_applies:
            nxt=next_action('open_study','Start tests for this configuration','The earlier qualification does not cover this cap/supplier combination.',{'run_id':run['id']})
        elif state and not state['specimens']:
            nxt=next_action('measure_batch','Enter three specimen readings','Record fictional application-torque observations against this required set. An empty plan is not qualification.',{'study_id':current['id']})
        elif state and not state['has_results'] and state.get('wait_hours_remaining',0)>0:
            nxt=next_action('demo_controls','Advance the fictional test wait','Use the clearly labelled demonstration clock controls. No physical test is performed.')
        elif q.get('REQUIRED_SOURCE_HEALTH',{}).get('verdict')!='SATISFIED':
            nxt=next_action('demo_controls','Refresh the fictional record feed','The demo feed is stale. This control sets a synthetic freshness flag; it is not real source reconciliation.')
        elif state and not state['has_results']:
            nxt=next_action('functional','Record the independent leak result','Supply your own fictional outcome after the wait. Torque does not determine it.',{'study_id':current['id']})
        elif ev['recommendation']!='ACCEPT':
            nxt=next_action('measure_batch','Review and complete the required evidence','Inspect missing eligibility, count, conformance or independent-result requirements. Do not overwrite a genuine failure.',{'study_id':current['id']} if current else {})
        elif s['release']['active_hold_count']:
            nxt=next_action('resolve_hold','Review and resolve the production pause','Tests are complete; the recorded pause still needs QA resolution.',{'run_id':run['id']})
        elif not s['release']['allowed']:
            nxt=next_action('authorize','Authorize bounded simulated production','QA permission is separate from passing tests. Review the condition and choose unit/time limits.',{'run_id':run['id']})
        else:
            nxt=next_action('produce','Record authorized sample units','A live scoped QA permission is present. The server rechecks it at use.',{'run_id':run['id']})
        checks=q.get('FUNCTIONAL_ENDPOINT',{})
        title='Simulated continuation authorized' if s['release']['allowed'] else 'Tests complete; production still awaits QA' if ev['recommendation']=='ACCEPT' else 'A recorded condition failed' if ev['recommendation']=='REJECT' else 'Production paused: evidence remains unresolved'
        reference_tests=[x for x in r.values() if previous and x['kind']=='functional' and x.get('study_id')==previous['id']]
        return {'product':r.get(run.get('product_id'),{}).get('label','Fictional bottled lotion'),'quantity':'100 g bottled lotion',
            'previous_study':{'id':previous['id'] if previous else None,'label':previous.get('label') if previous else 'No earlier study',
                'date':previous.get('created_at',previous.get('available_at')) if previous else None,'applies':prior_applies,
                'recorded_results':len(reference_tests),'scope':previous_scope},'rows':changes,'changed':changed,
            'physical_context':'A different cap or supplier can change how the assembled package seals or behaves during ageing. A physical test is required to establish performance; this app does not predict it.',
            'coverage_reason':'The earlier record targets the original configuration and its explicitly covered C03 alternative. The changed condition is outside that recorded approval.' if not prior_applies else 'The earlier record covers these identities. Any separately required new verification must still be completed; test readiness is not production permission.',
            'affected_scope':{'run_id':run['id'],'run':run['label'],'line':run['line'],'planned_units':run.get('target_units'),
                'description':'Further simulated production on this selected run. Other runs retain their own inputs and are checked independently.'},
            'title':title,'evidence':ev['recommendation'],'permission_granted':s['release']['allowed'],
            'next':nxt,'current_test_set':state,'minimum_specimens':r.get(run.get('policy_id'),{}).get('minimum_specimens'),
            'hold_reason':next((x['reason'] for x in ev['requirements'] if x['verdict']!='SATISFIED'),'Applicable tests complete; explicit QA review and permission remain separate.'),
            'containment_scope':'Potential impact counts cover the whole saved experiment; they are separate from this selected run’s future permission.'}

    def audit_read(self, wid, actor, action, detail):
        with self.store.transaction() as c:
            self._workspace(c, wid)
            self._audit(c, wid, actor, action, "READ", detail)
