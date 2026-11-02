"""Publish actual remediation checks without changing original review evidence."""
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from qualityos.evaluation import run_evaluation
from qualityos.security import utcnow

root=Path(__file__).resolve().parents[1]
workspace=root.parent
out=root/'docs/validation/review-remediation'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

backend=ET.parse(out/'backend.xml').getroot()
tests=list(backend.iter('testcase'))
failed=[t.attrib['name'] for t in tests if t.find('failure') is not None or t.find('error') is not None]
assert not failed,failed
frontend=read(out/'frontend.json');assert frontend['numFailedTests']==0
checks=read(root/'docs/validation/checks.json')
assert checks['typescript_and_build']=='PASSED' and checks['contract_generation']=='PASSED'
browser=read(out/'browser.json');assert not browser.get('failure') and not browser.get('errors')
contrast=read(out/'contrast.json');assert not any(x['failures'] for x in contrast['reports'])

before=ET.parse(root/'var/review-remediation-before.xml').getroot()
before_failures=[t.attrib['name'] for t in before.iter('testcase') if t.find('failure') is not None or t.find('error') is not None]
(out/'before.json').write_text(json.dumps({'basis':'New frozen expectation tests run against unpatched code; includes missing new contracts, not only demonstrated bugs',
    'tests':len(list(before.iter('testcase'))),'failures':before_failures},indent=2),encoding='utf-8')

baseline=read(workspace/'qualityos_independent_review/artifacts/preservation-before.json')
changed=[p for p,h in baseline.items() if not (workspace/p).exists() or sha(workspace/p)!=h]
protected=[p for p in baseline if not p.startswith('qualityos/') or p in {'qualityos/scenarios/expected-v1.json','qualityos/backend/qualityos/store.py','qualityos/backend/qualityos/security.py'}]
assert not set(changed)&set(protected),'A protected original changed'
(out/'preservation.json').write_text(json.dumps({'basis':'Comparison with independent-review file baseline; expected source/build changes are listed, not claimed unchanged',
    'protected_files':len(protected),'all_protected_matched':True,'changed_original_paths':changed,
    'root_manual_and_pdf_unchanged':all(p not in changed for p in ['QUALITYOS_USER_MANUAL.md','QUALITYOS_VISUAL_USER_GUIDE.pdf']),
    'frozen_v1_sha256':sha(root/'scenarios/expected-v1.json'),'user_runtime_store_used':False},indent=2),encoding='utf-8')

evaluation=run_evaluation();assert evaluation['passed']==evaluation['total']
(out/'evaluation-v1-retained.json').write_text(json.dumps(evaluation,indent=2),encoding='utf-8')
names={t.attrib['name'].split('[')[0] for t in tests}
groups={
 'R01':['test_governing_policy_never_defaults_to_accept','test_invalid_policy_blocks_actual_authorization_transaction'],
 'R02':['test_complete_flag_does_not_replace_actual_identity'],
 'R03':['test_successor_corrections_preserve_chain_and_historical_attestors'],
 'R04':['test_operator_cannot_correct_a_failed_result','test_unhandled_failure_returns_controlled_json_and_rolls_back'],
 'R05':['test_sparse_required_recovery_cannot_resolve_authorize_or_produce','test_required_action_blocks_an_existing_permission_before_any_new_study'],
 'R06':['test_optional_action_does_not_block_unrelated_valid_production'],
 'R07':['test_empty_required_set_is_not_coverage_or_qualification','test_mandatory_inconclusive_cannot_borrow_old_proof'],
 'R08':['test_explicit_supplemental_inconclusive_preserves_independent_proof'],
 'R09':['test_three_sparse_studies_cannot_pool_to_qualification'],
 'R10':['test_real_failure_needs_qa_study_determination_not_newer_pass'],
 'R11':['test_real_failure_needs_qa_study_determination_not_newer_pass','test_scoped_determination_cannot_clear_another_unresolved_failure'],
 'R12':['test_old_scope_impact_has_durable_containment_without_current_blanket_hold'],
 'R13':['test_unapproved_cartesian_envelope_cannot_accept'],
 'R14':['test_varied_readings_user_chosen_outcome_and_timing'],
 'R15':['test_frozen_independent_cases']}
declared=read(root/'scenarios/expected-review-v2.json')
for case in declared['cases']:
    expected=groups[case['id']];assert set(expected)<=names,(case['id'],expected)
    case.update(executed_test_functions=expected,result='PASSED_DECLARED_SOFTWARE_BOUNDARY')
declared['limits']='Development regressions and developer browser operation, not blind external certification, physical trials or proof of industrial value'
declared['browser_checks']=len(browser['checks'])
(out/'evaluation-review-v2.json').write_text(json.dumps(declared,indent=2),encoding='utf-8')
report={'completed_at':utcnow(),'provenance':'SYNTHETIC_SOFTWARE_ONLY',
    'backend':{'tests':len(tests),'failed':len(failed),'new_review_regressions':sum('review_regressions' in t.attrib.get('classname','') for t in tests)},
    'frontend':{'tests':frontend['numTotalTests'],'passed':frontend['numPassedTests']},
    'typescript_no_emit':'PASSED','production_build':'PASSED','contract_generation':'PASSED',
    'browser':{'checks':len(browser['checks']),'runtime_errors':browser['errors'],'basis':browser.get('workflow_basis')},
    'contrast':{'checked_text_elements':sum(x['checked'] for x in contrast['reports']),'failures':0,'limits':contrast['basis']},
    'frozen_v1_cases':{'passed':evaluation['passed'],'total':evaluation['total'],'reference':'Limited separately specified checklist, not a validated industrial SOP'},
    'declared_review_groups':len(declared['cases']),'protected_originals':len(protected),
    'commands':['qualityos/verify.ps1','PYTHONPATH=backend .venv/Scripts/python.exe -m pytest backend/tests -q --tb=short --junitxml=docs/validation/review-remediation/backend.xml',
                'npm test -- --reporter=json --outputFile=../docs/validation/review-remediation/frontend.json',
                'node node_modules/typescript/bin/tsc --noEmit --incremental false','npm run build',
                'node web/scripts/review-remediation-check.mjs','node web/scripts/review-remediation-contrast.mjs'],
    'limitations':['Existing Starlette multipart PendingDeprecationWarning','No independent fresh-user comprehension study','No clean online environment or factory/physical validation','No new scaling benchmark or new power-loss test']}
(out/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k in ['backend','frontend','browser','contrast','frozen_v1_cases','declared_review_groups']},indent=2))
