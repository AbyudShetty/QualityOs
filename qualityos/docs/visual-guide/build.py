"""Build an annotated PDF from authentic, unmodified application screenshots.

Annotations are PDF vectors; screenshot pixels are never painted over or invented.
Run capture.mjs against the isolated review store before this builder.
"""
import hashlib
import html
import json
import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT = ROOT / 'QUALITYOS_VISUAL_USER_GUIDE.pdf'
CAPTURE = json.loads((HERE / 'captures.json').read_text(encoding='utf-8'))
MANUAL = ROOT / 'QUALITYOS_USER_MANUAL.md'
if hashlib.sha256(MANUAL.read_bytes()).hexdigest() != CAPTURE['markdown_manual_sha256']:
    raise RuntimeError('Markdown manual differs from the untouched capture baseline')

for name, filename in [('Body','segoeui.ttf'),('Bold','segoeuib.ttf'),('Mono','consola.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/' + filename))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Bold', italic='Body', boldItalic='Bold')
W,H = landscape(A4)
INK = colors.HexColor('#173B2F')
FOREST = colors.HexColor('#255B45')
CREAM = colors.HexColor('#F6F4EE')
PALE = colors.HexColor('#EAF0E5')
MUTED = colors.HexColor('#53655A')
LINE = colors.HexColor('#D5DFD3')
ORANGE = colors.HexColor('#B34F23')
WHITE = colors.white


def step(title, text):
    return (title, text)


def page(key, section, title, subtitle, figures, steps, result, next_step, mode='detail'):
    return dict(key=key, section=section, title=title, subtitle=subtitle, figures=figures,
                steps=steps, result=result, next_step=next_step, mode=mode)


