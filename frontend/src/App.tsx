import { useState } from "react";

import { searchProducts } from "@/api/client";
import type { Product, SearchResponse } from "@/api/client";
import SearchBar from "@/components/SearchBar";
import TargetProductCard from "@/components/TargetProductCard";
import AlternativeTierList from "@/components/AlternativeTierList";
import SpecBreakdownModal from "@/components/SpecBreakdownModal";
import HoneyDrop from "@/components/HoneyDrop";

type AppState = "idle" | "loading" | "results" | "error";

// ponytail: a Google Form stands in for a real feedback endpoint because the
// repo has no working datastore yet — an endpoint would mean provisioning one
// first. Replace with POST /api/feedback once there is somewhere to put it.
const FEEDBACK_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf0WtkQRAguepMWqBOKYo-e3HQR2Ed6yip4oglBy49RQEGAkg/viewform?usp=publish-editor";

function LoadingSkeleton() {
  return (
    <div className="flex flex-col gap-4 animate-fade-in">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="skeleton rounded-2xl h-24"
          style={{ animationDelay: `${i * 0.1}s`, opacity: 1 - i * 0.15 }}
        />
      ))}
    </div>
  );
}

function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="glass-card honey-shadow rounded-3xl p-6 text-center animate-fade-in-up">
      <h2 className="text-base font-bold mb-1.5" style={{ color: "#7c4a00" }}>
        Search unavailable
      </h2>
      <p className="text-sm font-mono break-words" style={{ color: "#a16207" }}>
        {message}
      </p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-5 animate-fade-in">
      <div className="animate-drop-bounce">
        <HoneyDrop size={72} />
      </div>
      <div className="text-center">
        <h2 className="text-xl font-bold mb-1.5" style={{ color: "#7c4a00" }}>
          Find sweeter deals
        </h2>
        <p className="text-sm max-w-xs" style={{ color: "#a16207" }}>
          Paste a product URL, search by name, or describe what you need — we find the best quality alternatives at the lowest price.
        </p>
      </div>
      <div className="flex gap-4 text-center">
        {[
          { label: "Paste URL", sub: "From any retailer" },
          { label: "Search Name", sub: "Exact product match" },
          { label: "Describe It", sub: "We find alternatives" },
        ].map((tip) => (
          <div
            key={tip.label}
            className="glass-card rounded-2xl px-4 py-3 text-center"
            style={{ minWidth: "90px" }}
          >
            <p className="text-xs font-semibold" style={{ color: "#7c4a00" }}>
              {tip.label}
            </p>
            <p className="text-[10px] mt-0.5" style={{ color: "#a16207" }}>
              {tip.sub}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [appState, setAppState] = useState<AppState>("idle");
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState("");
  const [compareProduct, setCompareProduct] = useState<Product | null>(null);

  async function handleSearch(query: string) {
    setAppState("loading");
    setResults(null);
    try {
      setResults(await searchProducts({ query }));
      setAppState("results");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
      setAppState("error");
    }
  }

  // No resolved target means the backend read the query as a description, so
  // there is nothing to anchor the comparison against — echo the query instead.
  const describedOnly = results !== null && results.targetProduct === null;

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(160deg, #fff8e1 0%, #ffe082 55%, #ffcc02 100%)" }}>
      {/* Header */}
      <header
        className="sticky top-0 z-30 px-4 py-3"
        style={{
          background: "rgba(255,248,225,0.8)",
          backdropFilter: "blur(16px)",
          borderBottom: "1px solid rgba(245,166,35,0.15)",
        }}
      >
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <div className="animate-drop-bounce flex-shrink-0">
            <HoneyDrop size={36} />
          </div>
          <div className="flex-shrink-0">
            <span
              className="text-xl font-extrabold tracking-tight"
              style={{ color: "#e87d00", letterSpacing: "-0.02em" }}
            >
              nectarly
            </span>
            <span className="text-xs ml-2 font-medium" style={{ color: "#a16207" }}>
              find sweeter deals
            </span>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-2xl mx-auto px-4 py-8 flex flex-col gap-6">
        <section className="flex flex-col gap-3">
          <SearchBar loading={appState === "loading"} onSearch={handleSearch} />
        </section>

        {appState === "loading" && <LoadingSkeleton />}

        {appState === "idle" && <EmptyState />}

        {appState === "error" && <ErrorPanel message={error} />}

        {appState === "results" && results && (
          <section className="flex flex-col gap-6">
            {results.targetProduct && <TargetProductCard product={results.targetProduct} />}

            {describedOnly && (
              <div className="animate-fade-in-up text-center py-2">
                <p className="text-sm font-medium" style={{ color: "#7c4a00" }}>
                  Showing best matches for: <em>"{results.query}"</em>
                </p>
              </div>
            )}

            <div
              className="animate-fade-in-up flex items-center justify-between"
              style={{ animationDelay: "0.1s" }}
            >
              <h2 className="text-base font-bold" style={{ color: "#7c4a00" }}>
                {describedOnly ? "Best Alternatives Found" : "Cheaper Alternatives"}
              </h2>
              <span
                className="text-xs font-mono px-2.5 py-1 rounded-xl"
                style={{ background: "rgba(245,166,35,0.15)", color: "#b45309" }}
              >
                {results.tiers.tier1.length + results.tiers.tier2.length + results.tiers.tier3.length} results
              </span>
            </div>

            <AlternativeTierList tiers={results.tiers} onCompare={setCompareProduct} />
          </section>
        )}
      </main>

      {/* Sits outside <main> but inside the gradient root, so it never competes
          with SpecBreakdownModal's layer below. */}
      <footer className="max-w-2xl mx-auto px-4 pb-8 text-center">
        <a
          href={FEEDBACK_FORM_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="glass-card inline-block rounded-2xl px-4 py-2 text-xs font-semibold transition-all duration-200 hover:opacity-80"
          style={{ color: "#7c4a00" }}
        >
          Send feedback
        </a>
      </footer>

      {compareProduct && (
        <SpecBreakdownModal
          product={compareProduct}
          targetProduct={results?.targetProduct ?? null}
          onClose={() => setCompareProduct(null)}
        />
      )}
    </div>
  );
}
