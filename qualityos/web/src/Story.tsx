import type {Actor, Journey, Snapshot, Workspace} from './api';
import {qaRequired} from './api';

const pageDescriptions: Record<string, {question: string; explanation: string}> = {
  line: {question: 'Can this run continue?', explanation: 'See which bottle, cap and machine setup are in use, what is blocking them, and whether QA has given permission.'},
  evidence: {question: 'What supports this decision?', explanation: 'Follow the saved records behind the decision. Use an earlier snapshot to see what was known before a later discovery.'},
  qualification: {question: 'Do these tests cover this combination?', explanation: 'Check the exact materials, trustworthy measurements and independent leak result. Passing these checks makes the evidence ready for QA review.'},
  investigation: {question: 'What might explain the failure, and what should we test?', explanation: 'Keep competing explanations, review a proposed change and assess fresh verification. An explanation remains a hypothesis until its evidence supports it.'},
};

function Arrow() {
  return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>;
}

function PackagingScene() {
  return <div className="story-scene" role="img" aria-label="Earlier evidence covers bottle B01 with cap C01. A new C02 cap delivery changes the combination.">
    <div className="scene-topline"><span className="scene-live-dot"/> AURELIA · FICTIONAL LOTION LINE</div>
    <svg viewBox="0 0 440 270" aria-hidden="true">
      <path d="M30 225h380M30 237h380" stroke="#9cab94" strokeWidth="1.4"/>
      {[49,99,149,199,249,299,349,399].map(x=><circle key={x} cx={x} cy="232" r="4" fill="#d2dcc8"/>)}
      {[90,179].map(x=><g key={x}><path d={`M${x} 100h34v19c0 10 13 13 13 27v76H${x-13}v-76c0-14 13-17 13-27Z`} fill="#f8faf4" stroke="#6e886d" strokeWidth="1.5"/><path d={`M${x-2} 84h38v16h-38Z`} fill="#c2d5ad" stroke="#6e886d" strokeWidth="1.5"/><rect x={x-6} y="157" width="46" height="37" rx="2" fill="#e7eddf"/><path d={`M${x+4} 169h26m-22 9h18`} stroke="#84977a"/></g>)}
      <path d="M302 100h34v19c0 10 13 13 13 27v76h-60v-76c0-14 13-17 13-27Z" fill="#f8faf4" stroke="#6e886d" strokeWidth="1.5"/>
      <path d="M300 60h38v19h-38Z" fill="#e9c98a" stroke="#966a29" strokeWidth="1.5"/>
      <path d="M319 85v10m-4-5 4 5 4-5" stroke="#966a29" fill="none"/>
      <path d="M234 94h46" stroke="#a78b59" strokeDasharray="4 4"/>
      <text x="107" y="63" textAnchor="middle">C01</text><text x="319" y="41" textAnchor="middle" className="new-cap-label">C02 · NEW DELIVERY</text>
      <text x="209" y="260" textAnchor="middle">SAME BOTTLE. DIFFERENT CAP LOT. SAME PROOF?</text>
    </svg>
    <div className="scene-proof"><span>EARLIER TESTS</span><strong>Bottle B01 + cap C01</strong><span className="scene-proof-status">Covered</span></div>
    <div className="scene-proof scene-question"><span>TODAY'S COMBINATION</span><strong>Bottle B01 + cap C02</strong><span className="scene-proof-status">Needs a decision</span></div>
  </div>;
}

export function Glossary() {
  const words = [
    ['Lot', 'An identified batch or delivery of a component. C01 and C02 are different cap lots.'],
    ['Closure', 'The cap or other component that closes a package. This story uses screw caps.'],
    ['Scope', 'The exact materials, machine setup and policy that a test or decision covers.'],
    ['Qualification', 'Test evidence that covers a stated combination of materials and process conditions.'],
    ['Hold', 'A recorded pause on affected work. It does not mean every held item is defective.'],
    ['Instrument reference', 'A calibration record of a check against a known standard, used here to judge whether a measuring tool’s readings are eligible.'],
    ['Torque', 'The twisting effort used to apply a cap. A torque reading alone does not establish leak integrity.'],
    ['QA', 'Quality assurance: the quality reviewer who can resolve a hold and grant a limited permission.'],
    ['Replay clock', 'Fictional demonstration time. Advancing it by a day does not physically perform a day-long test.'],
  ];
  return <details className="story-glossary"><summary>New to manufacturing? A few useful words <span aria-hidden="true">+</span></summary><dl>{words.map(([word,meaning])=><div key={word}><dt>{word}</dt><dd>{meaning}</dd></div>)}</dl></details>;
}