PAGES = [
    dict(key='cover', special='cover'),
    dict(key='contents', special='contents'),
    page('purpose','GET ORIENTED','The question QualityOS answers',
         'Do the saved tests still support the bottles, caps and machine setup we are about to use?',
         ['02-introduction'],[
             step('Start with the factory situation','Lotion is filled into bottles, caps are fitted, and packages are tested. A changed material or setup may need different evidence.'),
             step('The software checks the connection','It connects the chosen condition to applicable records and review decisions before allowing saved sample production.'),
             step('Know the boundary','You supply fictional readings and leak outcomes. The app saves and checks them; it does not calculate physical leaks.')],
         'A missing test is an evidence gap. It is not proof that the new caps are defective.',
         'Launch the app, then sign in as qa.', mode='context'),
    page('login','GET ORIENTED','Launch once. Sign in as the reviewer.',
         'From the LOREAL folder: npm start. Open http://127.0.0.1:8107/start and keep the terminal running.',
         ['01-login'],[
             step('Username: qa','This demo account can complete tests and quality approvals. The displayed reviewer name is fictional.'),
             step('Use your private local password','Open qualityos/var/local-credentials.json on your device and use the password under qa. No password is printed in this guide.'),
             step('Select Open workspace','operator cannot sign QA approvals; viewer is read-only. If an old server is running, stop it with Ctrl+C before npm start.')],
         'The Getting started page opens. Stop the server with Ctrl+C; saved records remain.',
         'Choose a starting point. npm run dev is an alias for the same complete launch.'),
    page('choose','GET ORIENTED','Choose the experiment you want to explore',
         'An experiment is one saved practice session with its own inputs, test records and decisions.',
         ['03-starting-points'],[
             step('Use approved example','For a first success, inspect preloaded passing evidence and learn the difference between test readiness and approval.'),
             step('Try untested caps','For the main walkthrough, choose C02 caps. Earlier example tests do not cover them; you will supply new evidence.'),
             step('Configure my experiment','Create fictional material identities or a machine setting. You still supply readings and independent outcomes yourself.')],
         'The next dialog lets you review your choices before any experiment is saved.',
         'This guide follows untested caps through failure, investigation and recovery.'),
    page('create','SET UP AN EXPERIMENT','Name it. Choose the materials and setup.',
         'Choose Try untested caps, then use these inputs for the worked example.',
         ['07-create-experiment'],[
             step('Give the session a useful name','Example: Guide 2 - New caps and verification. This name helps you reopen the right saved work later.'),
             step('Keep different caps C02','C01 means original covered caps. C02 means caps not covered by earlier tests. C03 is a different batch explicitly covered.'),
             step('Keep original machine setup v1','Use the original bottles and v1 now so the later comparison changes only the machine setup. Select Create experiment.')],
         'A new saved experiment opens with the chosen inputs. No new tests or units are automatically produced.',
         'Understand the tabs and selected run before entering results.'),
    page('navigation','SET UP AN EXPERIMENT','Four tabs. One saved experiment.',
         'The screenshot is an overview; the following pages magnify the controls you will use.',
         ['04-navigation'],[
             step('Use the four task tabs','Production setup: inputs and readiness. Tests & approval: test records and permission. Investigate a problem: reviewed changes. Decision history: past choices.'),
             step('Saved experiment selects your session','Changing this selector opens different saved work. It is not a list of factory departments or tasks to complete.'),
             step('Keep the main run selected','The first/main packaging run is the walkthrough subject. The second run is an independent comparison with its own records.')],
         'All four tabs describe the selected experiment/run; switching tabs does not create a new session.',
         'Open Production setup and read the decision.', mode='context'),
    page('paused','SET UP AN EXPERIMENT','Why the new-cap setup is paused',
         'C02 is not in the earlier example test coverage. Similar-looking materials do not inherit proof.',
         [{'id':'08-paused-setup','focus':1,'keep':[1],'crop_top':430}],[
             step('Read the current decision','More evidence needed means the current combination is not adequately supported. The run is paused; the app has not diagnosed a physical defect.'),
             step('Change inputs deliberately','Change an input lets you try a different bottle batch, cap batch or machine setup. Tests and permission are rechecked when the condition changes.')],
         'No sample production is allowed merely because an earlier setup passed.',
         'Go to Tests & approval to collect evidence for this combination.'),
    page('test-set','ENTER THE EVIDENCE','Start an empty test set first',
         'A test set attaches new specimen readings and the independent leak result to the selected condition.',
         ['09-start-test-set'],[
             step('Select Start a test set','Submit the dialog. This creates the container for evidence, not passing evidence itself.'),
             step('Read the prerequisite message','Without a fresh set, the app has nowhere appropriate to attach new readings. Completed sets stay in history; a new trial needs a new set.')],
         'Enter torque readings becomes available for the fresh test set.',
         'Enter three fictional readings with an eligible reference.'),
    page('readings','ENTER THE EVIDENCE','Enter readings for three separate specimens',
         'Torque is the twisting effort used to fit a cap. It is one check, not a leak prediction.',
         ['10-enter-readings'],[
             step('Check the selected test set','It should name C02 and original machine setup v1. Do not attach new data to an unrelated condition.'),
             step('Enter: 0.98, 1.00, 1.02','Use commas between readings. Each value creates one distinct fictional specimen. At least three eligible specimens are needed in this example.'),
             step('Choose T-01 reference certificate','Keep the eligible reference and the default assumed bound of 0.02. Select Save these readings in the fixed dialog footer.')],
         'The readings are saved. Test readiness remains incomplete because the independent leak endpoint is still missing.',
         'Account for the example 24-hour wait before supplying the leak outcome.'),
    page('time','ENTER THE EVIDENCE','Advance the demonstration clock',
         'Use Advance time (24 h remaining) after saving the readings.',
         ['11-advance-time'],[
             step('Enter 24 fictional hours','The required wait runs from each specimen observation. If you add a later reading, that specimen needs its own full wait.'),
             step('Submit the advance','This changes the saved scenario clock. It does not physically age a sample, perform a test, refresh records or renew permission.')],
         'The independent result can be recorded after the wait, but the record feed now needs a freshness confirmation.',
         'Select Confirm current records.'),
    page('freshness','ENTER THE EVIDENCE','Confirm the test records are current',
         'This is separate from choosing a test outcome.',
         ['12-confirm-records'],[
             step('Read what is being confirmed','In a factory, records arrive from equipment or people. The demo checks whether that feed is complete and sufficiently recent.'),
             step('Select Confirm current records','The time advance aged the previous freshness record. This explicit confirmation updates that record; it does not make a failed test pass.')],
         'The selected run has a current, complete fictional record feed.',
         'Choose an independent leak-test outcome.'),
    page('leak','ENTER THE EVIDENCE','Supply the independent leak-test outcome',
         'For the investigation route in this guide, deliberately choose FAIL.',
         ['13-independent-result'],[
             step('Use the same fresh test set','The independent result must refer to the specimens and condition just tested.'),
             step('Choose your fictional observation','PASS: no leak observed in the supplied test. FAIL: leak observed. INCONCLUSIVE: the test does not settle the question. None is predicted by torque.'),
             step('Save the selected result','FAIL is used here so you can explore investigation. For a direct passing route, choose PASS and skip to pause resolution once all checks are met.')],
         'The supplied FAIL becomes persisted evidence. The current condition is blocked despite eligible in-range torque readings.',
         'Inspect which requirement failed.'),
    page('failed-check','UNDERSTAND THE DECISION','A good torque value cannot overrule a leak failure',
         'Read the requirement verdicts, not only the overall status.',
         ['14-failed-check'],[
             step('Locate the independent leak requirement','The independent functional failure produces Condition failed for this condition. The torque check and tool-reference check answer different questions.'),
             step('Read torque as a different check','Met torque requirements can coexist with a failed leak requirement. These observations do not establish whether caps, setup or another mechanism caused a real leak.')],
         'The run remains paused. Adding a convenient PASS does not erase the earlier FAIL.',
         'Open Investigate a problem and describe what was actually observed.'),
    page('problem','INVESTIGATE A FAILURE','Describe the problem before naming a cause',
         'In Investigate a problem, select Describe a problem.',
         ['15-describe-problem'],[
             step('Use a recognizable title','Example: Leak result failed with the current caps.'),
             step('Record the observed mismatch','Name C02, setup v1, the eligible torque readings and the supplied leak failure. Ask what needs explaining; do not state an unproven cause as fact.')],
         'The problem description is saved and becomes the home for explanations and reviewed actions.',
         'Select Add a possible explanation.'),
    page('hypothesis','INVESTIGATE A FAILURE','Record a possibility that can be wrong',
         'A hypothesis is an explanation to test, not a confirmed root cause.',
         ['16-possible-explanation'],[
             step('State the possible interaction','Example: The application setup may interact with this cap batch.'),
             step('Describe a testable comparison','Try alternate setup v2 while retaining the same bottles and caps. Collect fresh torque and independent leak evidence afterward.'),
             step('Link observations only if justified','Supporting and challenging selections can stay empty. A failed result shows a problem; it does not by itself prove this particular explanation.')],
         'The saved explanation remains under test. It has not approved a change or granted production permission.',
         'Select Plan a change.'),
    page('plan','INVESTIGATE A FAILURE','Plan the change and the evidence needed afterward',
         'Choose a bounded comparison that you can evaluate.',
         ['17-plan-change'],[
             step('Choose alternate machine setup v2','Keep the bottles and caps unchanged for this comparison. A new setup needs evidence for its own condition.'),
             step('Specify fresh verification','Use three new eligible torque readings, a new 24-hour demonstration wait, current records and an independent leak result. Old proof cannot fill the fresh set\'s gaps.')],
         'This is a proposed experiment, not a claim that v2 fixes real C02 packages.',
         'Explain the review/action reason, then save the proposed change.'),
    page('reason','INVESTIGATE A FAILURE','What should go in the review note?',
         'A note explains a decision to a later reader. It is not a secret phrase or an AI prompt.',
         ['18-review-note'],[
             step('Answer: why this action, and what scope?','For this plan: compare the alternate setup with the same materials, using fresh torque and independent leak tests. Avoid claiming physical results you do not have.'),
             step('Use the editable example if helpful','Read it and adapt it to your experiment. Routine reading entry has an optional note; review steps require a meaningful explanation.'),
             step('Save the plan','A persuasive note cannot bypass an unmet test requirement. The server still checks the prerequisites.')],
         'The reason and proposed change are saved together. The action is still only proposed.',
         'Approve the plan before applying it.'),
    page('approve-apply','INVESTIGATE A FAILURE','Approve the plan, then apply the approved setup',
         'These are separate actions with different meanings.',
         [{'id':'19-approve-plan'},{'id':'20-apply-setup','offset':1}], [
             step('Approve the change plan','As qa, review the comparison and fresh-test plan. Submit a note explaining why the planned experiment is appropriate. This is not production approval.'),
             step('Apply the approved setup','After approval, record execution of that specific setup change. The experiment now uses v2, but still needs fresh verification.')],
         'The changed condition remains unqualified until independently sufficient new evidence is supplied.',
         'Start a new verification set from the action card.'),
    page('fresh-set','VERIFY THE CHANGE','Use a new set for the changed condition',
         'Fresh verification must be attached to the action and the post-change setup.',
         [{'id':'21-start-verification'},{'id':'22-fresh-readings','offset':1}], [
             step('Start a new verification set','Use this button on the action card after applying the approved setup. It links the set to this action.'),
             step('Check the set now names v2','In Tests & approval, enter readings against the fresh post-change set, not the earlier failed v1 condition.'),
             step('Enter: 0.99, 1.01, 1.02','Choose the eligible T-01 reference again. Save these fresh specimen records. Then advance 24 demonstration hours and confirm current records again.')],
         'The new measurements are independent records. Earlier observations and the original failure remain in history.',
         'Supply a new independent outcome after the fresh wait.'),
    page('fresh-pass','VERIFY THE CHANGE','Choose the fresh verification outcome',
         'Use PASS here to explore supported recovery; you are choosing the fictional observation.',
         ['23-fresh-pass'],[
             step('Verify the post-change test-set identity','The result must belong to the fresh verification set for C02 with v2.'),
             step('Supply PASS for this worked route','If you choose FAIL or INCONCLUSIVE instead, recovery should remain blocked. The software does not force a successful ending.')],
         'With all example requirements met, the evidence can become Tests ready. That still does not grant permission.',
         'Return to Investigate a problem to review the verification.'),
    page('assess','VERIFY THE CHANGE','Assess the fresh verification',
         'Select Review the new verification on the action card.',
         ['24-review-verification'],[
             step('Review the new results, not just the action','The server checks that the approved action was executed and has independently sufficient post-change evidence.'),
             step('Keep the conclusion bounded','Use the editable note or explain that the fresh set supports this changed condition in the fictional demonstration. It does not confirm physical causation or factory savings.')],
         'The action can be marked verified in simulation. Earlier adverse records are retained.',
         'Resolve the recorded pause in Tests & approval.'),
    page('resolve','REVIEW AND CONTINUE','Resolve the recorded pause',
         'This review closes the evidence-gap restriction. Permission is a separate next step.',
         ['25-resolve-pause'],[
             step('Explain what resolves the gap','Refer to the current materials/setup, eligible fresh readings and independent passing leak result after the wait.'),
             step('Select Resolve this pause','All relevant requirements must already be met. The note records your review; it cannot turn missing or failed evidence into a pass.')],
         'The pause is resolved, but sample production still requires a current bounded permission.',
         'Select Approve sample production.'),
    page('permission','REVIEW AND CONTINUE','Approve a bounded amount of sample production',
         'Tests ready, pause resolved and permission granted are distinct states.',
         ['26-bounded-permission'],[
             step('Maximum units: 10','This is a quantity budget for the displayed condition. Approving it does not create ten units.'),
             step('Permission duration: 30 minutes','This uses the demonstration clock. Explain the limited approval in the required review note, then select Approve within these limits.'),
             step('Use qa for the approval','An operator can enter observations but cannot sign this step. A changed condition, expiry or adverse information can invalidate permission.')],
         'A limited permission is saved for the reviewed condition. Nothing has been produced merely by approving it.',
         'Go to Production setup and choose how many sample units to record.'),
    page('produce','REVIEW AND CONTINUE','Record five units and inspect the saved result',
         'The server checks the current evidence, pause status and permission again at submission.',
         [{'id':'27-record-units'},{'id':'28-recovered-production','offset':2}], [
             step('Choose 5 fictional units','Use Record sample units. The count must fit the active permission\'s remaining quantity budget.'),
             step('Submit the request','This records sample packages in the database; it does not operate a machine.'),
             step('Expect five saved units','The result is persisted and should survive a reload.'),
             step('Five units remain in the budget','Trying six more against this ten-unit permission must be rejected. Complete run closes the run; leave it alone while exploring.')],
         'The evidence-to-review-to-production sequence has been completed for this fictional changed condition.',
         'Open Decision history to inspect how the result was reached.'),
    page('history','INSPECT WHAT HAPPENED','Read choices and consequences together',
         'Decision history answers: what was entered, what changed, and what did that imply?',
         ['29-decision-history'],[
             step('Read the saved timeline','It contains your readings, supplied outcomes, time advances and review actions. The original failure is not overwritten by recovery.'),
             step('Select an earlier decision','The historical selector opens an earlier knowledge cut. This lets you inspect the decision without applying later information retroactively.')],
         'Saved choices, evidence and decisions remain traceable. Simply viewing them grants no permission.',
         'Try an earlier failed decision, then return to current.'),
    page('past','INSPECT WHAT HAPPENED','Look at the past without editing it',
         'The banner identifies a historical, read-only view.',
         ['30-historical-view'],[
             step('Read the historical-view banner','This is what was known at that earlier point. It is not a statement that later evidence has disappeared.'),
             step('Choose Return to current','Do this before entering new data or authorizing work. Historical views intentionally disable writes.')],
         'Current and historical decisions coexist; later knowledge does not silently rewrite the earlier receipt.',
         'Inspect record details or export the experiment if you need the underlying data.'),
    page('details-export','INSPECT WHAT HAPPENED','Inspect a record. Export the experiment.',
         'Details are available when you want to go beyond the plain timeline.',
         [{'id':'38-record-details','focus':1,'crop_top':255},{'id':'40-export','offset':1}], [
             step('Open a timeline entry or record link','The drawer shows persisted fields and identifiers. Close it with its close button or Escape. A recorded relation does not itself prove causation.'),
             step('Use Export experiment','It downloads workspace-wide synthetic records/history as JSON, including when viewing an earlier decision. It is not a release certificate and does not include passwords.')],
         'You can inspect and preserve the evidence trail without altering it.',
         'The remaining pages cover optional experiments and advanced checks.'),
    page('custom','EXPLORE OTHER INPUTS','Choose your own fictional batches and setting',
         'Getting started → Configure my experiment → choose the custom options.',
         ['32-custom-inputs'],[
             step('Name a fictional cap batch','A new identity is saved separately. Similar names or appearance do not confer coverage from another batch.'),
             step('Name the custom machine setup','Keep your comparison recognizable so you know which tests apply to it later.'),
             step('Enter an intended setting, e.g. 1.05','This setting is an input. It does not generate torque readings or predict leakage. Create the experiment and supply new evidence explicitly.')],
         'The custom condition starts unsupported when earlier proof does not apply. This is intentional.',
         'Compare this with the explicitly covered alternative batch on the next page.'),
    page('covered','EXPLORE OTHER INPUTS','Different caps can already be covered',
         'Create an approved example, then choose C03 in the cap selector before saving.',
         [{'id':'41-covered-caps','focus':1,'crop_top':430}],[
             step('Read Tests ready for C03','The earlier approved example coverage explicitly includes this alternative batch. A change alone is not a reason to invent a failure.'),
             step('Still review the current exact condition','Evidence readiness is separate from a current, scoped permission. Obtain QA approval before recording sample units.')],
         'C02 pauses because coverage is missing; C03 can remain ready because coverage is explicit.',
         'Try an expired measuring-tool reference to explore a different evidence gap.'),
    page('expired','EXPLORE OTHER INPUTS','Good-looking numbers can still be unusable',
         'Use a separate new-cap experiment for this deliberately adverse check.',
         [{'id':'33-expired-reference'},{'id':'34-unusable-measurement','offset':2}], [
             step('Enter the same in-range readings','Start a fresh set and use 0.98, 1.00, 1.02.'),
             step('Deliberately select the expired T-02 reference','Save the readings. Their reference was ineligible at measurement time.'),
             step('Inspect the Unusable verdict','Range and reliability are separate. A later new reference cannot repair old measurements; collect fresh eligible observations.')],
         'Apparently satisfactory values cannot authorize continuation when their measurement reliability is unsupported.',
         'Use advanced controls only when deliberately exploring later discoveries.'),
    page('advanced','OPTIONAL ADVANCED CHECKS','Explore later discoveries without erasing history',
         'In Investigate a problem, expand the Advanced section.',
         ['31-advanced-controls'],[
             step('Withdraw a past reference','Model later learning that a reference was unreliable during a specified measurement period. This can change current implications for dependent units.'),
             step('Correct a saved leak result','Append a corrected version with a reason. The earlier version remains in history. Conflicting evidence does not become a clean pass automatically.'),
             step('Use a separate experiment first','These are deliberate adverse scenarios, not routine setup steps. Review the selected record and dates carefully.')],
         'Advanced discoveries change current assessment while retaining the original facts and decisions.',
         'The next page shows a scoped fictional reference withdrawal.'),
    page('withdraw','OPTIONAL ADVANCED CHECKS','Choose the reference and affected period',
         'This example is performed after the five recovery units were recorded.',
         ['42-reference-withdrawal'],[
             step('Select the reference used by fresh readings','The worked example withdraws T-01. Select the relevant reference, not another run\'s independent control.'),
             step('Start: 2026-01-16T00:00:00Z','This is the beginning of the fictional period affecting measurement reliability, not your computer\'s real current date.'),
             step('End: 2026-01-17T08:00:00Z','Use the demonstration dates shown for this fresh experiment. Record a review reason, then submit. Other experiments may have different relevant dates.')],
         'The current decision is recalculated. Dependent permission can be withdrawn and relevant units marked potentially affected.',
         'Inspect potential impact; affected does not automatically mean defective.'),
    page('impact','OPTIONAL ADVANCED CHECKS','Review affected samples and their handling',
         'This screenshot shows the actual five-unit result of the scoped fictional withdrawal.',
         [{'id':'43-potential-impact'},{'id':'44-handling-decision','offset':2}], [
             step('Inspect the potentially affected count','These samples depended on evidence affected by the selected withdrawal. This is not a measured defect or scrap count.'),
             step('Record a separate handling decision','QA can document how these potentially affected fictional units should be handled.'),
             step('Choose the handling outcome deliberately','HELD keeps the samples restricted while reviewing. ACCEPTED or REJECTED are recorded dispositions; they do not prove physical quality or grant new run permission.')],
         'The handling decision is saved separately from test readiness and production approval.',
         'Check the independent evaluation for declared software-case results.'),
    page('evaluation','OPTIONAL ADVANCED CHECKS','Run the declared software checks',
         'Production setup → Independent evaluation → Run independent evaluation.',
         ['37-evaluation'],[
             step('Run the comparison explicitly','The app evaluates the frozen synthetic cases and saves actual policy outcomes. Inspect all case outcomes for the individual cases.'),
             step('Interpret 20/20 correctly','It is a match count on declared software cases. The evidence-aware reference can match too. It is not factory accuracy, safety probability or proof of novelty.')],
         'Software correctness evidence is visible without being presented as a manufacturing trial.',
         'Reopen saved experiments or use the same tabs on mobile.'),
    page('saved','REOPEN AND RESUME','Find your saved experiments',
         'Getting started keeps your practice sessions separate and accessible.',
         ['36-saved-list'],[
             step('Open the experiment you actually want','Each session retains its own inputs, evidence and history. Successfully submitted actions persist; unsent form edits do not.'),
             step('Inspect earlier sessions separately','Earlier versions and development checks are preserved outside the normal selector. Keep in my experiments adds a relevant older session back to the ordinary list.')],
         'Stopping/restarting the server does not wipe your saved records. Create another experiment for a clean trial.',
         'On a narrow screen, use the menu icon to reach the same tabs.'),
    page('mobile','REOPEN AND RESUME','The same workflow on a narrow screen',
         'Open the menu icon at the top left to reveal navigation.',
         ['39-mobile-navigation'],[
             step('Choose the same four task tabs','There is no separate mobile workflow. The backend rules and saved decisions are the same.'),
             step('Select the intended saved experiment','Close the menu by navigating to a tab. Scroll down for the visible instructions and action controls.')],
         'Your saved evidence and permissions remain attached to the same experiment on mobile.',
         'Use the final reference pages when a step is blocked.'),
    dict(key='reference', special='reference'),
    dict(key='troubleshooting', special='troubleshooting'),
]

