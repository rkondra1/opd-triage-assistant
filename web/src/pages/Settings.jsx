import { useEffect, useState } from "react";
import AppLayout from "../components/AppLayout.jsx";

const KEY = "opd_settings";
const DEFAULTS = {
  showConfidence: true,
  confirmRemove: false,
  defaultSex: "M",
  defaultDepartmentHint: true,
};

function load() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || "{}") };
  } catch {
    return { ...DEFAULTS };
  }
}

export default function Settings() {
  const [settings, setSettings] = useState(load);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!saved) return;
    const t = setTimeout(() => setSaved(false), 2000);
    return () => clearTimeout(t);
  }, [saved]);

  function set(key, value) {
    setSettings((s) => ({ ...s, [key]: value }));
    setSaved(false);
  }

  function save() {
    localStorage.setItem(KEY, JSON.stringify(settings));
    setSaved(true);
  }

  function reset() {
    setSettings({ ...DEFAULTS });
    localStorage.setItem(KEY, JSON.stringify(DEFAULTS));
    setSaved(true);
  }

  return (
    <AppLayout title="Settings" subtitle="Personal preferences (saved on this device)">
      <div className="card settings-card">
        <h3 className="card-title">Display</h3>

        <Toggle
          label="Show model confidence on results"
          checked={settings.showConfidence}
          onChange={(v) => set("showConfidence", v)}
        />
        <Toggle
          label="Show recommended-department hint"
          checked={settings.defaultDepartmentHint}
          onChange={(v) => set("defaultDepartmentHint", v)}
        />

        <h3 className="card-title spaced">Workflow</h3>
        <Toggle
          label="Ask for confirmation before removing a patient from the queue"
          checked={settings.confirmRemove}
          onChange={(v) => set("confirmRemove", v)}
        />

        <label className="field inline-field">
          <span className="field-label light">Default sex on intake form</span>
          <select value={settings.defaultSex} onChange={(e) => set("defaultSex", e.target.value)}>
            <option value="M">M</option>
            <option value="F">F</option>
          </select>
        </label>

        <div className="settings-actions">
          <button className="btn-primary compact" onClick={save}>Save changes</button>
          <button className="btn-ghost dark" onClick={reset}>Reset to defaults</button>
          {saved && <span className="saved-note">Saved ✓</span>}
        </div>
      </div>
    </AppLayout>
  );
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="toggle-row">
      <span>{label}</span>
      <button
        type="button"
        className={`switch ${checked ? "on" : ""}`}
        onClick={() => onChange(!checked)}
        aria-pressed={checked}
      >
        <span className="knob" />
      </button>
    </label>
  );
}