export function StartHere({actor,snapshot,workspaces,onStart,onResume,onSandbox}: {
  actor:Actor; snapshot:Snapshot|null; workspaces:Workspace[];
  onStart:()=>void; onResume:(wid:string)=>void; onSandbox:()=>void;
}) {
  const saved=workspaces.filter(w=>w.scenario_version.includes('/guided-story-v1'));
  const current=snapshot?.journey&&!snapshot.historical?snapshot:null;
  const mayCreate=['QUALITY_ENGINEER','OPERATOR','ADMIN'].includes(actor.role);
  return <div className="start-here">
    <section className="story-welcome">
      <div className="story-welcome-copy"><span className="eyebrow">A STORY ABOUT GETTING QUALITY RIGHT</span>
        <h1>The cap changed.<br/>Should the line<br/>{' '}<span>keep running?</span></h1>
        <p className="welcome-lead">Yesterday's tests passed. Today's delivery is different. QualityOS helps a team decide whether its evidence still justifies continuing.</p>
        <p>The aim is to catch an unsupported quality decision before more product is made. Follow a fictional lotion line, introduce a new cap delivery, and build the evidence needed to continue.</p>
        <div className="welcome-actions"><button className="button primary story-start" disabled={!mayCreate} onClick={current?()=>onResume(current.workspace.id):onStart}>{current?'Resume your story':'Start the guided story'}<Arrow/></button>{current&&<button className="text-button" disabled={!mayCreate} onClick={onStart}>Start a separate story</button>}</div>
        <small className="story-provenance">Interactive demonstration with fictional test data · Your work is saved</small>
        {!mayCreate&&<p className="story-access-note">Your visitor account can read saved stories below. An operator or quality engineer creates a new one.</p>}
        {actor.role!=='QUALITY_ENGINEER'&&<p className="story-access-note">You are signed in as {actor.role==='OPERATOR'?'an operator':actor.role==='ADMIN'?'an administrator':'a visitor'}. QA review steps require the local <code>qa</code> account; your current role cannot sign them.</p>}
      </div>
      <PackagingScene/>
    </section>
    <section className="story-promise" aria-label="What this product helps you do">
      <div><span>01 / NOTICE THE CHANGE</span><h2>The same-looking cap can be a different condition.</h2><p>Identify exactly what changed before reusing an earlier passing status.</p></div>
      <div><span>02 / CHECK THE PROOF</span><h2>A good number can still be weak evidence.</h2><p>Check the measurement's reference and the independent functional test.</p></div>
      <div><span>03 / JUSTIFY THE NEXT MOVE</span><h2>Continue when the evidence and permission agree.</h2><p>Keep the failure visible, verify a new condition, then ask QA to authorize it.</p></div>
    </section>
    {saved.length>0&&<section className="story-saved"><div><span className="eyebrow">PICK UP WHERE THE RECORDS LEFT OFF</span><h2>Continue a saved story.</h2><p>Progress comes from saved work, so a reload does not reset the experiment.</p></div><div className="saved-story-list">{saved.slice(0,3).map(w=><button key={w.id} onClick={()=>onResume(w.id)}><span><strong>{w.name}</strong><small>{current?.workspace.id===w.id?current.journey!.title:'Open the current saved step'}</small></span><Arrow/></button>)}</div></section>}
    <Glossary/>
    <div className="story-expert"><div><strong>Already familiar with the workflow?</strong><p>The four workspaces remain available for independent exploration.</p></div><button className="button" disabled={!mayCreate} onClick={onSandbox}>Open an unguided workspace<Arrow/></button></div>
  </div>;
}

export function PagePurpose({page}:{page:string}) {
  const description=pageDescriptions[page];
  if(!description)return null;
  return <details className="page-purpose"><summary>{description.question}<span>What this screen is for</span></summary><p>{description.explanation}</p></details>;
}