PAGE_NO={p['key']:i+1 for i,p in enumerate(PAGES)}
pdf=canvas.Canvas(str(OUTPUT),pagesize=(W,H),pageCompression=1)
pdf.setTitle('QualityOS - Visual User Guide')
pdf.setAuthor('QualityOS project')
pdf.setSubject('Annotated authentic screenshots, first-time walkthroughs and synthetic demonstration boundaries')
pdf.setCreator('QualityOS visual-guide builder / ReportLab')
LAYOUT=[]


def para(text,x,top,width,size=10.4,color=INK,bold=False,leading=None):
    style=ParagraphStyle('manual',fontName='Bold' if bold else 'Body',fontSize=size,
                         leading=leading or size*1.35,textColor=color,spaceAfter=0)
    p=Paragraph(html.escape(text).replace('\n','<br/>'),style)
    _,height=p.wrap(width,1000)
    p.drawOn(pdf,x,top-height)
    return height


def label(text,x,y,color=MUTED,size=8):
    pdf.saveState()
    pdf.setFillColor(color);pdf.setFont('Bold',size)
    t=pdf.beginText(x,y);t.setCharSpace(1.1);t.textOut(text);pdf.drawText(t)
    pdf.restoreState()


def brand(x,y,color=FOREST):
    pdf.setFillColor(color)
    for a,b in [(0,0),(9,0),(0,9),(9,9)]:pdf.roundRect(x+a,y+b,7,7,1,fill=1,stroke=0)
    pdf.setFont('Bold',12);pdf.drawString(x+27,y+2,'QualityOS')


