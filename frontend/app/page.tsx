"use client";

import { useRef, useState } from "react";

type ScenarioId = "job" | "phd" | "school";
type DemoStatus = "idle" | "running" | "ready" | "approved" | "rejected";

type Scenario = {
  id: ScenarioId;
  label: string;
  eyebrow: string;
  goal: string;
  materials: string[];
  intent: string;
  task: string;
  complexity: string;
  agents: string[];
  steps: { title: string; detail: string }[];
  evidence: { title: string; source: string; content: string; simulated?: boolean }[];
  email: { to: string; subject: string; body: string; attachments: string[] };
};

const scenarios: Record<ScenarioId, Scenario> = {
  job: {
    id: "job",
    label: "Job Application",
    eyebrow: "Career outreach",
    goal: "Use my CV and this AI Product Manager job description to draft a personalized outreach email.",
    materials: ["Resume.pdf", "AI_Product_Manager_JD.pdf"],
    intent: "Job Application",
    task: "Recruiter Outreach",
    complexity: "Medium",
    agents: ["Planner", "Context", "Writer", "Reviewer"],
    steps: [
      { title: "Intent identified", detail: "Job application" },
      { title: "Task planned", detail: "Recruiter outreach" },
      { title: "Materials understood", detail: "Resume + job description" },
      { title: "Relevant experience matched", detail: "Product strategy · AI workflows" },
      { title: "Draft generated", detail: "Personalized to the role" },
      { title: "Claims reviewed", detail: "Evidence-linked and complete" },
    ],
    evidence: [
      { title: "Candidate background", source: "Resume.pdf", content: "Product discovery, AI prototyping and cross-functional delivery experience." },
      { title: "Role priority", source: "AI_Product_Manager_JD.pdf", content: "The role emphasizes agent workflows, user research and measurable product outcomes." },
    ],
    email: {
      to: "jordan.lee@example-company.com",
      subject: "AI Product Manager — product thinking meets agent delivery",
      body: "Hi Jordan,\n\nI’m reaching out about the AI Product Manager role. My background combines product discovery, hands-on AI prototyping and cross-functional delivery — closely matching the role’s focus on turning agent capabilities into measurable user outcomes.\n\nI’d value the chance to share how I approach ambiguous AI problems, from defining the user need through to evaluation and iteration. I’ve attached my resume for context.\n\nWould you be open to a short conversation next week?\n\nBest,\nAlex",
      attachments: ["Resume.pdf"],
    },
  },
  phd: {
    id: "phd",
    label: "PhD Outreach",
    eyebrow: "Research enquiry",
    goal: "Use my CV and research proposal to draft a personalized PhD enquiry to Professor Alex Smith.",
    materials: ["CV.pdf", "Research_Proposal.pdf"],
    intent: "PhD Outreach",
    task: "Supervisor Enquiry",
    complexity: "High",
    agents: ["Planner", "Context", "Research", "Writer", "Reviewer"],
    steps: [
      { title: "Intent identified", detail: "PhD outreach" },
      { title: "Task planned", detail: "Supervisor enquiry" },
      { title: "Materials understood", detail: "CV + research proposal" },
      { title: "Research context prepared", detail: "Simulated professor profile" },
      { title: "Research overlap mapped", detail: "3D vision · multimodal reasoning" },
      { title: "Draft generated", detail: "Research-specific enquiry" },
      { title: "Claims reviewed", detail: "Sources checked" },
    ],
    evidence: [
      { title: "Candidate background", source: "CV.pdf", content: "Computer vision and applied AI project experience, including 3D scene understanding." },
      { title: "Research interest", source: "Research_Proposal.pdf", content: "3D Question Answering with grounded multimodal representations." },
      { title: "Professor information", source: "Demo research source", content: "Professor Alex Smith studies multimodal reasoning and 3D vision at Example University.", simulated: true },
    ],
    email: {
      to: "alex.smith@example-university.edu",
      subject: "Prospective PhD enquiry — 3D vision and multimodal reasoning",
      body: "Dear Professor Smith,\n\nI’m writing to ask whether you may be accepting PhD students for the next intake. My current research interest is 3D Question Answering, particularly how grounded multimodal representations can support reasoning about complex scenes.\n\nYour simulated demo profile’s focus on multimodal reasoning and 3D vision closely aligns with the direction of my proposal. My background includes computer vision and applied AI projects, and I would be excited to explore how this experience could contribute to your group.\n\nI’ve attached my CV and research proposal for context. If the topic is relevant to your current supervision plans, I would be grateful for the opportunity to discuss it.\n\nKind regards,\nAlex",
      attachments: ["CV.pdf", "Research_Proposal.pdf"],
    },
  },
  school: {
    id: "school",
    label: "School Affairs",
    eyebrow: "Course communication",
    goal: "Help me email my course coordinator about an assessment submission issue.",
    materials: ["Assessment_Screenshot.png"],
    intent: "School Affairs",
    task: "Assessment Support",
    complexity: "Low",
    agents: ["Planner", "Writer", "Reviewer"],
    steps: [
      { title: "Intent identified", detail: "School affairs" },
      { title: "Task planned", detail: "Assessment support" },
      { title: "Key facts prepared", detail: "Submission issue + timestamp" },
      { title: "Draft generated", detail: "Clear and respectful" },
      { title: "Claims reviewed", detail: "No unsupported assumptions" },
    ],
    evidence: [
      { title: "Submission issue", source: "User-provided details", content: "The student attempted to submit before the deadline but received an upload error." },
      { title: "Supporting material", source: "Assessment_Screenshot.png", content: "Screenshot showing the submission error and timestamp." },
    ],
    email: {
      to: "course.coordinator@example-university.edu",
      subject: "Assessment submission issue — request for guidance",
      body: "Dear Course Coordinator,\n\nI’m writing about an issue I encountered while submitting the assessment. I attempted to upload the file before the deadline, but the system returned an error. I’ve attached a screenshot showing the error and timestamp.\n\nCould you please advise on the appropriate next step? I can provide the completed assessment file and any additional details you need.\n\nThank you for your help.\n\nKind regards,\nAlex",
      attachments: ["Assessment_Screenshot.png"],
    },
  },
};