export function StoryGuide({journey,actor,offline,busy,collapsed,onToggle,onAction,onStart,onControl}: {
  journey:Journey;actor:Actor;offline:boolean;busy:boolean;collapsed:boolean;
  onToggle:()=>void;onAction:()=>void;onStart:()=>void;onControl:()=>void;
}) {
  const complete=journey.status==='COMPLETE';
  const roleBlocked=!!journey.operation&&(actor.role==='VIEWER'||actor.role==='ADMIN'||(qaRequired(journey.operation)&&actor.role!=='QUALITY_ENGINEER'));
  if(collapsed)return <div className="guide-compact"><span>YOUR STORY</span><strong>{journey.title}</strong><button className="text-button" onClick={onToggle}>Show guide<Arrow/></button></div>;
  return <section className={'story-guide '+(complete?'story-guide-complete':'')} aria-labelledby="story-step-title" data-story-step={journey.id}>
    <div className="guide-header"><span className="eyebrow">{complete?'STORY COMPLETE · EVIDENCE KEPT':'YOUR GUIDED STORY'}</span><button className="text-button" onClick={onToggle}>Explore without the guide</button></div>
    {['ACTIVE','COMPLETE'].includes(journey.status)&&<ol className="story-chapters" aria-label="Story chapters">{journey.chapters.map((chapter,i)=><li key={chapter} className={i===journey.chapter?'current':i<journey.chapter||complete?'past':''} aria-current={i===journey.chapter?'step':undefined}><span>{i<journey.chapter||complete?'✓':String(i+1).padStart(2,'0')}</span>{chapter}</li>)}</ol>}
    <div className="guide-content"><div className="guide-narrative"><span className="guide-chapter">{['HISTORICAL','CONTROL'].includes(journey.status)?'A DIFFERENT VIEW':`CHAPTER ${journey.chapter+1} / ${journey.chapters.length}`}</span><h2 id="story-step-title">{journey.title}</h2><p>{journey.story}</p></div>
      <div className="guide-move"><span className="eyebrow">{complete?'WHAT YOU HAVE DEMONSTRATED':'WHY THIS NEXT MOVE MATTERS'}</span><p>{journey.why}</p>
        <button className="button primary guide-action" disabled={busy||!!journey.operation&&(offline||roleBlocked)} onClick={onAction}>{journey.action_label}<Arrow/></button>
        {journey.id==='open_first'&&journey.control_run_id&&<button className="text-button" onClick={onControl}>Check the independent line<Arrow/></button>}
        {roleBlocked&&<small className="guide-role-note">{qaRequired(journey.operation||'')?'A quality engineer must review this action. Sign in as the local qa account to complete it.':'Your current role can inspect this step but cannot record it.'}</small>}
        {offline&&journey.operation&&<small className="guide-role-note">Reconnect before recording the next action. Your saved progress remains intact.</small>}
        {journey.status==='NEEDS_REVIEW'&&<button className="text-button" onClick={onStart}>Start a separate guided story</button>}
        {complete&&<p className="guide-completion-note">This shows a software decision workflow. It does not establish physical defect reduction, seal safety or factory savings.</p>}
      </div></div>
    {!complete&&journey.expected&&<div className="guide-expectation"><span>WHAT TO LOOK FOR</span><p>{journey.expected}</p></div>}
    {complete&&journey.preview.length>0&&<div className="guide-recap">{journey.preview.map(p=><div key={p.label}><span>{p.label}</span><strong>{p.value}</strong></div>)}</div>}
  </section>;
}

export function StoryReview({journey}:{journey:Journey}) {
  return <div className="story-review"><p>{journey.story}</p><div className="story-review-why"><span>WHY YOU ARE DOING THIS</span><p>{journey.why}</p></div>{journey.preview.length>0&&<dl>{journey.preview.map(x=><div key={x.label}><dt>{x.label}</dt><dd>{x.value}</dd></div>)}</dl>}<small>These are supplied fictional inputs. Review them before recording. You can adjust them below; the same evidence and permission checks apply either way.</small></div>;
}