def footer(i):
    pdf.setStrokeColor(LINE);pdf.setLineWidth(.6);pdf.line(28,35,W-28,35)
    pdf.setFont('Body',8);pdf.setFillColor(MUTED);pdf.drawString(28,20,'VISUAL USER GUIDE  /  LOCAL SYNTHETIC DEMONSTRATION')
    pdf.drawRightString(W-28,20,f'{i:02d} / {len(PAGES):02d}')
    if i!=2:
        pdf.setFillColor(FOREST);pdf.drawRightString(W-88,20,'Contents')
        pdf.linkRect('', 'contents', (W-132,15,W-86,30), relative=0, thickness=0)


def header(i,p):
    pdf.setFillColor(CREAM);pdf.rect(0,0,W,H,fill=1,stroke=0)
    brand(28,H-39);label('31 OCT 2026  /  INTERFACE EDITION',W-262,H-32)
    pdf.setStrokeColor(LINE);pdf.line(28,H-52,W-28,H-52)
    label(p.get('section','REFERENCE'),28,H-74,ORANGE)
    size=24
    while pdfmetrics.stringWidth(p.get('title',''),'Bold',size)>W-56:size-=.5
    para(p.get('title',''),28,H-85,W-56,size,bold=True)
    para(p.get('subtitle',''),28,H-119,W-56,10.6,MUTED)
    footer(i)


