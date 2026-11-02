"""Independent review boundaries; expectations frozen in expected-review-v2.json."""
from copy import deepcopy

import pytest

from qualityos.domain import evaluate
from qualityos.scenarios import START, seed_records
from test_workflow import system, command, find, snap


def review(c,w,op,**extra):
    s=snap(c,w)
    return command(c,w,op,{'run_id':s['run']['id'],'decision_id':s['decision']['id'],
                         'fingerprint':s['decision']['applicability_fingerprint'],**extra})


def fresh(c,w,outcome='PASS',count=3,action_id=None,purpose='REQUIRED'):
    s=snap(c,w);before=set(s['records'])
    payload={'run_id':s['run']['id']}
    if purpose!='REQUIRED':payload['purpose']=purpose
    if action_id:payload['action_id']=action_id
    command(c,w,'open_study',payload)
    s=snap(c,w)
    study=next(x['id'] for i,x in s['records'].items() if i not in before and x['kind']=='study')
    cal=find(s,'calibration','calibration-01')[0]['id']
    command(c,w,'measure',{'study_id':study,'calibration_id':cal,'value':'1.00','count':count})
    command(c,w,'advance',{'hours':24})
    command(c,w,'refresh_source',{'run_id':s['run']['id']})
    command(c,w,'functional',{'study_id':study,'outcome':outcome})
    return study


@pytest.mark.parametrize('change',['missing','kind','revision','minimum','boolean_count','limits','dwell','incomplete'])
def test_governing_policy_never_defaults_to_accept(change):
    r=seed_records();run=r['run-1'];p=r[run['policy_id']]
    if change=='missing':del r[run['policy_id']]
    elif change=='kind':p['kind']='note'
    elif change=='revision':p['revision']=0
    elif change=='minimum':p['minimum_specimens']=0
    elif change=='boolean_count':p['minimum_specimens']=True
    elif change=='limits':p['torque_high']='NaN'
    elif change=='dwell':p['dwell_hours']=-24
    else:del p['torque_low']
    result=evaluate(run,r,START)
    assert result['recommendation']!='ACCEPT'
    assert any(q['type']=='GOVERNING_POLICY' and q['verdict']!='SATISFIED' for q in result['requirements'])


def test_invalid_policy_blocks_actual_authorization_transaction(system):
    app,c,w,*_=system
    s=snap(c,w);policy=deepcopy(s['records'][s['run']['policy_id']]);policy['minimum_specimens']=0
    with app.state.store.transaction() as connection:app.state.store.put(connection,w,policy)
    # Internal corrupt-input fixture, not a public policy/corruption endpoint.
    s=snap(c,w)
    assert s['decision']['recommendation']=='HOLD'
    command(c,w,'authorize',{'run_id':s['run']['id'],'decision_id':s['decision']['id'],'fingerprint':s['decision']['applicability_fingerprint']},status=409)
    assert not find(snap(c,w),'permit')


def test_unhandled_failure_returns_controlled_json_and_rolls_back(system,monkeypatch):
    app,c,w,*_=system
    before=app.state.store.semantic_digest(w)
    def fail(*args,**kwargs):raise RuntimeError('Internal-only injected detail')
    monkeypatch.setattr(app.state.service,'_commit',fail)
    r=command(c,w,'correct_evidence',{'evidence_id':find(snap(c,w),'functional')[0]['id'],'outcome':'FAIL'},status=500)
    assert r.json()['code']=='INTERNAL_ERROR'
    assert 'Internal-only' not in r.text
    assert app.state.store.semantic_digest(w)==before


@pytest.mark.parametrize('field',['product_id','bottle_lot_id','closure_lot_id','config_id'])
def test_complete_flag_does_not_replace_actual_identity(field):
    r=seed_records();run=r['run-1'];del r[run[field]]
    assert evaluate(run,r,START)['recommendation']=='HOLD'


