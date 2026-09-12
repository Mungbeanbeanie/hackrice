import { useCallback, useEffect, useState } from "react";
import { AlertCircle, ArrowLeft, Search, User } from "lucide-react";

import { getCurrentAccount, searchProducts } from "@/api/client";
import type { Account, Group, Product, SearchResponse } from "@/api/client";
import SearchBar from "@/components/SearchBar";
import TargetProductCard from "@/components/TargetProductCard";
import AlternativeGroups, { GROUP_ORDER } from "@/components/AlternativeGroups";
import ComparisonTable from "@/components/ComparisonTable";
import SpecBreakdownModal from "@/components/SpecBreakdownModal";
import LandingPage from "@/components/LandingPage";
import SignInPage from "@/components/SignInPage";
import ExtensionPanel from "@/components/ExtensionPanel";
import CouponPanel from "@/components/CouponPanel";
import HoneyDrop from "@/components/HoneyDrop";

type Screen = "landing" | "app" | "signin" | "extension";
type AppState = "idle" | "loading" | "results" | "error";
type View = "ranked" | "table";

function flattenGroups(groups: Record<Group, Product[]>): Product[] {
  return GROUP_ORDER.flatMap((g) => groups[g]);
}

function EmptyState() {
  const modes = [
    { label: "Paste a link", sub: "Any retailer product page" },
    { label: "Name a product", sub: "Brand and model, as you'd say it" },
    { label: "Describe the job", sub: "No target — we rank against the description" },
  ];
  return (
    <div
      className="mx-auto text-center animate-soft-in"
      style={{ maxWidth: "620px", margin: "clamp(40px, 8vh, 90px) auto" }}
    >
      <div className="mx-auto animate-bob" style={{ width: 76, height: 88 }}>
        <HoneyDrop size={76} />
      </div>
      <h2 style={{ fontSize: "clamp(26px, 3.4vw, 34px)", lineHeight: 1.14, margin: "var(--space-6) 0 var(--space-2)" }}>
        Show us what you were about to buy.
      </h2>
      <p className="text-neutral-800 mx-auto" style={{ maxWidth: "38em", margin: "0 auto var(--space-6)" }}>
        A link, a product name, or a plain description of the job it has to do. All three work — we figure out
        which one you gave us.
      </p>
      <div
        className="grid text-left"
        style={{ gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: "var(--space-3)" }}
      >
        {modes.map((m) => (
          <div key={m.label} className="bg-neutral-100 border border-divider rounded-md" style={{ padding: "var(--space-4)" }}>
            <p style={{ fontSize: "14px", fontWeight: 700, margin: 0 }}>{m.label}</p>
            <p className="text-neutral-700" style={{ fontSize: "12.5px", margin: "var(--space-1) 0 0" }}>
              {m.sub}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="animate-soft-in">
      <div className="flex flex-col items-center" style={{ gap: "var(--space-3)", padding: "var(--space-6) 0 var(--space-8)" }}>
        <div className="flex flex-col items-center justify-end" style={{ height: 92 }}>
          <div style={{ width: 46, height: 54, transformOrigin: "50% 50%", animation: "hopSpin 1.15s linear infinite" }}>
            <HoneyDrop size={46} />
          </div>
          <div
            className="rounded-full bg-accent-800"
            style={{ width: 34, height: 5, marginTop: "var(--space-1)", animation: "hopShadow 1.15s linear infinite" }}
          />
        </div>
        <span className="text-accent-700 font-semibold" style={{ fontSize: "14.5px" }}>
          Searching retailers...
        </span>
      </div>
      <div className="flex flex-col" style={{ gap: "var(--space-3)" }}>
        {[0, 0.15, 0.3].map((delay, i) => (
          <div
            key={i}
            className="rounded-lg"
            style={{
              height: 104,
              opacity: 1 - i * 0.25,
              background: "linear-gradient(90deg, var(--color-neutral-200) 25%, var(--color-neutral-100) 50%, var(--color-neutral-200) 75%)",
              backgroundSize: "200% 100%",
              animation: `sweep 1.5s ease ${delay}s infinite`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div
      className="text-center bg-neutral-100 border border-divider rounded-lg shadow-sm animate-rise-in mx-auto"
      style={{ maxWidth: "520px", margin: "clamp(40px, 8vh, 80px) auto", padding: "var(--space-8)" }}
    >
      <span
        className="inline-flex items-center justify-center rounded-full bg-accent-200 text-accent-800"
        style={{ width: 46, height: 46 }}
      >
        <AlertCircle size={22} strokeWidth={2.75} />
      </span>
      <h2 style={{ fontSize: "25px", lineHeight: 1.2, margin: "var(--space-4) 0 var(--space-2)" }}>
        We couldn't reach the catalogue.
      </h2>
      <p className="text-neutral-800" style={{ margin: "0 0 var(--space-2)" }}>
        Nothing's wrong with your search — the product feed timed out. Try again in a moment.
      </p>
      <p
        className="text-neutral-600"
        style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: "12.5px", margin: "0 0 var(--space-6)" }}
      >
        {message}
      </p>
      <button
        onClick={onRetry}
        className="rounded-full bg-accent text-bg font-heading hover:bg-accent-600 transition-colors cursor-pointer"
        style={{ padding: "var(--space-3) var(--space-6)", fontSize: "14px" }}
      >
        Try again
      </button>
    </div>
  );
}

export default function App() {
  // Extension "Open full comparison" deep-links here with ?q=<title>.
  const initialQuery = new URLSearchParams(window.location.search).get("q") ?? "";
  const [screen, setScreen] = useState<Screen>(initialQuery ? "app" : "landing");
  const [appState, setAppState] = useState<AppState>("idle");
  const [view, setView] = useState<View>("ranked");
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState("");
  const [compareProduct, setCompareProduct] = useState<Product | null>(null);
  const [couponProduct, setCouponProduct] = useState<Product | null>(null);
  const [account, setAccount] = useState<Account | null>(null);
  // Which screen to return to after the sign-in flow — landing and the app
  // header both open the same SignInPage, so "always land back on app" was
  // wrong for the landing entry point.
  const [returnScreen, setReturnScreen] = useState<Screen>("landing");

  useEffect(() => {
    getCurrentAccount().then(setAccount);
  }, []);

  function goTo(next: Screen) {
    // The overlay surviving a screen change was a real bug in the design
    // prototype — clear it on every navigation.
    setCompareProduct(null);
    setCouponProduct(null);
    // Going home means starting over; leaving the last query in the box made
    // the landing page look like it was mid-search.
    if (next === "landing") setQuery("");
    setScreen(next);
  }

  function goToSignIn() {
    setReturnScreen(screen);
    goTo("signin");
  }

  const runSearch = useCallback(async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed) {
      setScreen("app");
      setAppState("idle");
      return;
    }
    setScreen("app");
    setAppState("loading");
    try {
      const res = await searchProducts({ query: trimmed });
      setResults(res);
      setAppState("results");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
      setAppState("error");
    }
  }, []);

  useEffect(() => {
    if (initialQuery) runSearch(initialQuery);
  }, [initialQuery, runSearch]);

  const allProducts = results ? flattenGroups(results.groups) : [];
  const best = allProducts[0];
  // Groups are ordered by equivalence and ranked by value within a group, so
  // the leader is the best match — not necessarily the lowest price anywhere.
  // Everything returned already cleared the quality floor, so a plain min is
  // the cheapest option worth showing.
  const cheapest = allProducts.reduce<Product | undefined>(
    (low, p) => (low === undefined || p.price < low.price ? p : low),
    undefined,
  );

  return (
    <>
      {screen === "landing" && (
        <LandingPage
          query={query}
          onQueryChange={setQuery}
          onSearch={runSearch}
          onGoSignin={goToSignIn}
          onGoExtension={() => goTo("extension")}
        />
      )}

      {screen === "app" && (
        <div>
          <header className="sticky top-0 z-20 bg-bg border-b border-divider" style={{ backdropFilter: "blur(14px)" }}>
            <div
              className="mx-auto flex items-center flex-wrap"
              style={{ maxWidth: "1240px", padding: "12px clamp(16px, 3vw, 36px)", gap: "var(--space-4)" }}
            >
              <button
                onClick={() => goTo("landing")}
                className="flex items-center bg-transparent border-none cursor-pointer"
                style={{ gap: "var(--space-2)", padding: 0 }}
              >
                <div style={{ width: 24, height: 28 }} className="flex-shrink-0">
                  <HoneyDrop size={24} />
                </div>
                <span style={{ fontFamily: "var(--font-heading)", fontSize: "19px", color: "var(--color-accent-700)" }}>
                  nectarly
                </span>
              </button>
              <SearchBar
                variant="compact"
                value={query}
                onChange={setQuery}
                loading={appState === "loading"}
                onSearch={runSearch}
              />
              <button
                onClick={goToSignIn}
                className="inline-flex items-center rounded-full border border-divider bg-transparent font-semibold text-text hover:bg-neutral-200 transition-colors cursor-pointer flex-shrink-0"
                style={{ gap: "var(--space-2)", padding: "var(--space-1) var(--space-2) var(--space-1) var(--space-3)", fontSize: "13.5px" }}
              >
                {account ? account.email : "Sign in"}
                <span
                  className="rounded-full bg-accent-200 text-accent-800 inline-flex items-center justify-center"
                  style={{ width: 26, height: 26 }}
                >
                  <User size={14} strokeWidth={2.75} />
                </span>
              </button>
            </div>
          </header>

          <main className="mx-auto" style={{ maxWidth: "1240px", padding: "clamp(20px, 3vw, 36px) clamp(16px, 3vw, 36px) 80px" }}>
            {appState === "idle" && <EmptyState />}
            {appState === "loading" && <LoadingState />}
            {appState === "error" && <ErrorState message={error} onRetry={() => runSearch(query)} />}

            {appState === "results" && results && (
              <div
                className="flex flex-wrap items-start animate-soft-in"
                style={{ gap: "clamp(20px, 2.6vw, 34px)" }}
              >
                <div className="flex flex-col" style={{ flex: "1 1 460px", minWidth: 0, gap: "var(--space-6)" }}>
                  {results.targetProduct && <TargetProductCard product={results.targetProduct} />}

                  <div className="flex items-center flex-wrap" style={{ gap: "var(--space-3)" }}>
                    <h2
                      className="mr-auto"
                      style={{ fontSize: "clamp(22px, 2.4vw, 27px)", lineHeight: 1.15, margin: 0 }}
                    >
                      {allProducts.length} alternatives worth your attention
                    </h2>
                    <div className="flex bg-surface border border-divider rounded-full" style={{ gap: "var(--space-1)", padding: "var(--space-1)" }}>
                      <button
                        onClick={() => setView("ranked")}
                        className={`rounded-full font-bold cursor-pointer border-none ${view === "ranked" ? "bg-neutral-100 text-text shadow-sm" : "bg-transparent text-neutral-700"}`}
                        style={{ padding: "var(--space-1) var(--space-3)", fontSize: "13px" }}
                      >
                        Ranked
                      </button>
                      <button
                        onClick={() => setView("table")}
                        className={`rounded-full font-bold cursor-pointer border-none ${view === "table" ? "bg-neutral-100 text-text shadow-sm" : "bg-transparent text-neutral-700"}`}
                        style={{ padding: "var(--space-1) var(--space-3)", fontSize: "13px" }}
                      >
                        Side by side
                      </button>
                    </div>
                  </div>

                  {view === "ranked" ? (
                    <AlternativeGroups
                      groups={results.groups}
                      baselinePrice={results.baselinePrice}
                      baselineLabel={
                        results.mode === "description" ? "median price" : "original price"
                      }
                      selectedId={couponProduct?.id ?? null}
                      onCompare={setCompareProduct}
                      onSelect={setCouponProduct}
                    />
                  ) : (
                    <ComparisonTable target={results.targetProduct} products={allProducts} />
                  )}
                </div>

                {best && (
                  <aside
                    className="flex flex-col sticky"
                    style={{ flex: "1 1 285px", minWidth: 0, maxWidth: "360px", gap: "var(--space-4)", top: 88 }}
                  >
                    <div className="bg-accent-2-100 border border-accent-2-300 rounded-lg" style={{ padding: "var(--space-6)" }}>
                      <p
                        className="uppercase text-accent-2-700 font-bold"
                        style={{ fontSize: "11px", letterSpacing: "0.08em", margin: "0 0 var(--space-1)" }}
                      >
                        Possible Savings:
                      </p>
                      <p className="text-accent-2-700" style={{ fontFamily: "var(--font-heading)", fontSize: "clamp(36px, 4vw, 44px)", lineHeight: 1, margin: 0 }}>
                        {results.targetProduct
                          ? `$${(results.targetProduct.price - best.price).toFixed(2)}`
                          : `$${best.price.toFixed(2)}`}
                      </p>
                      <p className="text-accent-2-700" style={{ fontSize: "14px", margin: "var(--space-2) 0 0" }}>
                        at {Math.round(best.matchScore)}% of the product you asked for
                      </p>
                      <div className="border-accent-2-300" style={{ marginTop: "var(--space-4)", paddingTop: "var(--space-3)", borderTopWidth: 1, borderTopStyle: "solid" }}>
                        <a
                          href={best.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:text-accent-700 underline"
                          style={{ fontSize: "13.5px", fontWeight: 700, lineHeight: 1.35 }}
                        >
                          {best.name}
                        </a>
                        <p className="text-accent-2-700" style={{ fontSize: "12.5px", margin: "var(--space-1) 0 0" }}>
                          {[best.brand, best.retailer].filter(Boolean).join(" · ")} ·{" "}
                          {best.rating.toFixed(1)}★ ({best.reviewCount.toLocaleString()})
                        </p>
                      </div>
                    </div>

                    {cheapest && (
                      <div className="bg-neutral-100 border border-divider rounded-lg" style={{ padding: "var(--space-6)" }}>
                        <p
                          className="uppercase text-neutral-700 font-bold"
                          style={{ fontSize: "11px", letterSpacing: "0.08em", margin: "0 0 var(--space-1)" }}
                        >
                          Cheapest option:
                        </p>
                        <p style={{ fontFamily: "var(--font-heading)", fontSize: "clamp(30px, 3.4vw, 38px)", lineHeight: 1, margin: 0 }}>
                          ${cheapest.price.toFixed(2)}
                        </p>
                        <p className="text-neutral-700" style={{ fontSize: "14px", margin: "var(--space-2) 0 0" }}>
                          the lowest price here that still clears the quality floor
                        </p>
                        <div className="border-divider" style={{ marginTop: "var(--space-4)", paddingTop: "var(--space-3)", borderTopWidth: 1, borderTopStyle: "solid" }}>
                          <a
                            href={cheapest.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-accent-700 underline"
                            style={{ fontSize: "13.5px", fontWeight: 700, lineHeight: 1.35 }}
                          >
                            {cheapest.name}
                          </a>
                          <p className="text-neutral-700" style={{ fontSize: "12.5px", margin: "var(--space-1) 0 0" }}>
                            {[cheapest.brand, cheapest.retailer].filter(Boolean).join(" · ")} ·{" "}
                            {cheapest.rating.toFixed(1)}★ ({cheapest.reviewCount.toLocaleString()})
                          </p>
                        </div>
                      </div>
                    )}

                    <CouponPanel product={couponProduct} />
                  </aside>
                )}
              </div>
            )}
          </main>
        </div>
      )}

      {screen === "signin" && (
        <SignInPage
          onGoLanding={() => goTo("landing")}
          onSignedIn={(acct) => {
            setAccount(acct);
            goTo(returnScreen);
          }}
          onContinueAsGuest={() => goTo(returnScreen)}
        />
      )}

      {screen === "extension" && (
        <div
          className="bg-neutral-200 flex flex-col items-center"
          style={{ minHeight: "100vh", padding: "clamp(16px, 3vw, 40px)", gap: "var(--space-4)" }}
        >
          <div className="w-full flex items-center flex-wrap" style={{ maxWidth: "1180px", gap: "var(--space-3)" }}>
            <button
              onClick={() => goTo("landing")}
              className="inline-flex items-center rounded-full border border-divider bg-neutral-100 hover:bg-surface transition-colors font-heading text-text cursor-pointer"
              style={{ gap: "var(--space-2)", padding: "var(--space-2) var(--space-4)", fontSize: "13.5px" }}
            >
              <ArrowLeft size={14} strokeWidth={2.75} />
              Back
            </button>
            <p className="text-neutral-700" style={{ fontSize: "14px", margin: 0 }}>
              The extension panel, in place on a retailer's product page.
            </p>
          </div>

          <div
            className="w-full bg-neutral-100 border border-divider rounded-lg shadow-lg overflow-hidden flex flex-col"
            style={{ maxWidth: "1180px", flex: "1 1 0%" }}
          >
            <div className="flex items-center bg-surface border-b border-divider" style={{ gap: "var(--space-2)", padding: "var(--space-3) var(--space-4)" }}>
              <span className="rounded-full bg-neutral-400" style={{ width: 11, height: 11 }} />
              <span className="rounded-full bg-neutral-400" style={{ width: 11, height: 11 }} />
              <span className="rounded-full bg-neutral-400" style={{ width: 11, height: 11 }} />
              <span
                className="rounded-full bg-neutral-100 flex items-center text-neutral-600 overflow-hidden whitespace-nowrap"
                style={{ marginLeft: "var(--space-2)", flex: "1 1 0%", maxWidth: "460px", height: 26, padding: "0 var(--space-3)", fontSize: "12px" }}
              >
                <Search size={12} strokeWidth={2.75} className="flex-shrink-0" style={{ marginRight: "var(--space-1)" }} />
                {results?.query || "retailer.com/product-page"}
              </span>
            </div>

            <div
              className="flex flex-wrap items-start"
              style={{ flex: "1 1 0%", gap: "clamp(20px, 3vw, 44px)", padding: "clamp(20px, 3vw, 44px)" }}
            >
              <div style={{ flex: "1 1 300px", minWidth: 0, opacity: 0.5 }}>
                <div
                  className="w-full rounded-lg border border-divider flex items-center justify-center text-neutral-600"
                  style={{
                    aspectRatio: "4 / 3",
                    background: "repeating-linear-gradient(45deg, var(--color-neutral-200) 0 8px, var(--color-neutral-100) 8px 16px)",
                    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                    fontSize: "12px",
                  }}
                >
                  retailer product photo
                </div>
                <div className="rounded-full bg-neutral-200" style={{ height: 26, width: "70%", marginTop: "var(--space-4)" }} />
                <div className="rounded-full bg-neutral-200" style={{ height: 16, width: "45%", marginTop: "var(--space-3)" }} />
                <div className="rounded-full bg-neutral-300" style={{ height: 44, width: "180px", marginTop: "var(--space-6)" }} />
              </div>

              <div style={{ flex: "0 1 386px", width: "100%", maxWidth: "386px" }}>
                <ExtensionPanel
                  targetProduct={results?.targetProduct ?? null}
                  products={allProducts}
                  onClose={() => goTo("landing")}
                  onOpenComparison={() => goTo("app")}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {compareProduct && (
        <SpecBreakdownModal
          product={compareProduct}
          targetProduct={results?.targetProduct ?? null}
          onClose={() => setCompareProduct(null)}
        />
      )}
    </>
  );
}
