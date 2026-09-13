import { useRef, useState } from "react";
import { LogOut, Settings, User } from "lucide-react";

import { signOut, type Account } from "@/api/client";

interface Props {
  account: Account | null;
  onSignIn: () => void;
  onProfile: () => void;
  onSettings: () => void;
  onSignedOut: () => void;
}

// ponytail: a native <dialog> rather than a hand-rolled popover, same call as
// TermsLink.tsx — showModal() gives Escape-to-close, a focus trap and an
// outside-click target for free. The backdrop is left transparent because this
// is a menu, not a modal: it should not dim the page behind it.
export default function AccountMenu({
  account,
  onSignIn,
  onProfile,
  onSettings,
  onSignedOut,
}: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);

  // Signed out, the pill is a plain button straight to sign-in. Signed in, it
  // opens the menu — the old behaviour sent a signed-in user back to the
  // sign-in form, which is the bug this component exists to fix.
  function handleTrigger() {
    if (!account) {
      onSignIn();
      return;
    }
    ref.current?.showModal();
  }

  function pick(action: () => void) {
    ref.current?.close();
    action();
  }

  async function handleSignOut() {
    if (busy) return;
    setBusy(true);
    try {
      await signOut();
    } finally {
      // A failed request still clears local state: leaving someone looking
      // signed in when they asked not to be is the worse outcome.
      setBusy(false);
      ref.current?.close();
      onSignedOut();
    }
  }

  const label = account ? (account.display_name || account.email) : "Sign in";

  return (
    <>
      <button
        onClick={handleTrigger}
        aria-haspopup={account ? "menu" : undefined}
        className="inline-flex items-center rounded-full border border-divider bg-transparent font-semibold text-text hover:bg-neutral-200 transition-colors cursor-pointer flex-shrink-0"
        style={{
          gap: "var(--space-2)",
          padding: "var(--space-1) var(--space-2) var(--space-1) var(--space-3)",
          fontSize: "13.5px",
          maxWidth: "220px",
        }}
      >
        <span className="truncate">{label}</span>
        <span
          className="rounded-full bg-accent-200 text-accent-800 inline-flex items-center justify-center overflow-hidden flex-shrink-0"
          style={{ width: 26, height: 26 }}
        >
          {account?.avatar ? (
            <img src={account.avatar} alt="" className="w-full h-full object-cover" />
          ) : (
            <User size={14} strokeWidth={2.75} />
          )}
        </span>
      </button>

      <dialog
        ref={ref}
        onClick={(e) => e.target === e.currentTarget && ref.current?.close()}
        className="open:block border-none bg-transparent backdrop:bg-transparent"
        // Replaces <dialog>'s default centring so the panel hangs under the
        // header pill. Identical in both headers, so no anchor prop.
        style={{ margin: "54px 16px 0 auto", padding: 0, maxWidth: "min(240px, calc(100vw - 32px))" }}
      >
        <div
          role="menu"
          className="bg-bg border border-divider rounded-md shadow-lg overflow-hidden animate-soft-in"
          style={{ minWidth: "200px" }}
        >
          {account && (
            <div
              className="border-b border-divider"
              style={{ padding: "var(--space-3)" }}
            >
              <div className="truncate font-semibold" style={{ fontSize: "13.5px" }}>
                {account.display_name || "No name set"}
              </div>
              <div
                className="truncate text-neutral-600"
                style={{ fontSize: "12.5px" }}
              >
                {account.email}
              </div>
            </div>
          )}
          <MenuItem icon={<User size={15} strokeWidth={2.75} />} onClick={() => pick(onProfile)}>
            Profile
          </MenuItem>
          <MenuItem
            icon={<Settings size={15} strokeWidth={2.75} />}
            onClick={() => pick(onSettings)}
          >
            Settings
          </MenuItem>
          <MenuItem
            icon={<LogOut size={15} strokeWidth={2.75} />}
            onClick={handleSignOut}
          >
            {busy ? "Signing out…" : "Log out"}
          </MenuItem>
        </div>
      </dialog>
    </>
  );
}

function MenuItem({
  icon,
  onClick,
  children,
}: {
  icon: React.ReactNode;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      role="menuitem"
      onClick={onClick}
      className="w-full flex items-center bg-transparent border-none cursor-pointer text-text font-semibold hover:bg-neutral-200 transition-colors"
      style={{ gap: "var(--space-2)", padding: "var(--space-3)", fontSize: "13.5px" }}
    >
      {icon}
      {children}
    </button>
  );
}