def crop_for(shot, mode='detail'):
    c=dict(shot['crop']);sw=shot['width'];sh=shot['height']
    if mode=='context':return c
    ts=shot['targets']
    # A large single container is already an explicit focus region.
    if len(ts)==1 and (ts[0]['h']>250 or ts[0]['w']>800):return c
    if ts:
        x=min(t['x'] for t in ts)-48;y=min(t['y'] for t in ts)-45
        right=max(t['x']+t['w'] for t in ts)+24;bottom=max(t['y']+t['h'] for t in ts)+26
        width=right-x
        if width<500:
            middle=(x+right)/2;x=middle-250;right=middle+250
        x=max(0,x);y=max(0,y);right=min(sw,right);bottom=min(sh,bottom)
        return dict(x=x,y=y,w=right-x,h=bottom-y)
    return c


def arrow(x1,y1,x2,y2):
    pdf.setStrokeColor(ORANGE);pdf.setFillColor(ORANGE);pdf.setLineWidth(1.4);pdf.line(x1,y1,x2,y2)
    a=math.atan2(y2-y1,x2-x1);length=6;side=2.4
    path=pdf.beginPath();path.moveTo(x2,y2)
    path.lineTo(x2-length*math.cos(a)+side*math.sin(a),y2-length*math.sin(a)-side*math.cos(a))
    path.lineTo(x2-length*math.cos(a)-side*math.sin(a),y2-length*math.sin(a)+side*math.cos(a))
    path.close();pdf.drawPath(path,fill=1,stroke=0)


