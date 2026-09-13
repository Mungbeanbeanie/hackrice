import { useEffect, useRef, useState } from "react";
import { ArrowRight, Search } from "lucide-react";

import { getAutocomplete } from "@/api/client";
import { getSuggestion } from "@/lib/autocomplete";

interface Props {
  value: string;
  onChange: (value: string) => void;
  loading: boolean;
  onSearch: (query: string) => void;
  // hero = landing page's large pill ("Find alternatives" + arrow icon);
  // compact = the sticky app header's smaller pill ("Search").
  variant?: "hero" | "compact";
}

// One box for all three search modes — the backend parses the raw string to
// decide whether it's a URL, an exact product, or a description. Anything
// non-empty is therefore valid input here.
const PLACEHOLDER = "Paste a link, name a product, or describe what you need";

export default function SearchBar({ value, onChange, loading, onSearch, variant = "compact" }: Props) {
  const hero = variant === "hero";
  const suggestion = getSuggestion(value);
  const suffix = suggestion ? suggestion.slice(value.length) : "";

  // True search-as-you-type dropdown, additive alongside the ghost suffix
  // above — separate state, separate data source (backend Trie over real
  // search history + curated guesses, not the frontend-only curated list).
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [highlighted, setHighlighted] = useState(-1);
  const [focused, setFocused] = useState(false);
  // Escape doesn't blur the input (DOM focus stays put), so `focused` alone
  // can't represent "user dismissed the dropdown" — it would never reopen on
  // further typing. Separate flag, cleared whenever the query changes.
  const [dismissed, setDismissed] = useState(false);
  const dropdownVisible = focused && !dismissed && suggestions.length > 0;

  // Tracks the most recent input value across renders so an in-flight
  // request's `.then` can detect it's stale (superseded by a later keystroke
  // that fired its own request before this one resolved) and discard itself
  // instead of clobbering fresher suggestions.
  const latestValueRef = useRef(value);
  latestValueRef.current = value;

  useEffect(() => {
    setDismissed(false);
    if (!value.trim()) {
      setSuggestions([]);
      setHighlighted(-1);
      return;
    }
    const timer = window.setTimeout(() => {
      getAutocomplete(value)
        .then((results) => {
          if (latestValueRef.current !== value) return;
          setSuggestions(results);
          setHighlighted(-1);
        })
        .catch(() => {
          if (latestValueRef.current !== value) return;
          setSuggestions([]);
        });
    }, 150);
    return () => window.clearTimeout(timer);
  }, [value]);

  function handleSelect(term: string) {
    onChange(term);
    setSuggestions([]);
    setHighlighted(-1);
    setFocused(false);
    onSearch(term);
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (value.trim()) onSearch(value.trim());
      }}
      // The compact variant takes a row of its own on a phone, which keeps the
      // app header's account pill on the first row — where AccountMenu's
      // dropdown offset assumes it is.
      className={hero ? "w-full" : "flex-1 min-w-[200px] max-sm:order-last max-sm:basis-full"}
      style={hero ? { maxWidth: "560px" } : undefined}
    >
      <div className="relative">
      <div
        className="flex items-center rounded-full bg-neutral-100 border border-divider"
        style={{
          gap: "var(--space-3)",
          padding: hero
            ? "var(--space-2) var(--space-2) var(--space-2) var(--space-4)"
            : "var(--space-1) var(--space-1) var(--space-1) var(--space-4)",
          boxShadow: hero ? "var(--shadow-md)" : "none",
        }}
      >
        <Search size={hero ? 19 : 17} color="var(--color-accent)" strokeWidth={2.75} className="flex-shrink-0" />
        <div className="relative flex-1 min-w-0">
          {suffix && (
            <div
              aria-hidden="true"
              className="absolute inset-0 flex items-center whitespace-pre pointer-events-none"
              style={{ fontSize: hero ? "15px" : "14.5px", padding: "var(--space-2) 0" }}
            >
              <span style={{ visibility: "hidden" }}>{value}</span>
              <span className="text-neutral-500">{suffix}</span>
            </div>
          )}
          <input
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            onKeyDown={(e) => {
              if (e.key === "Tab" && suffix) {
                e.preventDefault();
                onChange(value + suffix);
                return;
              }
              if (!dropdownVisible) return;
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setHighlighted((h) => Math.min(h + 1, suggestions.length - 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setHighlighted((h) => Math.max(h - 1, -1));
              } else if (e.key === "Enter" && highlighted >= 0) {
                // Only intercepts Enter when a row is highlighted — otherwise
                // falls through to the form's own submit (or the ghost
                // suffix's own Tab-accept above), unchanged.
                const term = suggestions[highlighted];
                if (term) {
                  e.preventDefault();
                  handleSelect(term);
                }
              } else if (e.key === "Escape") {
                setDismissed(true);
                setHighlighted(-1);
              }
            }}
            placeholder={PLACEHOLDER}
            disabled={loading}
            className="relative w-full bg-transparent outline-none text-text"
            style={{ fontSize: hero ? "15px" : "14.5px", padding: "var(--space-2) 0" }}
          />
        </div>
        <button
          type="submit"
          disabled={!value.trim() || loading}
          className="flex-shrink-0 whitespace-nowrap inline-flex items-center rounded-full bg-accent text-bg font-heading hover:bg-accent-600 transition-colors disabled:opacity-40 cursor-pointer"
          style={{
            padding: hero ? "var(--space-3) var(--space-4)" : "var(--space-2) var(--space-4)",
            fontSize: hero ? "14.5px" : "14px",
            lineHeight: 1.2,
            gap: "var(--space-2)",
          }}
        >
          {loading ? (
            <span className="w-4 h-4 rounded-full border-2 border-bg/40 border-t-bg animate-spin" />
          ) : hero ? (
            <>
              Search
              <ArrowRight size={16} strokeWidth={2.75} />
            </>
          ) : (
            "Search"
          )}
        </button>
      </div>
      {dropdownVisible && (
        <ul
          role="listbox"
          className="absolute left-0 right-0 top-full z-10 rounded-lg border border-divider bg-bg shadow-md overflow-hidden"
          style={{ marginTop: "var(--space-1)" }}
        >
          {suggestions.map((term, i) => (
            <li
              key={term}
              role="option"
              aria-selected={i === highlighted}
              // Fires before the input's blur, so clicking a row doesn't
              // close the dropdown before onClick runs.
              onMouseDown={(e) => e.preventDefault()}
              onMouseEnter={() => setHighlighted(i)}
              onClick={() => handleSelect(term)}
              className={i === highlighted ? "bg-neutral-100 cursor-pointer" : "cursor-pointer"}
              style={{ padding: "var(--space-2) var(--space-4)", fontSize: "14px" }}
            >
              {term}
            </li>
          ))}
        </ul>
      )}
      </div>
    </form>
  );
}
