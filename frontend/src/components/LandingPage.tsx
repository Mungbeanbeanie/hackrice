import { useState } from "react";
import { ArrowDown, ArrowRight, Check } from "lucide-react";

import HoneyDrop from "@/components/HoneyDrop";
import SearchBar from "@/components/SearchBar";
import TermsLink from "@/components/TermsLink";

interface Props {
  query: string;
  onQueryChange: (value: string) => void;
  onSearch: (query: string) => void;
  onGoSignin: () => void;
  onGoExtension: () => void;
}

const EXAMPLES = ["purple harmony pillow", "sony wh-1000xm5", "dyson v15 detect"];

const STEPS = [
  {
    n: "1",
    title: "Match on specs, not names",
    body: "Two products doing the same job rarely list the same attributes. We line them up spec by spec so they can be compared at all.",
  },
  {
    n: "2",
    title: "Filter out the junk",
    body: "A 5.0 from two reviews is not a 5.0. Ratings only count once there are enough of them to mean something.",
  },
  {
    n: "3",
    title: "Rank by value, not discount",
    body: "What you get weighed against what you pay. The cheapest thing rarely wins. The overpriced brand never does.",
  },
];

const EXT_POINTS = [
  "Reads the page you're already on — no copying links",
  "Shows the equivalent before you reach the cart",
  "Nothing leaves your browser until you ask for a comparison",
];

const STRIPE = "repeating-linear-gradient(45deg, var(--color-neutral-200) 0 5px, var(--color-neutral-100) 5px 10px)";
const STRIPE_SAGE = "repeating-linear-gradient(45deg, var(--color-accent-2-200) 0 5px, var(--color-accent-2-100) 5px 10px)";

// The two hero mockup thumbnails, served from frontend/public/. The onError
// below falls back to the striped placeholder that used to be hardcoded here,
// so a renamed or missing file degrades instead of showing a broken image.
function ExampleThumb({
  src,
  alt,
  fallback,
  border,
}: {
  src: string;
  alt: string;
  fallback: string;
  border: string;
}) {
  const [failed, setFailed] = useState(false);
  return (
    <div
      className={`rounded-md flex-shrink-0 border ${border} overflow-hidden`}
      style={{ width: 52, height: 52, background: failed ? fallback : "#fff" }}
    >
      {!failed && (
        <img
          src={src}
          alt={alt}
          className="w-full h-full object-contain"
          onError={() => setFailed(true)}
        />
      )}
    </div>
  );
}

// ponytail: a Google Form stands in for a real feedback endpoint because the
// repo has no working datastore yet — an endpoint would mean provisioning one
// first. Replace with POST /api/feedback once there is somewhere to put it.
const FEEDBACK_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf0WtkQRAguepMWqBOKYo-e3HQR2Ed6yip4oglBy49RQEGAkg/viewform?usp=publish-editor";