def image_frame(spec,x,y,width,height,mode='detail'):
    spec={'id':spec} if isinstance(spec,str) else spec
    shot=CAPTURE['shots'][spec['id']];crop=crop_for(shot,spec.get('mode',mode))
    if spec.get('focus'):
        target=next(t for t in shot['targets'] if t['n']==spec['focus'])
        crop={'x':max(0,target['x']-22),'y':max(0,target['y']-20),
              'w':min(shot['width']-max(0,target['x']-22),target['w']+44),
              'h':min(shot['height']-max(0,target['y']-20),target['h']+40)}
    if spec.get('crop_top'):crop['h']=min(crop['h'],spec['crop_top'])
    pdf.setFillColor(WHITE);pdf.setStrokeColor(LINE);pdf.setLineWidth(.7)
    pdf.roundRect(x,y,width,height,6,fill=1,stroke=1)
    inset=8;scale=min((width-2*inset)/crop['w'],(height-2*inset)/crop['h'])
    iw,ih=crop['w']*scale,crop['h']*scale;ix=x+(width-iw)/2;iy=y+(height-ih)/2
    pdf.saveState();clip=pdf.beginPath();clip.rect(ix,iy,iw,ih);pdf.clipPath(clip,stroke=0,fill=0)
    pdf.drawImage(str(HERE/shot['file']),ix-crop['x']*scale,
                  iy-(shot['height']-crop['y']-crop['h'])*scale,
                  width=shot['width']*scale,height=shot['height']*scale,mask='auto')
    pdf.restoreState()
    markers=[]
    for target in shot['targets']:
        if spec.get('keep') and target['n'] not in spec['keep']:continue
        visible_left=max(target['x'],crop['x']);visible_right=min(target['x']+target['w'],crop['x']+crop['w'])
        visible_top=max(target['y'],crop['y']);visible_bottom=min(target['y']+target['h'],crop['y']+crop['h'])
        if visible_right<=visible_left or visible_bottom<=visible_top:raise RuntimeError('Invisible callout: '+spec['id'])
        rx=ix+(visible_left-crop['x'])*scale;ry=iy+(crop['y']+crop['h']-visible_bottom)*scale
        rw=(visible_right-visible_left)*scale;rh=(visible_bottom-visible_top)*scale
        pdf.setStrokeColor(ORANGE);pdf.setLineWidth(1.05);pdf.roundRect(rx-1,ry-1,rw+2,rh+2,2,fill=0,stroke=1)
        endx=rx+2;endy=ry+rh-min(rh/2,14)
        bx=max(x+12,rx-17);by=min(y+height-12,endy+20)
        number=target['n']+spec.get('offset',0)
        arrow(bx+5,by-6,endx,endy)
        pdf.setFillColor(ORANGE);pdf.circle(bx,by,9,fill=1,stroke=0)
        pdf.setFont('Bold',9);pdf.setFillColor(WHITE);pdf.drawCentredString(bx,by-3,str(number))
        markers.append({'number':number,'label':target['label']})
    LAYOUT.append({'page':pdf.getPageNumber(),'screenshot':spec['id'],'css_to_pdf_scale':round(scale,3),'markers':markers})


