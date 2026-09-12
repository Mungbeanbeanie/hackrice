import { useState } from "react";

import { requestSignInCode, verifySignInCode } from "@/api/client";
import HoneyDrop from "@/components/HoneyDrop";
import TermsLink from "@/components/TermsLink";

interface Props {
  onGoLanding: () => void;
  onSignedIn: () => void;
}

type Step = "email" | "code";

// NOTE — deviation from the design handoff: the mockup's copy ("Email me a
// sign-in link" / "We send a link that signs you in for 30 days") assumes a
// magic-link flow, but the backend (Phase 8, routes/auth.py) implements a
// verification CODE: POST /request-code emails a code, POST /verify checks
// email+code. There is no link-click step to land on. Copy adjusted to
// "code" and a second step added for entering it — not present in the
// original mockup, which only modeled a single email step.
export default function SignInPage({ onGoLanding, onSignedIn }: Props) {
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleRequestCode(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || busy) return;
    setBusy(true);
    setError("");
    try {
      await requestSignInCode(email.trim());
      setStep("code");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't send the code");
    } finally {
      setBusy(false);
    }
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    if (!code.trim() || busy) return;
    setBusy(true);
    setError("");
    try {
      await verifySignInCode(email.trim(), code.trim());
      onSignedIn();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid or expired code");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid" style={{ minHeight: "100vh", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" }}>
      <div className="flex items-center justify-center" style={{ padding: "clamp(32px, 6vw, 72px)" }}>
        <div className="w-full animate-rise-in" style={{ maxWidth: "380px" }}>
          <button
            onClick={onGoLanding}
            className="flex items-center bg-transparent border-none cursor-pointer"
            style={{ gap: "var(--space-2)", padding: 0, marginBottom: "var(--space-8)" }}
          >
            <div style={{ width: 26, height: 30 }} className="flex-shrink-0">
              <HoneyDrop size={26} />
            </div>
            <span style={{ fontFamily: "var(--font-heading)", fontSize: "21px", color: "var(--color-accent-700)" }}>
              nectarly
            </span>
          </button>

          <h1 style={{ fontSize: "clamp(30px, 3.6vw, 38px)", lineHeight: 1.12, margin: "0 0 var(--space-2)" }}>
            Keep what you found.
          </h1>
          <p className="text-neutral-800" style={{ margin: "0 0 var(--space-6)" }}>
            Sign in to save comparisons, track price moves, and pick up a search where you left it.
          </p>

          {step === "email" ? (
            <form onSubmit={handleRequestCode}>
              <div style={{ marginBottom: "var(--space-4)" }}>
                <label
                  htmlFor="email"
                  className="block text-neutral-800 font-semibold"
                  style={{ fontSize: "12.5px", marginBottom: "var(--space-1)" }}
                >
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  disabled={busy}
                  className="w-full rounded-full border border-divider bg-neutral-100 text-text outline-none"
                  style={{ padding: "var(--space-3) var(--space-4)", fontSize: "15px" }}
                />
              </div>
              {/* `required` is the whole gate: the browser blocks the submit
                  event outright, so handleRequestCode never fires. Acceptance
                  is not sent to or stored by the backend. */}
              <div className="flex items-start" style={{ gap: "var(--space-2)", marginBottom: "var(--space-4)" }}>
                <input
                  id="terms"
                  type="checkbox"
                  required
                  disabled={busy}
                  className="cursor-pointer flex-shrink-0"
                  style={{ marginTop: "3px", accentColor: "var(--color-accent)" }}
                />
                <label
                  htmlFor="terms"
                  className="text-neutral-800 cursor-pointer"
                  style={{ fontSize: "12.5px", lineHeight: 1.4 }}
                >
                  I agree to the <TermsLink /> and to nectarly storing my email address and the searches I
                  run.
                </label>
              </div>
              <button
                type="submit"
                disabled={!email.trim() || busy}
                className="w-full rounded-full bg-accent text-bg font-heading hover:bg-accent-600 transition-colors disabled:opacity-40 cursor-pointer"
                style={{ padding: "var(--space-3)", fontSize: "15px" }}
              >
                {busy ? "Sending…" : "Email me a sign-in code"}
              </button>
              <p className="text-center text-neutral-700" style={{ fontSize: "12.5px", margin: "var(--space-3) 0 0" }}>
                No password. We'll email you a one-time code.
              </p>
            </form>
          ) : (
            <form onSubmit={handleVerify}>
              <div style={{ marginBottom: "var(--space-4)" }}>
                <label
                  htmlFor="code"
                  className="block text-neutral-800 font-semibold"
                  style={{ fontSize: "12.5px", marginBottom: "var(--space-1)" }}
                >
                  Code sent to {email}
                </label>
                <input
                  id="code"
                  type="text"
                  inputMode="numeric"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="123456"
                  disabled={busy}
                  className="w-full rounded-full border border-divider bg-neutral-100 text-text outline-none"
                  style={{ padding: "var(--space-3) var(--space-4)", fontSize: "15px" }}
                />
              </div>
              <button
                type="submit"
                disabled={!code.trim() || busy}
                className="w-full rounded-full bg-accent text-bg font-heading hover:bg-accent-600 transition-colors disabled:opacity-40 cursor-pointer"
                style={{ padding: "var(--space-3)", fontSize: "15px" }}
              >
                {busy ? "Verifying…" : "Verify code"}
              </button>
              <button
                type="button"
                onClick={() => setStep("email")}
                className="w-full text-center text-neutral-700 bg-transparent border-none cursor-pointer"
                style={{ fontSize: "12.5px", margin: "var(--space-3) 0 0" }}
              >
                Use a different email
              </button>
            </form>
          )}

          {error && (
            <p className="text-center" style={{ fontSize: "12.5px", color: "var(--color-accent-800)", marginTop: "var(--space-3)" }}>
              {error}
            </p>
          )}

          <div className="flex items-center" style={{ gap: "var(--space-3)", margin: "var(--space-6) 0" }}>
            <span className="flex-1 bg-divider" style={{ height: 1 }} />
            <span className="text-neutral-600" style={{ fontSize: "12px" }}>
              or
            </span>
            <span className="flex-1 bg-divider" style={{ height: 1 }} />
          </div>
          <button
            onClick={onSignedIn}
            className="w-full rounded-full border border-divider bg-transparent font-heading text-text hover:bg-neutral-200 transition-colors cursor-pointer"
            style={{ padding: "var(--space-3)", fontSize: "14.5px" }}
          >
            Continue without an account
          </button>
        </div>
      </div>

      <div className="bg-surface relative overflow-hidden flex items-center justify-center" style={{ padding: "clamp(32px, 6vw, 72px)" }}>
        <div
          className="absolute rounded-full bg-accent-200"
          style={{ width: 430, height: 430, top: -90, right: -120 }}
        />
        <div
          className="absolute rounded-full bg-accent-2-200"
          style={{ width: 220, height: 220, bottom: -60, left: -50 }}
        />
        <blockquote className="relative" style={{ margin: 0, maxWidth: "400px" }}>
          <p style={{ fontFamily: "var(--font-heading)", fontSize: "clamp(24px, 2.8vw, 31px)", lineHeight: 1.25, margin: "0 0 var(--space-4)" }}>
            "Pay for the product, not the brand."
          </p>
          <footer className="text-neutral-700" style={{ fontSize: "14px" }}>
            The whole idea, in six words.
          </footer>
        </blockquote>
      </div>
    </div>
  );
}