const problems = [
  ["Context is fragmented", "CVs, job descriptions, proposals and course details live in different places."],
  ["Research takes time", "Important messages often require recipient or organization context before writing starts."],
  ["Generic AI lacks context", "One prompt tends to produce generic language rather than a goal-specific strategy."],
  ["AI can hallucinate", "Confident prose can include claims that were never supported by the source material."],
  ["Users need control", "Important external communication should never leave without deliberate approval."],
];

const howItWorks = [
  ["01", "Understand", "Identify the user’s goal, recipient and communication scenario."],
  ["02", "Plan", "Decide what context, tools and specialist agents the task actually needs."],
  ["03", "Prepare Context", "Turn materials and relevant information into traceable evidence."],
  ["04", "Generate & Review", "Draft the message, then independently check quality and claims."],
  ["05", "Approve", "Show the complete action preview and wait for the user’s decision."],
];

const evaluation = [
  ["Intent Accuracy", "100%", "V2 regression result across the 80-case deterministic safety suite."],
  ["Task Completion", "100%", "Contract completion, including correct ASK_USER behavior."],
  ["Hard-case Completion", "100%", "Up from 41.0% before evaluation-led routing changes."],
  ["LIVE Qwen3 Completion", "58.3%", "12-case ContextMail run vs 75.0% for the single-LLM baseline."],
];

function Arrow() {
  return <span className="flow-arrow" aria-hidden="true">→</span>;
}