def result_strip(result,next_step):
    pdf.setFillColor(PALE);pdf.roundRect(28,57,W-56,65,5,fill=1,stroke=0)
    label('YOU SHOULD SEE',42,107,FOREST)
    a=para(result,42,99,458,10.2)
    label('NEXT',527,107,FOREST)
    b=para(next_step,527,99,W-570,10.2)
    if max(a,b)>43:raise RuntimeError('Result strip overflow')


def screen_page(i,p):
    header(i,p)
    figures=p['figures']
    if len(figures)==1:image_frame(figures[0],28,145,540,294,p.get('mode','detail'))
    else:
        image_frame(figures[0],28,298,540,141,p.get('mode','detail'))
        image_frame(figures[1],28,145,540,141,p.get('mode','detail'))
    label('SCREEN DETAIL / NUMBERED CONTROLS',28,132,size=7.3)
    top=438
    for number,(title,text) in enumerate(p['steps'],1):
        pdf.setFillColor(ORANGE);pdf.circle(593,top-7,8,fill=1,stroke=0)
        pdf.setFillColor(WHITE);pdf.setFont('Bold',8);pdf.drawCentredString(593,top-9.7,str(number))
        a=para(title,608,top+1,W-636,10.7,bold=True)
        b=para(text,608,top-a-4,W-636,10.1,MUTED)
        top-=a+b+17
    if top<135:raise RuntimeError('Callout text overflow: '+p['key'])
    result_strip(p['result'],p['next_step'])


def cover(i):
    pdf.setFillColor(INK);pdf.rect(0,0,W,H,fill=1,stroke=0)
    brand(35,H-49,WHITE);label('A GUIDE TO THE ACTUAL LOCAL APP',35,H-86,colors.HexColor('#D4E1CE'))
    para('Your first experiment.\nEvery decision explained.',35,H-108,470,31,WHITE,bold=True,leading=37)
    para('A visual, click-by-click user guide with authentic screenshots, numbered arrows and worked examples.',37,H-201,435,12,colors.HexColor('#D4E1CE'))
    pdf.setFillColor(PALE);pdf.roundRect(35,112,445,159,8,fill=1,stroke=0)
    label('WHAT YOU WILL BE ABLE TO DO',53,248,FOREST)
    para('Choose a packaging condition. Enter test records. Understand a pause. Investigate a failure. Review fresh evidence. Approve limited continuation. Inspect what happened.',53,232,402,13,INK,leading=19)
    para('All screenshots show fictional demonstration data. No physical leak prediction, plant control or manufacturing result is claimed.',53,148,400,9.5,MUTED)
    image_frame('02-introduction',510,109,298,377,'context')
    label('31 OCTOBER 2026',37,75,colors.HexColor('#D4E1CE'))
    pdf.setFillColor(WHITE);pdf.setFont('Body',10);pdf.drawString(37,53,'Start with the map on page 2. Follow the orange numbers beside each screen.')
    pdf.drawRightString(W-34,28,f'01 / {len(PAGES):02d}')


def contents(i):
    p={'section':'READ THIS FIRST','title':'Find your route through the guide',
       'subtitle':'Use the clickable entries below or the PDF bookmarks. This is a reference you can follow beside the website.'}
    header(i,p)
    routes=[('purpose','Understand the product','Purpose, login, starting points and navigation.'),
            ('paused','Enter the evidence','New caps, a fresh set, readings, time and an independent result.'),
            ('problem','Investigate a failed result','Describe the observation, propose an explanation, review and apply a change.'),
            ('fresh-set','Verify and continue','Fresh tests, pause resolution, bounded permission and saved sample units.'),
            ('history','Inspect your work','Timeline, earlier knowledge, record details and export.'),
            ('custom','Explore alternatives','Custom inputs, already-covered caps and unreliable measurement references.'),
            ('advanced','Try advanced checks','Late discoveries, affected samples and declared software-case evaluation.'),
            ('saved','Reopen and troubleshoot','Saved sessions, mobile navigation and a compact reference.'),]
    for n,(key,title,text) in enumerate(routes):
        col=n//4;row=n%4;x=28+col*398;y=430-row*73
        pdf.setFillColor(WHITE);pdf.setStrokeColor(LINE);pdf.roundRect(x,y-50,382,63,4,fill=1,stroke=1)
        para(title,x+13,y+1,300,12,bold=True);para(text,x+13,y-20,302,9.7,MUTED)
        pdf.setFillColor(FOREST);pdf.setFont('Bold',16);pdf.drawRightString(x+368,y-5,str(PAGE_NO[key]).zfill(2))
        pdf.linkRect('',key,(x,y-50,x+382,y+13),relative=0,thickness=0)
    pdf.setFillColor(PALE);pdf.roundRect(28,59,W-56,66,5,fill=1,stroke=0)
    para('Want a shorter first success?',42,110,330,12,bold=True)
    para(f'Use the approved example, grant permission on page {PAGE_NO["permission"]}, then record five units on page {PAGE_NO["produce"]}. Its tests are preloaded.',42,91,355,10.1)
    para('Following a direct PASS route?',435,110,350,12,bold=True)
    para(f'At the independent result, choose PASS. Once checks are met, skip investigation and go to pause resolution on page {PAGE_NO["resolve"]}.',435,91,350,10.1)


