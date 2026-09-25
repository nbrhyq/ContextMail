"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";

type DocumentInfo = { id: string; filename: string; size_bytes?: number };
type PlanStep = { id: string; agent: string; action: string; tools: string[] };
type TraceEvent = { actor: string; action: string; status: string; summary: string };
type Draft = { recipient: string; subject: string; body: string; attachments: string[] };
type Run = {
  id: string;
  status: string;
  mock_message_id?: string;
  state: {
    intent: string;
    missing_context: string[];
    execution_plan: PlanStep[];
    execution_trace: TraceEvent[];
    draft?: Draft;
    approval_status: string;
    llm_call_count: number;
    iteration_count: number;
  };
};

const intentNames: Record<string, string> = {
  JOB_APPLICATION: "Job application",
  PHD_OUTREACH: "PhD outreach",
  SCHOOL_AFFAIRS: "School affairs",
  OTHER: "General communication",
  UNCERTAIN: "Needs clarification",
};

export default function Home() {
  const [goal, setGoal] = useState("");
  const [recipient, setRecipient] = useState({ name: "", email: "", role: "", organization: "" });
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const ready = run?.status === "READY_FOR_APPROVAL";
  const statusText = useMemo(() => {
    if (!run) return "Describe what you want to accomplish.";
    if (run.status === "NEEDS_INPUT") return `More information needed: ${run.state.missing_context.join(", ")}`;
    if (run.status === "SENT") return `Mock email action complete · ${run.mock_message_id}`;
    return run.status.replaceAll("_", " ").toLowerCase();
  }, [run]);

  async function uploadFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    setBusy(true);
    setError("");
    try {
      const uploaded = await Promise.all(files.map(async (file) => {
        const form = new FormData();
        form.append("file", file);
        const response = await fetch(`${API}/uploads`, { method: "POST", body: form });
        if (!response.ok) throw new Error((await response.json()).detail ?? "Upload failed");
        return response.json() as Promise<DocumentInfo>;
      }));
      setDocuments((current) => [...current, ...uploaded]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Upload failed");
    } finally {
      setBusy(false);
      event.target.value = "";
    }
  }

  async function start(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setRun(null);
    try {
      const response = await fetch(`${API}/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_request: goal, recipient, document_ids: documents.map((item) => item.id) }),
      });
      if (!response.ok) throw new Error((await response.json()).detail ?? "Agent run failed");
      const nextRun: Run = await response.json();
      setRun(nextRun);
      setDraft(nextRun.state.draft ?? null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Agent run failed");
    } finally {
      setBusy(false);
    }
  }

  async function saveDraft() {
    if (!run || !draft) return;
    setBusy(true);
    const response = await fetch(`${API}/runs/${run.id}/draft`, {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(draft),
    });
    const updated = await response.json();
    setRun(updated);
    setDraft(updated.state.draft);
    setBusy(false);
  }

  async function decide(action: "approve" | "reject") {
    if (!run) return;
    setBusy(true);
    const response = await fetch(`${API}/runs/${run.id}/${action}`, { method: "POST" });
    const updated = await response.json();
    setRun(updated);
    setBusy(false);
  }

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#">Context<span>Mail</span></a>
        <div className="status-dot"><i /> Mock-safe mode</div>
      </header>

      <section className="hero">
        <p className="eyebrow">Intent-aware communication agent</p>
        <h1>Turn context into<br /><em>considered communication.</em></h1>
        <p className="lead">ContextMail plans the work, gathers evidence, drafts, reviews, and waits for you before taking action.</p>
      </section>

      <div className="workspace">
        <form className="panel compose" onSubmit={start}>
          <div className="panel-head"><span>01</span><div><h2>Set the goal</h2><p>Tell the agent what outcome you need.</p></div></div>
          <label className="field-label" htmlFor="goal">Communication goal</label>
          <textarea id="goal" value={goal} onChange={(event) => setGoal(event.target.value)} required
            placeholder="Use my CV and research proposal, research Professor Chen’s recent work, and draft an email asking about PhD opportunities." />

          <div className="divider" />
          <div className="field-row">
            <label><span>Recipient name</span><input value={recipient.name} onChange={(e) => setRecipient({...recipient, name: e.target.value})} placeholder="Prof. Alex Chen" /></label>
            <label><span>Email</span><input type="email" value={recipient.email} onChange={(e) => setRecipient({...recipient, email: e.target.value})} placeholder="alex@university.edu" /></label>
          </div>
          <div className="field-row">
            <label><span>Role</span><input value={recipient.role} onChange={(e) => setRecipient({...recipient, role: e.target.value})} placeholder="Professor" /></label>
            <label><span>Organization</span><input value={recipient.organization} onChange={(e) => setRecipient({...recipient, organization: e.target.value})} placeholder="University" /></label>
          </div>

          <label className="upload">
            <input type="file" multiple accept=".pdf,.docx,.txt" onChange={uploadFiles} />
            <span className="upload-icon">＋</span>
            <strong>Add supporting materials</strong>
            <small>PDF, DOCX or TXT · up to 10 MB</small>
          </label>
          {documents.length > 0 && <div className="chips">{documents.map((doc) => <span key={doc.id}>↗ {doc.filename}</span>)}</div>}
          {error && <p className="error">{error}</p>}
          <button className="primary" disabled={busy || !goal.trim()}>{busy ? "Working…" : "Start agent"}<b>→</b></button>
        </form>

        <section className="panel result">
          <div className="panel-head"><span>02</span><div><h2>Agent workspace</h2><p>{statusText}</p></div></div>
          {!run && <div className="empty-state"><div className="orb"><i /><i /><i /></div><h3>Ready when you are</h3><p>Your plan, evidence trail, and reviewed draft will appear here.</p></div>}
          {run && <>
            <div className="intent-row"><span className="tag">{intentNames[run.state.intent] ?? run.state.intent}</span><small>{run.state.llm_call_count} model calls · {run.state.iteration_count} revisions</small></div>
            <div className="timeline">
              {run.state.execution_trace.map((event, index) => <div className="trace" key={`${event.actor}-${index}`}><i>✓</i><div><strong>{event.actor.replaceAll("_", " ")}</strong><p>{event.summary}</p></div></div>)}
            </div>
            {run.state.missing_context.length > 0 && <div className="notice"><strong>Input required</strong>{run.state.missing_context.join(" · ")}</div>}
            {draft && <div className="draft">
              <div className="draft-title"><h3>Email preview</h3><span>{run.state.approval_status.toLowerCase()}</span></div>
              <label><span>To</span><input value={draft.recipient} onChange={(e) => setDraft({...draft, recipient: e.target.value})} /></label>
              <label><span>Subject</span><input value={draft.subject} onChange={(e) => setDraft({...draft, subject: e.target.value})} /></label>
              <textarea value={draft.body} onChange={(e) => setDraft({...draft, body: e.target.value})} />
              {draft.attachments.length > 0 && <p className="attachments">Attachments · {draft.attachments.join(", ")}</p>}
              {ready && <div className="actions"><button type="button" className="secondary" onClick={saveDraft} disabled={busy}>Save edit</button><button type="button" className="reject" onClick={() => decide("reject")} disabled={busy}>Reject</button><button type="button" className="approve" onClick={() => decide("approve")} disabled={busy}>Approve mock send →</button></div>}
            </div>}
          </>}
        </section>
      </div>
      <footer><span>Evidence grounded</span><span>Human approved</span><span>Traceable by design</span></footer>
    </main>
  );
}
