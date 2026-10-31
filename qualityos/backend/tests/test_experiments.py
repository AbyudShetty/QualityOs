"""User choices, non-destructive organization and atomic varied readings."""
import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from qualityos.api import create_app
from qualityos.scenarios import START, seed_records
from qualityos.security import initialise_accounts
from qualityos.service import Service
from test_workflow import command, find, snap, system


def create(c,**setup):
    response=c.post('/api/v1/demo/workspaces',json={'name':'User-chosen packaging experiment','setup':setup})
    assert response.status_code==200,response.text
    return response.json()['workspace_id']


@pytest.mark.parametrize('cap,machine,expected',[('ORIGINAL','BASELINE','ACCEPT'),('UNTESTED','BASELINE','HOLD'),('COVERED','BASELINE','ACCEPT'),('ORIGINAL','ALTERNATE','HOLD')])
def test_chosen_inputs_determine_initial_readiness(system,cap,machine,expected):
    _,c,*_=system
    w=create(c,cap=cap,machine=machine)
    s=snap(c,w)
    assert s['decision']['recommendation']==expected
    assert s['workspace']['purpose']=='USER_EXPERIMENT'
    assert not find(s,'guide') and not find(s,'unit')


def test_custom_inputs_are_persisted_and_do_not_inherit_qualification(system):
    app,c,*_=system
    w=create(c,bottle='CUSTOM',bottle_name='My bottle batch',cap='CUSTOM',cap_name='My cap batch',machine='CUSTOM',machine_name='My application setup',machine_torque='1.07')
    s=snap(c,w)
    assert s['records'][s['run']['bottle_lot_id']]['label']=='My bottle batch'
    assert s['records'][s['run']['closure_lot_id']]['label']=='My cap batch'
    assert s['records'][s['run']['config_id']]['torque_setting']=='1.07'
    assert s['decision']['recommendation']=='HOLD'
    assert app.state.store.semantic_digest(w)==app.state.store.replay_digest(w)
    before=c.get('/api/v1/workspaces').json()
    assert c.post('/api/v1/demo/workspaces',json={'setup':{'machine':'CUSTOM','machine_name':'Bad setup','machine_torque':'NaN'}}).status_code==422
    assert c.get('/api/v1/workspaces').json()==before


def test_varied_readings_user_chosen_outcome_and_timing(system):
    _,c,*_=system
    w=create(c,cap='UNTESTED')
    s=snap(c,w);rid=s['run']['id']
    command(c,w,'open_study',{'run_id':rid})
    s=snap(c,w);study=find(s,'study')[-1]['id'];cal=find(s,'calibration','calibration-01')[0]['id']
    command(c,w,'measure_batch',{'study_id':study,'calibration_id':cal,'values':['0.98','1.00','1.03']})
    s=snap(c,w)
    assert {m['value'] for m in s['decision']['measurements']}=={'0.98','1.00','1.03'}
    assert len({m['sample_id'] for m in s['decision']['measurements']})==3
    assert s['test_sets'][-1]['wait_hours_remaining']==24
    command(c,w,'functional',{'study_id':study,'outcome':'PASS'},status=409)
    command(c,w,'advance',{'hours':24})
    command(c,w,'refresh_source',{'run_id':rid})
    command(c,w,'functional',{'study_id':study,'outcome':'PASS'})
    s=snap(c,w)
    assert s['decision']['recommendation']=='ACCEPT'
    assert any(h['status']=='ACTIVE' for h in find(s,'hold'))
    assert not find(s,'permit')  # A chosen PASS is not a QA approval.
    assert any(e.get('detail',{}).get('payload',{}).get('values')==['0.98','1.00','1.03'] for e in s['events'])