export default function LandingPage({ query, onQueryChange, onSearch, onGoSignin, onGoExtension }: Props) {
  return (
    <div>
      {/* Header */}
      <header
        className="sticky top-0 z-20 bg-bg border-b border-divider"
        style={{ backdropFilter: "blur(14px)" }}
      >
        <div
          className="mx-auto flex items-center"
          style={{ maxWidth: "1160px", padding: "14px clamp(20px, 4vw, 48px)", gap: "var(--space-4)" }}
        >
          <div className="flex items-center mr-auto" style={{ gap: "var(--space-2)" }}>
            <div className="animate-bob flex-shrink-0" style={{ width: 30, height: 35 }}>
              <HoneyDrop size={30} />
            </div>
            <span style={{ fontFamily: "var(--font-heading)", fontSize: "23px", color: "var(--color-accent-700)" }}>
              nectarly
            </span>
          </div>
          <nav className="flex items-center" style={{ gap: "var(--space-1)" }}>
            <a
              href="#how"
              className="inline-flex items-center rounded-full font-semibold no-underline text-text hover:bg-neutral-200 transition-colors"
              style={{ padding: "var(--space-2) var(--space-3)", fontSize: "14px" }}
            >
              How it works
            </a>
            <a
              href="#extension"
              className="inline-flex items-center rounded-full font-semibold no-underline text-text hover:bg-neutral-200 transition-colors"
              style={{ padding: "var(--space-2) var(--space-3)", fontSize: "14px" }}
            >
              Extension
            </a>
            <button
              onClick={onGoSignin}
              className="inline-flex items-center rounded-full border border-divider bg-transparent font-heading text-text hover:bg-neutral-200 transition-colors cursor-pointer"
              style={{ padding: "var(--space-2) var(--space-3)", fontSize: "14px" }}
            >
              Sign in
            </button>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section
        className="mx-auto grid items-start"
        style={{
          maxWidth: "1160px",
          padding: "clamp(40px, 7vw, 88px) clamp(20px, 4vw, 48px) clamp(32px, 5vw, 64px)",
          gridTemplateColumns: "repeat(auto-fit, minmax(440px, 1fr))",
          gap: "clamp(36px, 5vw, 64px)",
        }}
      >
        <div className="animate-rise-in">
          <span
            className="inline-flex items-center rounded-full bg-accent-2-100 text-accent-2-700 border border-accent-2-200 font-bold"
            style={{ gap: "var(--space-1)", padding: "var(--space-1) var(--space-3)", fontSize: "13px" }}
          >
            <Check size={13} strokeWidth={2.75} />
            Not another coupon extension
          </span>
          <h1
            style={{
              fontSize: "clamp(36px, 4.6vw, 62px)",
              lineHeight: 1.05,
              letterSpacing: "-0.02em",
              marginTop: "var(--space-4)",
            }}
          >
            Pay for the product,
            <br />
            not the brand.
          </h1>
          <p
            className="text-neutral-800"
            style={{ fontSize: "clamp(16px, 1.6vw, 19px)", lineHeight: 1.55, maxWidth: "30em", marginTop: "var(--space-4)" }}
          >
            Paste any product link. Nectarly finds the versions that match it on specs, filters out the junk, and
            ranks what's left by what you actually get per dollar.
          </p>

          <div style={{ marginTop: "var(--space-6)" }}>
            <SearchBar variant="hero" value={query} onChange={onQueryChange} loading={false} onSearch={onSearch} />
          </div>
          <div className="flex items-center flex-wrap" style={{ gap: "var(--space-2)", marginTop: "var(--space-3)" }}>
            <span className="text-neutral-700" style={{ fontSize: "13px" }}>
              Try
            </span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                onClick={() => {
                  onQueryChange(ex);
                  onSearch(ex);
                }}
                className="rounded-full border border-divider bg-transparent font-semibold text-accent-700 hover:bg-accent-100 hover:border-accent-300 transition-colors cursor-pointer"
                style={{ padding: "var(--space-1) var(--space-3)", fontSize: "13px" }}
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        <div
          className="relative flex items-start justify-center animate-rise-in"
          style={{ paddingTop: "48.5px" }}
        >
          <div
            className="absolute rounded-full bg-accent-200"
            style={{ top: "50%", left: "50%", transform: "translate(-50%, -50%)", width: "min(400px, 92%)", aspectRatio: "1" }}
          />
          <div
            className="absolute rounded-full bg-accent-2-200"
            style={{ top: "4%", right: "6%", width: "120px", height: "120px" }}
          />
          <div className="relative flex flex-col" style={{ width: "min(392px, 100%)", gap: "var(--space-3)" }}>
            <div
              className="bg-neutral-100 border border-divider rounded-lg shadow-md"
              style={{ padding: "var(--space-4)", transform: "rotate(-1.4deg)" }}
            >
              <p
                className="uppercase text-neutral-700 font-bold"
                style={{ fontSize: "11px", letterSpacing: "0.08em", margin: "0 0 var(--space-2)" }}
              >
                What you were buying
              </p>
              <div className="flex items-center" style={{ gap: "var(--space-3)" }}>
                <ExampleThumb
                  src="/purple%20harmony%20pillow.webp"
                  alt="Purple Harmony Pillow"
                  fallback={STRIPE}
                  border="border-divider"
                />
                <div className="flex-1 min-w-0">
                  <p style={{ fontSize: "14px", fontWeight: 700, lineHeight: 1.3 }}>Purple Harmony Pillow</p>
                  <p className="text-neutral-700" style={{ fontSize: "13px", marginTop: "2px" }}>
                    Talalay latex · 6.5 in loft
                  </p>
                </div>
                <p style={{ fontFamily: "var(--font-heading)", fontSize: "24px", lineHeight: 1 }}>$159</p>
              </div>
            </div>

            <div className="flex items-center" style={{ gap: "var(--space-2)", paddingLeft: "var(--space-6)" }}>
              <ArrowDown size={18} strokeWidth={2.75} color="var(--color-accent)" />
              <span className="text-accent-700 font-bold" style={{ fontSize: "13px" }}>
                96% spec match found
              </span>
            </div>

            <div
              className="bg-accent-2-100 border border-accent-2-300 rounded-lg shadow-lg"
              style={{ padding: "var(--space-4)", transform: "rotate(1.1deg)" }}
            >
              <p
                className="uppercase text-accent-2-700 font-bold"
                style={{ fontSize: "11px", letterSpacing: "0.08em", margin: "0 0 var(--space-2)" }}
              >
                What you'll buy instead
              </p>
              <div className="flex items-center" style={{ gap: "var(--space-3)" }}>
                <ExampleThumb
                  src="/gel%20memory%20foam%20contour.webp"
                  alt="Gel Memory Foam Contour pillow"
                  fallback={STRIPE_SAGE}
                  border="border-accent-2-300"
                />
                <div className="flex-1 min-w-0">
                  <p style={{ fontSize: "14px", fontWeight: 700, lineHeight: 1.3 }}>Gel Memory Foam Contour</p>
                  <p className="text-accent-2-700" style={{ fontSize: "13px", marginTop: "2px" }}>
                    Same loft · same cover · 4.4★ (8,912)
                  </p>
                </div>
                <p className="text-accent-2-700" style={{ fontFamily: "var(--font-heading)", fontSize: "24px", lineHeight: 1 }}>
                  $42
                </p>
              </div>
              <div
                className="flex items-baseline justify-between border-accent-2-300"
                style={{ marginTop: "var(--space-3)", paddingTop: "var(--space-3)", borderTopWidth: 1, borderTopStyle: "solid", gap: "var(--space-2)" }}
              >
                <span className="text-accent-2-700 font-semibold" style={{ fontSize: "13px" }}>
                  You keep
                </span>
                <span className="text-accent-2-700" style={{ fontFamily: "var(--font-heading)", fontSize: "27px", lineHeight: 1 }}>
                  $117.00
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Three things */}
      <section
        id="how"
        className="mx-auto border-t border-divider"
        style={{ maxWidth: "1160px", padding: "clamp(36px, 5vw, 72px) clamp(20px, 4vw, 48px)" }}
      >
        <h2 style={{ fontSize: "clamp(28px, 3.6vw, 40px)", lineHeight: 1.1, margin: "0 0 var(--space-2)", maxWidth: "14em" }}>
          Three things every other shopping tool skips.
        </h2>
        <p className="text-neutral-800" style={{ maxWidth: "44em", margin: "0 0 clamp(28px, 3.5vw, 44px)" }}>
          Coupon extensions optimise the last 5% of a price you already agreed to. Nectarly questions the price.
        </p>
        <div
          className="grid"
          style={{ gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "clamp(16px, 2vw, 26px)" }}
        >
          {STEPS.map((s) => (
            <div
              key={s.n}
              className="bg-neutral-100 border border-divider rounded-lg"
              style={{ padding: "clamp(20px, 2.4vw, 28px)" }}
            >
              <span
                className="inline-flex items-center justify-center rounded-full bg-accent-200 text-accent-800"
                style={{ width: 38, height: 38, fontFamily: "var(--font-heading)", fontSize: "17px" }}
              >
                {s.n}
              </span>
              <h3 style={{ fontSize: "21px", lineHeight: 1.2, margin: "var(--space-4) 0 var(--space-2)" }}>{s.title}</h3>
              <p className="text-neutral-800" style={{ fontSize: "14.5px", margin: 0 }}>
                {s.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Extension teaser */}
      <section
        id="extension"
        className="mx-auto grid items-center border-t border-divider"
        style={{
          maxWidth: "1160px",
          padding: "clamp(36px, 5vw, 72px) clamp(20px, 4vw, 48px)",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "clamp(32px, 4vw, 56px)",
        }}
      >
        <div>
          <h2 style={{ fontSize: "clamp(28px, 3.6vw, 40px)", lineHeight: 1.1, margin: "0 0 var(--space-3)", maxWidth: "12em" }}>
            It comes with you.
          </h2>
          <p className="text-neutral-800" style={{ maxWidth: "34em", margin: "0 0 var(--space-6)" }}>
            The extension wakes up on any product page, reads the listing, and puts the equivalents one click away —
            before you've added anything to a cart.
          </p>
          <div className="flex flex-col" style={{ gap: "var(--space-3)", marginBottom: "var(--space-6)" }}>
            {EXT_POINTS.map((pt) => (
              <div key={pt} className="flex items-start" style={{ gap: "var(--space-3)" }}>
                <Check
                  size={18}
                  strokeWidth={2.75}
                  color="var(--color-accent-2-600)"
                  className="flex-shrink-0"
                  style={{ marginTop: "var(--space-1)" }}
                />
                <span className="text-neutral-800" style={{ fontSize: "14.5px" }}>
                  {pt}
                </span>
              </div>
            ))}
          </div>
          <button
            onClick={onGoExtension}
            className="inline-flex items-center rounded-full bg-accent text-bg font-heading hover:bg-accent-600 transition-colors cursor-pointer"
            style={{ gap: "var(--space-2)", padding: "var(--space-3) var(--space-6)", fontSize: "15px" }}
          >
            See the panel
            <ArrowRight size={16} strokeWidth={2.75} />
          </button>
        </div>
        <div className="flex justify-center">
          <div
            className="w-full bg-surface border border-divider rounded-lg shadow-lg"
            style={{ maxWidth: "390px", padding: "var(--space-3)" }}
          >
            <div className="flex items-center" style={{ gap: "var(--space-1)", padding: "0 var(--space-1) var(--space-3)" }}>
              <span className="rounded-full bg-neutral-400" style={{ width: 10, height: 10 }} />
              <span className="rounded-full bg-neutral-400" style={{ width: 10, height: 10 }} />
              <span className="rounded-full bg-neutral-400" style={{ width: 10, height: 10 }} />
              <span
                className="flex-1 rounded-full bg-neutral-200 flex items-center text-neutral-600 overflow-hidden whitespace-nowrap"
                style={{ marginLeft: "var(--space-2)", height: 20, padding: "0 var(--space-2)", fontSize: "10.5px" }}
              >
                purple.com/pillows/harmony
              </span>
            </div>
            <div className="bg-neutral-100 rounded-md" style={{ padding: "var(--space-4)" }}>
              <div className="flex items-center" style={{ gap: "var(--space-2)", marginBottom: "var(--space-3)" }}>
                <div style={{ width: 20, height: 23 }} className="flex-shrink-0">
                  <HoneyDrop size={20} />
                </div>
                <span style={{ fontFamily: "var(--font-heading)", fontSize: "15px", color: "var(--color-accent-700)" }} className="mr-auto">
                  nectarly
                </span>
                <span
                  className="font-bold rounded-full bg-accent-2-100 text-accent-2-700"
                  style={{ fontSize: "11px", padding: "var(--space-1) var(--space-2)" }}
                >
                  4 found
                </span>
              </div>
              <p
                className="uppercase text-neutral-700 font-bold"
                style={{ fontSize: "11px", letterSpacing: "0.07em", margin: "0 0 var(--space-1)" }}
              >
                Best equivalent
              </p>
              <p style={{ fontSize: "14px", fontWeight: 700, lineHeight: 1.3, margin: 0 }}>Gel Memory Foam Contour Pillow</p>
              <div className="flex items-baseline" style={{ gap: "var(--space-2)", marginTop: "var(--space-2)" }}>
                <span className="text-accent-2-700" style={{ fontFamily: "var(--font-heading)", fontSize: "28px", lineHeight: 1 }}>
                  $42
                </span>
                <span className="text-neutral-700 line-through" style={{ fontSize: "13px" }}>
                  $159
                </span>
                <span className="text-accent-2-700 font-bold ml-auto" style={{ fontSize: "12px" }}>
                  96% match
                </span>
              </div>
              <div className="rounded-full bg-accent-2-200 overflow-hidden" style={{ height: 8, marginTop: "var(--space-3)" }}>
                <div className="h-full rounded-full bg-accent" style={{ width: "26%" }} />
              </div>
              <p className="text-neutral-700" style={{ fontSize: "12px", margin: "var(--space-1) 0 0" }}>
                You'd pay 26% of the original
              </p>
              <button
                onClick={onGoExtension}
                className="w-full rounded-full bg-accent text-bg font-heading hover:bg-accent-600 transition-colors cursor-pointer"
                style={{ marginTop: "var(--space-3)", padding: "var(--space-2)", fontSize: "14px" }}
              >
                Compare all 4
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-divider">
        <div
          className="mx-auto flex flex-wrap items-center"
          style={{ maxWidth: "1160px", padding: "32px clamp(20px, 4vw, 48px)", gap: "var(--space-4)" }}
        >
          <div className="flex items-center mr-auto" style={{ gap: "var(--space-2)" }}>
            <div style={{ width: 20, height: 23 }} className="flex-shrink-0">
              <HoneyDrop size={20} />
            </div>
            <span style={{ fontFamily: "var(--font-heading)", fontSize: "16px", color: "var(--color-accent-700)" }}>
              nectarly
            </span>
            <span className="text-neutral-700" style={{ fontSize: "13px" }}>
              find sweeter deals
            </span>
          </div>
          <a
            href={FEEDBACK_FORM_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold no-underline text-text"
            style={{ fontSize: "13.5px" }}
          >
            Send feedback
          </a>
          <span className="text-neutral-600" style={{ fontSize: "12.5px" }}>
            <TermsLink />
          </span>
        </div>
      </footer>
    </div>
  );
}
