import { ArrowRight, Search } from "lucide-react";

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
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={PLACEHOLDER}
          disabled={loading}
          className="flex-1 min-w-0 bg-transparent outline-none text-text"
          style={{ fontSize: hero ? "15px" : "14.5px", padding: "var(--space-2) 0" }}
        />
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
              Find alternatives
              <ArrowRight size={16} strokeWidth={2.75} />
            </>
          ) : (
            "Search"
          )}
        </button>
      </div>
    </form>
  );
}