export default function Home() {
  const [scenarioId, setScenarioId] = useState<ScenarioId>("phd");
  const [goal, setGoal] = useState(scenarios.phd.goal);
  const [status, setStatus] = useState<DemoStatus>("idle");
  const [completedSteps, setCompletedSteps] = useState(0);
  const [plannerOpen, setPlannerOpen] = useState(true);
  const [editing, setEditing] = useState(false);
  const [subject, setSubject] = useState(scenarios.phd.email.subject);
  const [body, setBody] = useState(scenarios.phd.email.body);
  const runToken = useRef(0);
  const scenario = scenarios[scenarioId];

  function resetForScenario(id: ScenarioId) {
    const nextScenario = scenarios[id];
    runToken.current += 1;
    setScenarioId(id);
    setGoal(nextScenario.goal);
    setStatus("idle");
    setCompletedSteps(0);
    setEditing(false);
    setSubject(nextScenario.email.subject);
    setBody(nextScenario.email.body);
  }

  function inferScenario(input: string): ScenarioId {
    const text = input.toLowerCase();
    if (/phd|professor|supervisor|research proposal|doctoral|博士|导师|套磁/.test(text)) return "phd";
    if (/job|recruiter|resume|cv|application|position|求职|招聘|职位/.test(text)) return "job";
    return "school";
  }

  async function runDemo() {
    const detectedId = inferScenario(goal);
    const detectedScenario = scenarios[detectedId];
    const token = ++runToken.current;
    setScenarioId(detectedId);
    setStatus("running");
    setCompletedSteps(0);
    setEditing(false);
    setSubject(detectedScenario.email.subject);
    setBody(detectedScenario.email.body);
    for (let index = 1; index <= detectedScenario.steps.length; index += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 420));
      if (runToken.current !== token) return;
      setCompletedSteps(index);
    }
    await new Promise((resolve) => window.setTimeout(resolve, 280));
    if (runToken.current === token) setStatus("ready");
  }

  function selectScenario(id: ScenarioId) {
    resetForScenario(id);
    document.getElementById("demo")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function approve() {
    setEditing(false);
    setStatus("approved");
  }

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="ContextMail home">Context<span>Mail</span></a>
        <nav aria-label="Primary navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#architecture">Architecture</a>
          <a href="#evaluation">Evaluation</a>
        </nav>
        <a className="nav-cta" href="#demo">Try demo</a>
      </header>

      <section className="hero section-shell" id="top">
        <div className="hero-copy">
          <p className="eyebrow"><span /> AI Communication Agent</p>
          <h1>Your AI agent for <em>important emails.</em></h1>
          <p className="hero-lead">Give ContextMail your goal and materials. It understands the task, plans the workflow, drafts the email and verifies it before you send.</p>
          <div className="hero-actions">
            <a className="button button-primary" href="#demo">Try Interactive Demo <span>→</span></a>
            <a className="button button-quiet" href="#how-it-works">View How It Works</a>
          </div>
          <p className="hero-note">Built for high-context communication: job applications, research outreach and school affairs.</p>
        </div>
        <div className="hero-visual" aria-label="ContextMail workflow summary">
          <div className="visual-topline"><span>Goal received</span><b>Planning</b></div>
          <div className="goal-card"><small>User goal</small><p>“Use my materials to write a personalized PhD enquiry.”</p><div><span>CV.pdf</span><span>Proposal.pdf</span></div></div>
          <div className="mini-flow">
            {["Goal", "Plan", "Research", "Write", "Review", "Approve"].map((item, index) => <div key={item}><i>{String(index + 1).padStart(2, "0")}</i><span>{item}</span>{index < 5 && <Arrow />}</div>)}
          </div>
          <div className="visual-result"><i>✓</i><div><strong>Ready for approval</strong><span>Claims reviewed · 2 sources attached</span></div></div>
        </div>
      </section>

      <section className="trust-strip" aria-label="Product principles">
        <span>Understands intent</span><span>Routes dynamically</span><span>Uses evidence</span><span>Waits for approval</span>
      </section>

      <section className="section-shell problem-section">
        <div className="section-intro"><p className="section-kicker">The problem</p><h2>Important emails require more than writing.</h2><p>The hardest part is rarely the sentence. It is understanding the goal, assembling the right context and deciding what can safely be said.</p></div>
        <div className="problem-grid">{problems.map(([title, description], index) => <article key={title}><span>{String(index + 1).padStart(2, "0")}</span><h3>{title}</h3><p>{description}</p></article>)}</div>
      </section>

      <section className="demo-section" id="demo">
        <div className="section-shell">
          <div className="demo-heading"><div><p className="section-kicker light">Interactive Product Demo</p><h2>Describe the goal. Let the agent decide.</h2><p>Start with an example or edit the request. The Planner identifies the intent and selects the workflow after you run it.</p></div><span className="demo-badge">Simulated agent execution</span></div>

          <div className="example-label"><span>Try an example</span><small>Examples fill the input — they do not manually set the final intent.</small></div>
          <div className="scenario-tabs" aria-label="Example prompts">
            {(Object.values(scenarios) as Scenario[]).map((item) => <button key={item.id} aria-pressed={goal === item.goal} onClick={() => selectScenario(item.id)}><small>{item.eyebrow}</small><strong>{item.label}</strong></button>)}
          </div>

          <div className="demo-workspace">
            <section className="demo-input" aria-label="Demo input">
              <div className="workspace-label"><span>01</span><div><strong>Your request</strong><small>Pre-filled scenario</small></div></div>
              <label htmlFor="demo-goal">Communication goal</label>
              <textarea id="demo-goal" value={goal} onChange={(event) => { setGoal(event.target.value); setStatus("idle"); setCompletedSteps(0); }} />
              <label>Materials</label>
              <div className="material-list">{scenario.materials.map((material) => <div key={material}><span className="file-mark">DOC</span><div><strong>{material}</strong><small>Demo material · ready</small></div><i>✓</i></div>)}</div>
              <button className="run-button" onClick={runDemo} disabled={status === "running" || !goal.trim()}>{status === "running" ? "Planner is identifying intent…" : status === "idle" ? "Run Agent" : "Run Again"}<span>→</span></button>
              <p className="simulation-note">This static demo uses pre-authored mock data. No backend, external search or email provider is called.</p>
            </section>

            <section className="activity-panel" aria-live="polite">
              <div className="workspace-label"><span>02</span><div><strong>Agent activity</strong><small>{status === "idle" ? "Waiting to start" : status === "running" ? "Workflow in progress" : "Workflow complete"}</small></div></div>
              {status === "idle" ? <div className="activity-empty"><div className="pulse-core" /><h3>Ready to plan</h3><p>The planner will select only the agents this scenario needs.</p></div> : <div className="activity-list">
                {scenario.steps.map((step, index) => {
                  const complete = index < completedSteps;
                  const active = status === "running" && index === completedSteps;
                  return <div className={`activity-step ${complete ? "complete" : ""} ${active ? "active" : ""}`} key={step.title}><i>{complete ? "✓" : index + 1}</i><div><strong>{step.title}</strong><span>{step.detail}</span></div>{active && <b>Working</b>}</div>;
                })}
                <div className={`activity-step approval-step ${status === "ready" || status === "approved" || status === "rejected" ? "active" : ""}`}><i>○</i><div><strong>Waiting for your approval</strong><span>No external action has been taken</span></div></div>
              </div>}
            </section>
          </div>

          {status !== "idle" && <div className="result-grid">
            <div className="decision-card">
              <button className="card-toggle" onClick={() => setPlannerOpen(!plannerOpen)} aria-expanded={plannerOpen}><div><small>Planner output</small><strong>Planner Decision</strong></div><span>{plannerOpen ? "−" : "+"}</span></button>
              {plannerOpen && <div className="decision-content"><dl><div><dt>Intent</dt><dd>{scenario.intent}</dd></div><div><dt>Task</dt><dd>{scenario.task}</dd></div><div><dt>Complexity</dt><dd>{scenario.complexity}</dd></div><div><dt>Context used</dt><dd>{scenario.materials.join(" · ")}</dd></div></dl><p>Activated agents</p><div className="agent-route">{scenario.agents.map((agent, index) => <span key={agent}><b>{agent}</b>{index < scenario.agents.length - 1 && <Arrow />}</span>)}</div><small className="route-note">The planner selects a different workflow for each communication task.</small></div>}
            </div>

            <div className="evidence-card"><div className="card-heading"><div><small>Grounded context</small><h3>Evidence Used</h3></div><span>Demo Evidence</span></div><div className="evidence-list">{scenario.evidence.map((item) => <article key={item.title}><div><strong>{item.title}</strong>{item.simulated && <b>Simulated profile</b>}</div><small>Source · {item.source}</small><p>{item.content}</p></article>)}</div>{scenario.id === "phd" && <p className="evidence-disclaimer">Professor Alex Smith and Example University are fictional and used only for product demonstration.</p>}</div>
          </div>}

          {(status === "ready" || status === "approved" || status === "rejected") && <section className="email-preview">
            <div className="email-toolbar"><div><small>Action preview</small><h3>Email Preview</h3></div><span className={`status-pill ${status}`}>{status === "ready" ? "Ready for approval" : status === "approved" ? "Approved" : "Rejected"}</span></div>
            <div className="email-meta"><label><span>To</span><input value={scenario.email.to} readOnly /></label><label><span>Subject</span><input value={subject} onChange={(event) => setSubject(event.target.value)} readOnly={!editing} /></label></div>
            <label className="body-label"><span>Body</span><textarea value={body} onChange={(event) => setBody(event.target.value)} readOnly={!editing} /></label>
            <div className="attachment-row"><span>Attachments</span>{scenario.email.attachments.map((file) => <b key={file}>{file}</b>)}</div>
            {status === "ready" && <div className="email-actions"><button className="text-button" onClick={() => setEditing(!editing)}>{editing ? "Save changes" : "Edit draft"}</button><button className="reject-button" onClick={() => { setEditing(false); setStatus("rejected"); }}>Reject</button><button className="approve-button" onClick={approve}>Approve <span>→</span></button></div>}
            {status === "approved" && <div className="outcome approved-outcome"><strong>✓ Approved</strong><p>Demo only — in the production workflow, the approved email would be passed to the connected email provider for sending.</p></div>}
            {status === "rejected" && <div className="outcome rejected-outcome"><strong>Task cancelled</strong><p>The draft was rejected. No email was sent and no external action was taken.</p></div>}
          </section>}
        </div>
      </section>

      <section className="control-section section-shell">
        <div className="control-copy"><p className="section-kicker">Human in the loop</p><h2>AI works. You stay in control.</h2><p>ContextMail can understand, plan, research, draft and review. But important external actions remain a human decision.</p><strong>No important external action without user approval.</strong></div>
        <div className="control-flow"><div><small>AI work</small><strong>Plan · Prepare · Draft · Review</strong></div><Arrow /><div className="control-highlight"><small>Decision point</small><strong>Human Approval</strong></div><Arrow /><div><small>Connected system</small><strong>External Action</strong></div></div>
      </section>

      <section className="how-section" id="how-it-works"><div className="section-shell"><div className="section-intro"><p className="section-kicker">Product workflow</p><h2>How ContextMail works.</h2><p>One goal enters. A task-specific, evidence-aware workflow comes out.</p></div><div className="how-grid">{howItWorks.map(([number, title, description]) => <article key={number}><span>{number}</span><h3>{title}</h3><p>{description}</p></article>)}</div></div></section>

      <section className="architecture-section section-shell" id="architecture">
        <div className="section-intro"><p className="section-kicker">System design</p><h2>Planner-led, not pipeline-bound.</h2><p>The workflow adapts to the task, shares traceable state and loops back when review finds a problem.</p></div>
        <div className="architecture-diagram" role="img" aria-label="ContextMail architecture from user goal through planner, dynamic agents, shared state, review and human approval">
          <div className="arch-node input-node"><small>Input</small><strong>User Goal + Materials</strong></div><span className="arch-down">↓</span>
          <div className="arch-node primary-node"><small>Orchestrator</small><strong>Planner Agent</strong></div><span className="arch-down">↓</span>
          <p className="routing-label">Dynamic routing</p>
          <div className="arch-agents"><div><strong>Context</strong><small>Read materials</small></div><div><strong>Research</strong><small>Find missing context</small></div><div><strong>Writer</strong><small>Create draft</small></div></div>
          <span className="arch-down">↓</span><div className="arch-node shared-node"><small>Traceable workspace</small><strong>Shared State + Evidence</strong></div><span className="arch-down">↓</span>
          <div className="arch-review"><div className="arch-node"><strong>Writer Agent</strong></div><Arrow /><div className="arch-node"><strong>Reviewer Agent</strong></div><span className="revision-loop">↶ Revise / gather evidence</span></div><span className="arch-down">↓</span>
          <div className="arch-node approval-node"><small>Safety boundary</small><strong>Human Approval</strong></div><span className="arch-down">↓</span><div className="arch-node action-node"><strong>Email Action</strong><small>Mocked in current MVP</small></div>
        </div>
      </section>

      <section className="comparison-section"><div className="section-shell"><div className="section-intro"><p className="section-kicker light">The product decision</p><h2>Why not just use a single prompt?</h2><p>Different communication tasks need different workflows, context and verification depth.</p></div><div className="comparison-grid"><article className="single-prompt"><small>Traditional AI Email Writer</small><h3>Prompt → LLM → Email</h3><ul><li>User must organize all context</li><li>The same workflow handles every task</li><li>Limited verification</li><li>Weak handling of missing information</li></ul></article><article className="agent-system"><small>ContextMail</small><h3>Goal → Plan → Adapt → Verify</h3><ul><li>Planner determines what the task needs</li><li>Only relevant agents are activated</li><li>Claims are grounded in evidence</li><li>Review can trigger re-planning</li></ul></article></div><p className="comparison-callout">The agent architecture exists to make the workflow fit the task — not to add complexity for its own sake.</p></div></section>

      <section className="evaluation-section section-shell" id="evaluation"><div className="section-intro"><p className="section-kicker">Evaluation</p><h2>Measured, then improved.</h2><p>An 80-case safety suite covers job, PhD, school and ambiguous requests. Results below separate deterministic workflow checks from a small LIVE model run.</p></div><div className="metric-grid">{evaluation.map(([title, value, description]) => <article key={title}><h3>{title}</h3><p>{description}</p><span>{value}</span></article>)}</div><div className="benchmark-note"><i>↗</i><div><strong>The LIVE result did not yet justify the full agent cost.</strong><p>On 12 stratified Qwen3 8B cases, ContextMail was slower (91.0s vs 16.8s), used 2.83 vs 1.0 calls, and completed fewer tasks. The next product focus is reducing reviewer/re-plan loops and validating with real evidence.</p></div></div></section>

      <section className="roadmap-section"><div className="section-shell"><div className="section-intro"><p className="section-kicker light">Delivery status</p><h2>Live locally. Safe in the demo.</h2><p>The static portfolio never calls external services; authenticated capabilities are available only in local LIVE mode.</p></div><div className="roadmap-grid"><article><small>Implemented</small>{["Adaptive Planner routing", "Brave Search provider", "Traceable Evidence Store", "Writer / Reviewer re-planning", "Microsoft Graph Mail.Send", "80-case evaluation suite", "Human approval boundary"].map(item => <p key={item}><span>✓</span>{item}</p>)}</article><article><small>Next validation</small>{["Blinded human draft ratings", "Real-user edit distance", "Authenticated research trials", "Outlook delivery testing", "Cost / latency tuning"].map(item => <p key={item}><span>○</span>{item}</p>)}</article></div></div></section>

      <footer className="site-footer"><div><a className="brand footer-brand" href="#top">Context<span>Mail</span></a><p>From materials to ready-to-send emails — planned, grounded and human-approved.</p></div><div><a href="#demo">Interactive Demo</a><a href="#architecture">Architecture</a><a href="https://github.com/nbrhyq/ContextMail" target="_blank" rel="noreferrer">GitHub ↗</a></div><small>AI Communication Agent · Portfolio MVP</small></footer>
    </main>
  );
}
