import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import AppLayout from "../components/AppLayout.jsx";
import { useQueue } from "../queue/QueueContext.jsx";
import { levelDisplay } from "../lib/triage.js";

export default function Patients() {
  const { items } = useQueue();
  const [query, setQuery] = useState("");
  const [levelFilter, setLevelFilter] = useState("all");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter((i) => {
      const name = (i.patient?.name || "").toLowerCase();
      const complaint = (i.complaint || "").toLowerCase();
      const matchesQuery = !q || name.includes(q) || complaint.includes(q);
      const lvl = i.result?.triage_level;
      const matchesLevel =
        levelFilter === "all" ||
        (levelFilter === "abstain"
          ? i.result?.abstained || lvl === "ABSTAIN"
          : String(lvl) === levelFilter);
      return matchesQuery && matchesLevel;
    });
  }, [items, query, levelFilter]);

  return (
    <AppLayout title="Patients" subtitle={`${items.length} patient record(s) this session`}>
      <div className="card">
        <div className="toolbar">
          <input
            className="search"
            placeholder="Search by name or complaint…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)}>
            <option value="all">All levels</option>
            <option value="1">Level 1</option>
            <option value="2">Level 2</option>
            <option value="3">Level 3</option>
            <option value="4">Level 4</option>
            <option value="5">Level 5</option>
            <option value="abstain">Sent to nurse</option>
          </select>
        </div>

        {items.length === 0 ? (
          <div className="result-list-empty">
            No patients yet. Assess one on the <Link to="/triage">New triage</Link> screen.
          </div>
        ) : filtered.length === 0 ? (
          <div className="result-list-empty">No patients match your search.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Age / Sex</th>
                <th>Complaint</th>
                <th>Level</th>
                <th>Department</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((i) => {
                const meta = levelDisplay(i.result);
                return (
                  <tr key={i.id}>
                    <td className="strong">{i.patient?.name || "Unnamed"}</td>
                    <td>{i.patient?.age} / {i.patient?.sex}</td>
                    <td className="truncate" title={i.complaint}>{i.complaint}</td>
                    <td>
                      <span className="level-pill" style={{ background: meta.color }}>
                        {meta.name}
                      </span>
                    </td>
                    <td>{i.result?.department}</td>
                    <td className={i.status === "seen" ? "muted" : ""}>
                      {i.status === "seen" ? "Seen" : "Waiting"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </AppLayout>
  );
}