def test_successor_corrections_preserve_chain_and_historical_attestors(system):
    app,c,w,*_=system
    s=snap(c,w);target=find(s,'functional','leak-initial-1-1')[0]
    original_cut=s['decision']['id'];previous=target
    for outcome in ['FAIL','INCONCLUSIVE','PASS']:
        command(c,w,'correct_evidence',{'evidence_id':previous['id'],'outcome':outcome})
        s=snap(c,w)
        new=next(x for x in find(s,'functional') if x.get('supersedes_id')==previous['id'])
        assert new['outcome']==outcome and new['corrected_by']
        assert new['original_attestor']==target.get('attestor')
        assert s['records'][previous['id']]['outcome']==previous['outcome']
        previous=new
    assert s['decision']['recommendation']=='ACCEPT'
    before=app.state.store.semantic_digest(w)
    command(c,w,'correct_evidence',{'evidence_id':target['id'],'outcome':'FAIL'},status=409)
    assert app.state.store.semantic_digest(w)==before
    history=c.get(f'/api/v1/workspaces/{w}/snapshot',params={'decision_id':original_cut}).json()
    assert history['records'][target['id']]['outcome']=='PASS'
    assert previous['id'] not in history['records']
    assert app.state.store.replay_digest(w)==app.state.store.semantic_digest(w)


def test_operator_cannot_correct_a_failed_result(system):
    _,c,w,users,*_=system
    target=find(snap(c,w),'functional')[0]['id']
    result=c.post('/api/v1/auth/session',json={'username':'operator','password':users['operator']['password']})
    c.headers['X-CSRF-Token']=result.json()['csrf_token']
    command(c,w,'correct_evidence',{'evidence_id':target,'outcome':'PASS'},status=403)


def action(c,w,required=True):
    s=snap(c,w);rid=s['run']['id']
    command(c,w,'investigate',{'run_id':rid,'title':'Review recovery condition','problem_definition':'A new independent verification is required before this reviewed condition may continue.'})
    incident=find(snap(c,w),'investigation')[-1]['id']
    payload={'investigation_id':incident,'config_id':s['run']['config_id'],
             'verification_plan':'Collect a complete fresh independently sufficient verification set.'}
    if not required:payload['required_for_release']=False
    command(c,w,'propose_action',payload)
    aid=find(snap(c,w),'action')[-1]['id']
    command(c,w,'approve_action',{'action_id':aid});command(c,w,'execute_action',{'action_id':aid})
    return aid


def test_sparse_required_recovery_cannot_resolve_authorize_or_produce(system):
    _,c,w,*_=system
    aid=action(c,w);fresh(c,w,count=1,action_id=aid)
    command(c,w,'assess_action',{'action_id':aid},status=409)
    s=snap(c,w)
    p={'run_id':s['run']['id'],'decision_id':s['decision']['id'],'fingerprint':s['decision']['applicability_fingerprint']}
    command(c,w,'resolve_hold',p,status=409);command(c,w,'authorize',p,status=409)
    command(c,w,'produce',{'run_id':s['run']['id'],'units':1},status=409)
    assert not find(snap(c,w),'unit')


def test_optional_action_does_not_block_unrelated_valid_production(system):
    _,c,w,*_=system
    action(c,w,required=False)
    assert snap(c,w)['decision']['recommendation']=='ACCEPT'
    review(c,w,'authorize')
    command(c,w,'produce',{'run_id':snap(c,w)['run']['id'],'units':1})
    assert len(find(snap(c,w),'unit'))==1
    command(c,w,'advance',{'hours':2})
    assert snap(c,w)['packaging_change']['next']['operation']=='demo_controls'


def test_empty_required_set_is_not_coverage_or_qualification(system):
    _,c,w,*_=system
    command(c,w,'open_study',{'run_id':snap(c,w)['run']['id']})
    s=snap(c,w)
    assert s['decision']['recommendation']=='HOLD'
    assert next(q for q in s['decision']['requirements'] if q['type']=='EXACT_SCOPE_MATCH')['verdict']=='UNKNOWN'


def test_mandatory_inconclusive_cannot_borrow_old_proof(system):
    _,c,w,*_=system
    fresh(c,w,outcome='INCONCLUSIVE')
    assert snap(c,w)['decision']['recommendation']=='HOLD'


def test_explicit_supplemental_inconclusive_preserves_independent_proof(system):
    _,c,w,*_=system
    fresh(c,w,outcome='INCONCLUSIVE',purpose='SUPPLEMENTAL')
    assert snap(c,w)['decision']['recommendation']=='ACCEPT'


def test_three_sparse_studies_cannot_pool_to_qualification(system):
    _,c,w,*_=system
    s=snap(c,w);command(c,w,'change_context',{'run_id':s['run']['id'],'field':'closure_lot_id','value':find(s,'lot','closure-c02')[0]['id']})
    for _ in range(3):fresh(c,w,count=1)
    assert snap(c,w)['decision']['recommendation']=='HOLD'