def reference(i):
    p={'section':'KEEP THIS PAGE HANDY','title':'Three stages that must not be confused',
       'subtitle':'A passing test, a reviewer approval and a recorded unit are different records with different purposes.'}
    header(i,p)
    cards=[('01','TESTS READY','The current condition has sufficient eligible evidence.','This is not permission to produce.'),
           ('02','APPROVED WITHIN LIMIT','QA has resolved active pauses and granted a scoped unit/time budget.','This does not automatically create units.'),
           ('03','SAMPLE UNITS RECORDED','You explicitly submitted a count within the current permission.','The server checked conditions again at use.')]
    for j,(n,title,body,boundary) in enumerate(cards):
        x=28+j*266;pdf.setFillColor(WHITE);pdf.setStrokeColor(LINE);pdf.roundRect(x,269,251,169,6,fill=1,stroke=1)
        label(n,x+15,414,ORANGE,11);para(title,x+15,395,220,11.4,bold=True)
        para(body,x+15,365,220,11);para(boundary,x+15,309,220,10.1,MUTED)
    terms=[('Batch / lot','An identified group of bottles or caps.'),('Scope','The exact condition a test or permission covers.'),
           ('Specimen','One fictional package represented by a reading.'),('Reference','A record of when a measuring tool can be relied on.'),
           ('Hold / pause','A restriction on continuing, not proof of a defect.'),('Demonstration time','A fictional clock, separate from your real wall-clock time.')]
    for j,(term,definition) in enumerate(terms):
        x=28+(j%2)*398;top=241-(j//2)*53
        para(term,x,top,370,11,bold=True);para(definition,x,top-17,370,10.3,MUTED)
    para('Example policy only: at least three eligible specimens; torque intervals inside 0.90-1.10 N·m; an independent leak result after 24 demonstration hours. These are not verified L’Oréal plant limits.',28,69,W-56,9.8,MUTED)


def troubleshooting(i):
    p={'section':'WHEN YOU GET STUCK','title':'Use the visible reason to choose the next step',
       'subtitle':'Do not repeatedly submit the same action or invent a positive outcome to make a warning disappear.'}
    header(i,p)
    rows=[('Old UI or developer sessions','Stop the old server with Ctrl+C, run npm start, then reload /start. A page refresh does not update Python.'),
          ('Tabs empty or actions disabled','Select/create an experiment. Use qa, the current view and the intended main run. Check the backend connection.'),
          ('No fresh test set / leak result blocked','Start a set first. The full wait must follow the latest specimen reading, not merely the set creation time.'),
          ('Numbers look good but remain unusable','Check the reference at measurement time, the assumed error interval, specimen count and exact condition.'),
          ('Time advance causes a new warning','Confirm current records. The advance aged the feed and may also expire existing permission.'),
          ('Tests ready but no production','Resolve any active pause, then separately obtain bounded QA permission for this condition.'),
          ('New PASS did not clear an old FAIL','Conflicting/adverse records are retained. Use a justified changed condition and fresh verification where appropriate.'),
          ('Stale context / connection lost','Review the refreshed state and reopen the form. Keep the server terminal running; do not assume a lost response means no commit.')]
    y=442
    for j,(symptom,answer) in enumerate(rows):
        pdf.setFillColor(WHITE if j%2==0 else PALE);pdf.roundRect(28,y-40,W-56,42,3,fill=1,stroke=0)
        para(symptom,40,y-3,221,10.1,bold=True);height=para(answer,276,y-3,W-319,10.1,MUTED)
        if height>31:raise RuntimeError('Troubleshooting row overflow')
        y-=46
    para('Guide scope: real screenshots and persisted software behavior using isolated fictional data. No factory data, physical pilot, measured waste reduction or independent novice usability study is claimed. The existing Markdown manual is unchanged.',28,68,W-56,9.3,MUTED)


for i,p in enumerate(PAGES,1):
    pdf.bookmarkPage(p['key']);pdf.addOutlineEntry(p.get('title',{'cover':'Cover','contents':'Contents','reference':'Quick reference','troubleshooting':'Troubleshooting'}.get(p['key'],p['key'])),p['key'],level=0,closed=False)
    if p.get('special')=='cover':cover(i)
    elif p.get('special')=='contents':contents(i)
    elif p.get('special')=='reference':reference(i)
    elif p.get('special')=='troubleshooting':troubleshooting(i)
    else:screen_page(i,p)
    pdf.showPage()
pdf.save()

reader=PdfReader(str(OUTPUT))
if len(reader.pages)!=len(PAGES):raise RuntimeError('Unexpected PDF page count')
if any(not page.extract_text().strip() for page in reader.pages):raise RuntimeError('Empty PDF page')
if hashlib.sha256(MANUAL.read_bytes()).hexdigest()!=CAPTURE['markdown_manual_sha256']:raise RuntimeError('Existing Markdown was modified')
report={'pdf':OUTPUT.name,'pages':len(reader.pages),'authentic_captures':len(CAPTURE['shots']),
        'annotated_figures':len(LAYOUT),'screenshot_basis':CAPTURE['database_basis'],
        'provenance':'SYNTHETIC','markdown_unchanged':True,'markdown_sha256':CAPTURE['markdown_manual_sha256'],
        'pdf_bytes':OUTPUT.stat().st_size,'pdf_sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        'selectable_text':True,'bookmarks':len(reader.outline),'layout':LAYOUT}
(HERE/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(f'Built {OUTPUT.name}: {len(reader.pages)} pages, {len(LAYOUT)} annotated screenshot figures, {OUTPUT.stat().st_size/1024/1024:.1f} MiB. Markdown unchanged.')
