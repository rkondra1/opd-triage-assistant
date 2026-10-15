import { createContext, useContext, useEffect, useMemo, useState } from "react";

// A lightweight, client-side patient queue. Assessed patients are kept in the
// browser (localStorage) so the Queue and Dashboard screens have real data to
// work with without requiring a database. Each entry stores the triage result
// returned by the backend ML engine.
const QueueContext = createContext(null);
const STORAGE_KEY = "opd_queue";

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function QueueProvider({ children }) {
  const [items, setItems] = useState(load);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  const value = useMemo(
    () => ({
      items,
      add(entry) {
        const id =
          (typeof crypto !== "undefined" && crypto.randomUUID && crypto.randomUUID()) ||
          String(Date.now() + Math.random());
        setItems((prev) => [
          {
            id,
            createdAt: new Date().toISOString(),
            status: "waiting",
            ...entry,
          },
          ...prev,
        ]);
        return id;
      },
      updateStatus(id, status) {
        setItems((prev) =>
          prev.map((it) => (it.id === id ? { ...it, status } : it))
        );
      },
      remove(id) {
        setItems((prev) => prev.filter((it) => it.id !== id));
      },
      clear() {
        setItems([]);
      },
    }),
    [items]
  );

  return <QueueContext.Provider value={value}>{children}</QueueContext.Provider>;
}

export function useQueue() {
  const ctx = useContext(QueueContext);
  if (!ctx) throw new Error("useQueue must be used within QueueProvider");
  return ctx;
}

// Sort key: ABSTAIN first (needs a human now), then by triage level (1 = most
// urgent), then oldest first within a level.
export function queueSortKey(entry) {
  const lvl = entry.result?.triage_level;
  const isAbstain = lvl === "ABSTAIN" || entry.result?.abstained;
  const levelNum = isAbstain ? -1 : Number(lvl) || 99;
  return [levelNum, new Date(entry.createdAt).getTime()];
}
