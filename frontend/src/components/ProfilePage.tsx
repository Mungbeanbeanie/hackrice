import { useEffect, useState } from "react";
import { ArrowLeft, RotateCcw, Trash2 } from "lucide-react";

import {
  clearSearchHistory,
  fetchSearchHistory,
  type Account,
  type SearchHistoryItem,
} from "@/api/client";

interface Props {
  account: Account;
  onBack: () => void;
  onRerun: (query: string) => void;
}

const MODE_LABEL: Record<string, string> = {
  url: "Link",
  exact_product: "Exact product",
  description: "Description",
};

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const mins = Math.round((Date.now() - then) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  if (mins < 1440) return `${Math.round(mins / 60)}h ago`;
  return new Date(iso).toLocaleDateString();
}

export default function ProfilePage({ account, onBack, onRerun }: Props) {
  const [rows, setRows] = useState<SearchHistoryItem[] | null>(null);
  const [error, setError] = useState("");
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    fetchSearchHistory()
      .then(setRows)
      .catch((e) => setError(e instanceof Error ? e.message : "Couldn't load history"));
  }, []);

  async function handleClear() {
    if (clearing || !rows?.length) return;
    if (!confirm(`Delete all ${rows.length} searches? This can't be undone.`)) return;
    setClearing(true);
    try {
      await clearSearchHistory();
      setRows([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't clear history");
    } finally {
      setClearing(false);
    }
  }

  return (
    <div className="min-h-screen">
      <div
        className="mx-auto"
        style={{ maxWidth: "900px", padding: "clamp(20px, 4vw, 44px) clamp(16px, 4vw, 32px) 80px" }}
      >
        <button
          onClick={onBack}
          className="inline-flex items-center bg-transparent border-none cursor-pointer text-neutral-700 hover:text-text font-semibold"
          style={{ gap: "var(--space-2)", padding: 0, fontSize: "13.5px" }}
        >
          <ArrowLeft size={16} strokeWidth={2.75} /> Back
        </button>

        <header className="flex items-center" style={{ gap: "var(--space-4)", margin: "var(--space-6) 0 var(--space-8)" }}>
          <span
            className="rounded-full bg-accent-200 text-accent-800 inline-flex items-center justify-center overflow-hidden flex-shrink-0"
            style={{ width: 64, height: 64, fontSize: "24px", fontFamily: "var(--font-heading)" }}
          >
            {account.avatar ? (
              <img src={account.avatar} alt="" className="w-full h-full object-cover" />
            ) : (
              (account.display_name || account.email).charAt(0).toUpperCase()
            )}
          </span>
          <div className="min-w-0">
            <h1 style={{ fontSize: "clamp(24px, 4vw, 32px)", lineHeight: 1.15 }}>
              {account.display_name || account.email}
            </h1>
            <p className="text-neutral-600 truncate" style={{ fontSize: "14px", marginTop: "var(--space-1)" }}>
              {account.email} · joined {new Date(account.created_at).toLocaleDateString()}
            </p>
          </div>
        </header>

        <div className="flex items-center flex-wrap" style={{ gap: "var(--space-3)", marginBottom: "var(--space-4)" }}>
          <h2 style={{ fontSize: "19px", marginRight: "auto" }}>Search history</h2>
          {!!rows?.length && (
            <button
              onClick={handleClear}
              disabled={clearing}
              className="inline-flex items-center rounded-full border border-divider bg-transparent cursor-pointer font-semibold text-neutral-700 hover:bg-neutral-200 transition-colors disabled:opacity-50"
              style={{ gap: "var(--space-2)", padding: "var(--space-2) var(--space-3)", fontSize: "13px" }}
            >
              <Trash2 size={14} strokeWidth={2.75} />
              {clearing ? "Clearing…" : "Clear history"}
            </button>
          )}
        </div>

        {/* Searches stay linked to the account even with sharing off, so this
            explains the one case where the table can look wrongly empty. */}
        {!account.share_data && (
          <p
            className="bg-accent-100 border border-divider rounded-md text-neutral-700"
            style={{ padding: "var(--space-3)", fontSize: "13px", marginBottom: "var(--space-4)" }}
          >
            Data sharing is off. Your searches are still saved here — they're just
            left out of our aggregate analytics.
          </p>
        )}

        {error && (
          <p className="text-accent-700" style={{ fontSize: "14px" }}>
            {error}
          </p>
        )}

        {rows === null && !error && (
          <p className="text-neutral-600" style={{ fontSize: "14px" }}>
            Loading…
          </p>
        )}

        {rows?.length === 0 && (
          <p className="text-neutral-600" style={{ fontSize: "14px" }}>
            No searches yet. Anything you look up will show up here.
          </p>
        )}

        {!!rows?.length && (
          <div className="overflow-x-auto border border-divider rounded-md bg-neutral-100">
            <table className="w-full" style={{ borderCollapse: "collapse", fontSize: "13.5px" }}>
              <thead>
                <tr className="text-left text-neutral-600">
                  <th style={{ padding: "var(--space-3)", fontWeight: 600 }}>When</th>
                  <th style={{ padding: "var(--space-3)", fontWeight: 600 }}>Search</th>
                  <th style={{ padding: "var(--space-3)", fontWeight: 600 }}>Mode</th>
                  <th style={{ padding: "var(--space-3)", fontWeight: 600 }}>Results</th>
                  <th style={{ padding: "var(--space-3)" }}>
                    <span className="sr-only">Run again</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} className="border-t border-divider">
                    <td className="text-neutral-600 whitespace-nowrap" style={{ padding: "var(--space-3)" }}>
                      {relativeTime(r.created_at)}
                    </td>
                    <td className="font-semibold" style={{ padding: "var(--space-3)" }}>
                      {r.query}
                    </td>
                    <td className="text-neutral-600 whitespace-nowrap" style={{ padding: "var(--space-3)" }}>
                      {MODE_LABEL[r.mode] ?? r.mode}
                    </td>
                    <td className="text-neutral-600" style={{ padding: "var(--space-3)" }}>
                      {r.result_count}
                    </td>
                    <td style={{ padding: "var(--space-3)" }}>
                      <button
                        onClick={() => onRerun(r.query)}
                        title="Run this search again"
                        className="inline-flex items-center rounded-full border border-divider bg-transparent cursor-pointer font-semibold text-text hover:bg-neutral-200 transition-colors whitespace-nowrap"
                        style={{ gap: "var(--space-1)", padding: "var(--space-1) var(--space-2)", fontSize: "12.5px" }}
                      >
                        <RotateCcw size={13} strokeWidth={2.75} /> Again
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
