import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AppLayout from "../components/AppLayout.jsx";
import { useAuth } from "../auth/AuthContext.jsx";
import { useQueue } from "../queue/QueueContext.jsx";
import { api } from "../lib/api.js";
import { levelDisplay } from "../lib/triage.js";

const EMPTY = {
  name: "",
  age: 45,
  sex: "M",
  spo2: 98,
  bp_systolic: 120,
  bp_diastolic: 80,
  pulse: 78,
  temp_c: 37.0,
  chief_complaint: "",
  known_conditions: "none",
  medications: "none",
};

export default function Triage() {
  const { token } = useAuth();
  const { add } = useQueue();
  const navigate = useNavigate();

  const [form, setForm] = useState(EMPTY);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [added, setAdded] = useState(false);

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function assess(e) {
    e.preventDefault();
    setError("");
    setResult(null);
    setAdded(false);
    setLoading(true);
    try {
      const { name, ...record } = form;
      record.chief_complaint = record.chief_complaint || "not stated";
      const res = await api.triage(token, record);
      setResult(res);
    } catch (err) {
      setError(err.message || "Assessment failed.");
    } finally {
      setLoading(false);
    }
  }

  function addToQueue() {
    add({
      patient: { name: form.name || "Unnamed patient", age: form.age, sex: form.sex },
      complaint: form.chief_complaint || "not stated",
      result,
    });
    setAdded(true);
  }

  const meta = result ? levelDisplay(result) : null;

  return (
    <AppLayout title="New triage" subtitle="Assess one patient in under 60 seconds">
      <div className="triage-grid">
        {/* ---- Intake form ---- */}
        <form className="card intake" onSubmit={assess}>
          <h3 className="card-title">Patient intake</h3>

          <div className="grid-2">
            <Field label="Patient name (optional)">
              <input value={form.name} onChange={(e) => set("name", e.target.value)}
                     placeholder="e.g. A. Kumar" />
            </Field>
            <Field label="Age">
              <input type="number" min="0" max="120" value={form.age}
                     onChange={(e) => set("age", Number(e.target.value))} />
            </Field>
          </div>

          <div className="grid-3">
            <Field label="Sex">
              <select value={form.sex} onChange={(e) => set("sex", e.target.value)}>
                <option value="M">M</option>
                <option value="F">F</option>
              </select>
            </Field>
            <Field label="SpO₂ (%)">
              <input type="number" min="0" max="100" value={form.spo2}
                     onChange={(e) => set("spo2", Number(e.target.value))} />
            </Field>
            <Field label="Pulse">
              <input type="number" min="0" max="300" value={form.pulse}
                     onChange={(e) => set("pulse", Number(e.target.value))} />
            </Field>
          </div>

          <div className="grid-3">
            <Field label="BP systolic">
              <input type="number" min="0" max="300" value={form.bp_systolic}
                     onChange={(e) => set("bp_systolic", Number(e.target.value))} />
            </Field>
            <Field label="BP diastolic">
              <input type="number" min="0" max="200" value={form.bp_diastolic}
                     onChange={(e) => set("bp_diastolic", Number(e.target.value))} />
            </Field>
            <Field label="Temp (°C)">
              <input type="number" step="0.1" min="0" max="110" value={form.temp_c}
                     onChange={(e) => set("temp_c", Number(e.target.value))} />
            </Field>
          </div>

          <Field label="Chief complaint (any language / Hinglish is fine)">
            <textarea rows="3" value={form.chief_complaint}
                      onChange={(e) => set("chief_complaint", e.target.value)}
                      placeholder="seene mein dard aur pasina aa raha hai" />
          </Field>

          <div className="grid-2">
            <Field label="Known conditions">
              <input value={form.known_conditions}
                     onChange={(e) => set("known_conditions", e.target.value)} />
            </Field>
            <Field label="Medications">
              <input value={form.medications}
                     onChange={(e) => set("medications", e.target.value)} />
            </Field>
          </div>

          {error && <div className="form-error">{error}</div>}

          <button className="btn-primary" disabled={loading}>
            {loading ? "Assessing…" : "Assess triage"}
          </button>
        </form>

        {/* ---- Result ---- */}
        <div className="card result">
          <h3 className="card-title">Assessment</h3>
          {!result && !loading && (
            <div className="result-empty">
              Fill in the intake form and press <b>Assess triage</b> to see the
              recommended priority from the model + safety rules.
            </div>
          )}
          {loading && <div className="result-empty">Running the model…</div>}

          {result && (
            <>
              <div className="level-banner" style={{ background: meta.color }}>
                <div className="level-top">
                  {result.abstained || result.triage_level === "ABSTAIN"
                    ? "CANNOT ASSESS"
                    : `TRIAGE LEVEL ${result.triage_level}`}
                </div>
                <div className="level-name">{meta.name}</div>
                <div className="level-target">Target: {meta.target}</div>
              </div>

              <div className="result-row">
                <span>Department</span>
                <b>{result.department}</b>
              </div>
              <div className="result-row">
                <span>Model confidence</span>
                <b>{Math.round((result.confidence || 0) * 100)}%</b>
              </div>

              <ResultList title="Red flags detected" items={result.red_flags} tone="red" />
              <ResultList title="Safety rules fired" items={result.rules_fired} tone="amber"
                          empty="none — model decision used directly" />
              <ResultList title="Data-quality warnings" items={result.data_flags} tone="amber"
                          empty="vitals look clean" />
              {result.abstain_reason && (
                <div className="abstain-note">{result.abstain_reason}</div>
              )}

              <div className="result-actions">
                <button className="btn-primary" onClick={addToQueue} disabled={added}>
                  {added ? "Added to queue ✓" : "Add to patient queue"}
                </button>
                {added && (
                  <button className="btn-ghost" onClick={() => navigate("/queue")}>
                    View queue
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </AppLayout>
  );
}

function Field({ label, children }) {
  return (
    <label className="field">
      <span className="field-label light">{label}</span>
      {children}
    </label>
  );
}

function ResultList({ title, items, tone, empty = "none" }) {
  return (
    <div className="result-list">
      <div className="result-list-title">{title}</div>
      {items && items.length ? (
        <ul>
          {items.map((it, i) => (
            <li key={i} className={`chip chip-${tone}`}>{it}</li>
          ))}
        </ul>
      ) : (
        <div className="result-list-empty">{empty}</div>
      )}
    </div>
  );
}
