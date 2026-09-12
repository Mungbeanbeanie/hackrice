import { useState } from "react";

interface Props {
  loading: boolean;
  onSearch: (query: string) => void;
}

// One box for all three search modes — the backend parses the raw string to
// decide whether it's a URL, an exact product, or a description. Anything
// non-empty is therefore valid input here.
const PLACEHOLDER = "Paste a product link, search a product, or describe what you need…";

export default function SearchBar({ loading, onSearch }: Props) {
  const [value, setValue] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (value.trim()) onSearch(value.trim());
      }}
      className="w-full"
    >
      <div
        className="flex items-center gap-3 px-4 py-3 rounded-3xl transition-all duration-200"
        style={{
          background: "rgba(255,255,255,0.85)",
          border: "2px solid rgba(245,166,35,0.4)",
          boxShadow: "0 4px 20px rgba(180,83,9,0.12)",
        }}
      >
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={PLACEHOLDER}
          className="flex-1 bg-transparent outline-none text-base placeholder:text-amber-700/40 font-medium"
          style={{ color: "#3d2000" }}
          disabled={loading}
        />
        {value && (
          <button
            type="button"
            onClick={() => setValue("")}
            className="text-amber-700/40 hover:text-amber-700 transition-colors text-lg leading-none"
          >
            ×
          </button>
        )}
        <button
          type="submit"
          disabled={!value.trim() || loading}
          className="flex items-center gap-2 px-5 py-2 rounded-2xl text-sm font-semibold text-white transition-all duration-200 disabled:opacity-40"
          style={{
            background: "linear-gradient(135deg, #f5a623 0%, #e87d00 100%)",
            boxShadow: "0 2px 10px rgba(180,83,9,0.3)",
          }}
        >
          {loading ? (
            <span
              className="w-4 h-4 rounded-full border-2 border-white/40 border-t-white"
              style={{ animation: "spin 0.7s linear infinite" }}
            />
          ) : (
            "Find Deals"
          )}
        </button>
      </div>
    </form>
  );
}