def test_batch_validation_is_atomic_and_idempotent(system):
    app,c,w,*_=system
    s=snap(c,w);study=find(s,'study','study-initial-1')[0]['id'];cal=find(s,'calibration','calibration-01')[0]['id']
    before=app.state.store.semantic_digest(w)
    command(c,w,'measure_batch',{'study_id':study,'calibration_id':cal,'values':['1.00','NaN','1.02']},status=422)
    assert app.state.store.semantic_digest(w)==before
    s=snap(c,w)
    body={'expected_context_revision':s['workspace']['revision'],'payload':{'study_id':study,'calibration_id':cal,'values':['0.99','1.01','1.02']}}
    headers={'Idempotency-Key':'batch-retry-key-unique'};url=f'/api/v1/workspaces/{w}/commands/measure_batch'
    initial_count=len(find(s,'measurement'))
    assert c.post(url,json=body,headers=headers).status_code==200
    retry=c.post(url,json=body,headers=headers)
    assert retry.status_code==200 and retry.json()['replayed']
    assert len(find(snap(c,w),'measurement'))==initial_count+3


def test_developer_fixtures_are_separate_and_organization_preserves_permissions(system):
    app,c,w,*_=system
    fixture=c.post('/api/v1/demo/workspaces',json={'name':'An isolated automated check','purpose':'AUTOMATION_TEST'}).json()['workspace_id']
    assert fixture not in {x['id'] for x in c.get('/api/v1/workspaces').json()}
    assert fixture in {x['id'] for x in c.get('/api/v1/workspaces?include_earlier=true').json()}
    s=snap(c,w);rid=s['run']['id']
    command(c,w,'authorize',{'run_id':rid,'decision_id':s['decision']['id'],'fingerprint':s['decision']['applicability_fingerprint']})
    before=app.state.store.semantic_digest(w);revision=snap(c,w)['workspace']['revision']
    response=c.post(f'/api/v1/workspaces/{w}/organize',json={'name':'My retained experiment','purpose':'LEGACY_SESSION'})
    assert response.status_code==200
    assert app.state.store.semantic_digest(w)==before and snap(c,w)['workspace']['revision']==revision
    assert w not in {x['id'] for x in c.get('/api/v1/workspaces').json()}
    command(c,w,'produce',{'run_id':rid,'units':1})
    assert c.post(f'/api/v1/workspaces/{w}/organize',json={'name':'My retained experiment','purpose':'USER_EXPERIMENT'}).status_code==200
    assert w in {x['id'] for x in c.get('/api/v1/workspaces').json()}


def test_version_one_migration_preserves_old_sessions_and_decisions(tmp_path,monkeypatch):
    import qualityos.store as module
    path=tmp_path/'old.sqlite';creds=tmp_path/'private.json'
    migrations=module.MIGRATIONS
    with monkeypatch.context() as m:
        m.setattr(module,'MIGRATIONS',migrations[:1])
        store=module.Store(path);initialise_accounts(store,creds);service=Service(store)
        for wid,name in [('old-user','My earlier work'),('old-test','Browser QA historical check')]:
            with store.transaction() as conn:
                conn.execute(text("INSERT INTO workspaces VALUES (:w,:n,:clock,'SYNTHETIC_DEMO',0,0,'packpair-v1/S1')"),{'w':wid,'n':name,'clock':START})
                ws=service._workspace(conn,wid)
                service._commit(conn,ws,{},seed_records(wid+'-'),{'id':'qa','role':'QUALITY_ENGINEER'},'WORKSPACE_CREATED',str(uuid.uuid4()),'legacy-fixture',{})
        original=store.semantic_digest('old-user');original_decision=service.snapshot('old-user')['decision']['id']
        store.engine.dispose()
    app=create_app(path,creds)
    assert app.state.store.semantic_digest('old-user')==original
    old=app.state.service.snapshot('old-user')
    assert old['workspace']['purpose']=='LEGACY_SESSION' and old['decision']['id']==original_decision
    assert app.state.service.snapshot('old-test')['workspace']['purpose']=='AUTOMATION_TEST'
    with app.state.store.engine.connect() as conn: assert conn.execute(text('SELECT max(version) FROM schema_version')).scalar()==2
