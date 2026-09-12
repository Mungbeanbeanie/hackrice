import { useRef } from "react";
import { X } from "lucide-react";

const LAST_UPDATED = "12 September 2026";

const SECTIONS: { title: string; body: string }[] = [
  {
    title: "What we store",
    body: "Two things: the email address you sign up with, and the searches you run — the link, product name, or description you typed, plus the alternatives we found for it.",
  },
  {
    title: "Why we store it",
    body: "Your email is how we sign you in; there is no password. Your searches are kept so a comparison can be re-opened later and so a repeated search doesn't re-bill the retail data APIs we pay per call.",
  },
  {
    title: "Who else sees it",
    body: "We don't sell your data and we don't hand it to advertisers. Running a search does send your query text to the product-search and embedding APIs we depend on — that is the only place it goes.",
  },
  {
    title: "Getting it deleted",
    body: "Ask, and we'll delete your account and its search history. Use the feedback link at the bottom of the home page; there is no automated delete button yet.",
  },
  {
    title: "About the prices we show",
    body: "Prices, ratings, and specs come from third-party retailers and can be stale, incomplete, or wrong. We don't sell anything, we aren't part of any purchase you make, and we can't stand behind a listing we didn't write.",
  },
  {
    title: "Changes",
    body: "These terms can change. The date above is the version you're reading. Continuing to use nectarly after a change means you accept the newer version.",
  },
];

// ponytail: a native <dialog> instead of the hand-rolled overlay in
// SpecBreakdownModal.tsx — showModal() gives Escape-to-close, a focus trap, and
// background inertness for free. Self-contained on purpose: no state in App.tsx,
// so it can be dropped anywhere a "Terms" link belongs.
export default function TermsLink() {
  const ref = useRef<HTMLDialogElement>(null);

  return (
    <>
      <button
        type="button"
        // preventDefault: this renders inside SignInPage's <label>, and a label
        // click otherwise forwards through and toggles the checkbox.
        onClick={(e) => {
          e.preventDefault();
          ref.current?.showModal();
        }}
        className="underline bg-transparent border-none cursor-pointer"
        style={{ font: "inherit", color: "inherit", padding: 0 }}
      >
        Terms
      </button>

      <dialog
        ref={ref}
        onClick={(e) => e.target === e.currentTarget && ref.current?.close()}
        className="open:flex flex-col border-none m-auto bg-bg text-text rounded-lg shadow-lg overflow-hidden backdrop:bg-[rgba(46,43,37,0.55)] backdrop:backdrop-blur-[5px]"
        style={{ padding: 0, width: "min(560px, calc(100vw - 32px))", maxHeight: "85vh" }}
      >
        <div
          className="flex items-start border-b border-divider flex-shrink-0"
          style={{ gap: "var(--space-4)", padding: "clamp(20px, 2.6vw, 28px)" }}
        >
          <div className="flex-1 min-w-0">
            <p
              className="uppercase text-neutral-700 font-bold"
              style={{ fontSize: "11px", letterSpacing: "0.08em", margin: "0 0 var(--space-1)" }}
            >
              Last updated {LAST_UPDATED}
            </p>
            <h2 style={{ fontSize: "clamp(21px, 2.4vw, 26px)", lineHeight: 1.2, margin: 0 }}>
              Terms &amp; what we keep
            </h2>
          </div>
          <button
            type="button"
            onClick={() => ref.current?.close()}
            className="w-9 h-9 flex-shrink-0 rounded-full bg-surface hover:bg-neutral-300 transition-colors flex items-center justify-center cursor-pointer border-none"
          >
            <X size={16} strokeWidth={2.75} />
          </button>
        </div>

        <div
          className="overflow-y-auto flex-1"
          style={{ padding: "clamp(16px, 2.2vw, 24px) clamp(20px, 2.6vw, 28px)" }}
        >
          {SECTIONS.map((s) => (
            <div key={s.title} style={{ marginBottom: "var(--space-6)" }}>
              <p style={{ fontSize: "14.5px", fontWeight: 700, margin: "0 0 var(--space-1)" }}>{s.title}</p>
              <p className="text-neutral-800" style={{ fontSize: "13.5px", lineHeight: 1.5, margin: 0 }}>
                {s.body}
              </p>
            </div>
          ))}
          <p className="text-neutral-700" style={{ fontSize: "12.5px", lineHeight: 1.5, margin: 0 }}>
            nectarly is a student project, offered as-is with no warranty. Don't use it for anything where a
            wrong price would actually hurt.
          </p>
        </div>
      </dialog>
    </>
  );
}