def test_unapproved_cartesian_envelope_cannot_accept():
    r=seed_records();run=r['run-1'];study=r['study-initial-1']
    # Isolate the proposed envelope: the independent B02 control has its own
    # legitimate joint C03 approval, which would otherwise confound this probe.
    r.pop('study-initial-2')
    study['approved_envelope']['bottle_lot_id']=['bottle-b02']
    run.update(bottle_lot_id='bottle-b02',closure_lot_id='closure-c03')
    assert evaluate(run,r,START)['recommendation']!='ACCEPT'


def test_real_failure_needs_qa_study_determination_not_newer_pass(system):
    _,c,w,*_=system
    failed=fresh(c,w,'FAIL');aid=action(c,w)
    passed=fresh(c,w,'PASS',action_id=aid)
    command(c,w,'disposition_study',{'study_id':failed,'verification_study_id':passed,'action_id':aid},status=409)
    assert snap(c,w)['decision']['recommendation']!='ACCEPT'
    # A provisional fresh-set assessment can review only that action's new
    # records, while unresolved old failure still blocks production.
    command(c,w,'assess_action',{'action_id':aid})
    command(c,w,'disposition_study',{'study_id':failed,'verification_study_id':passed,'action_id':aid})
    s=snap(c,w)
    assert s['decision']['recommendation']=='ACCEPT'
    assert any(x['outcome']=='FAIL' for x in find(s,'functional') if x['study_id']==failed)
    assert not find(s,'permit')
    review(c,w,'resolve_hold');review(c,w,'authorize')


def test_required_action_blocks_an_existing_permission_before_any_new_study(system):
    _,c,w,*_=system
    review(c,w,'authorize')
    action(c,w)
    command(c,w,'produce',{'run_id':snap(c,w)['run']['id'],'units':1},status=409)
    assert not find(snap(c,w),'unit')


def test_scoped_determination_cannot_clear_another_unresolved_failure(system):
    _,c,w,*_=system
    first=fresh(c,w,'FAIL');second=fresh(c,w,'FAIL')
    aid=action(c,w);passed=fresh(c,w,'PASS',action_id=aid)
    command(c,w,'assess_action',{'action_id':aid})
    command(c,w,'disposition_study',{'study_id':first,'verification_study_id':passed,'action_id':aid})
    s=snap(c,w)
    assert s['decision']['recommendation']!='ACCEPT'
    command(c,w,'authorize',{'run_id':s['run']['id'],'decision_id':s['decision']['id'],'fingerprint':s['decision']['applicability_fingerprint']},status=409)
    command(c,w,'disposition_study',{'study_id':second,'verification_study_id':passed,'action_id':aid})
    assert snap(c,w)['decision']['recommendation']=='ACCEPT'


def test_old_scope_impact_has_durable_containment_without_current_blanket_hold(system):
    app,c,w,*_=system
    s=snap(c,w);rid=s['run']['id'];old=find(s,'functional','leak-initial-1-1')[0]['id']
    review(c,w,'authorize');command(c,w,'produce',{'run_id':rid,'units':1})
    old_unit=find(snap(c,w),'unit')[0]['id']
    command(c,w,'change_context',{'run_id':rid,'field':'closure_lot_id','value':find(s,'lot','closure-c02')[0]['id']})
    fresh(c,w);review(c,w,'resolve_hold');review(c,w,'authorize');command(c,w,'produce',{'run_id':rid,'units':1})
    command(c,w,'correct_evidence',{'evidence_id':old,'outcome':'FAIL'})
    s=snap(c,w)
    assert s['decision']['recommendation']=='ACCEPT'
    population={uid for hold in find(s,'containment') if hold['status']=='ACTIVE' for uid in hold['unit_ids']}
    assert population=={old_unit}
    command(c,w,'disposition',{'unit_ids':[old_unit],'disposition':'HELD'})
    assert app.state.store.replay_digest(w)==app.state.store.semantic_digest(w)
    command(c,w,'disposition',{'unit_ids':[old_unit],'disposition':'ACCEPTED'})
    latest=next(x for x in find(snap(c,w),'functional') if x.get('supersedes_id')==old)
    command(c,w,'correct_evidence',{'evidence_id':latest['id'],'outcome':'INCONCLUSIVE'})
    s=snap(c,w)
    assert s['decision']['recommendation']=='ACCEPT'
    assert {i for h in find(s,'containment') if h['status']=='ACTIVE' for i in h['unit_ids']}=={old_unit}

