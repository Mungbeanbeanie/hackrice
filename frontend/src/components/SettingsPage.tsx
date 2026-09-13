import { useRef, useState } from "react";
import { ArrowLeft, Upload, User } from "lucide-react";

import { updateProfile, type Account } from "@/api/client";

interface Props {
  account: Account;
  onBack: () => void;
  onSaved: (account: Account) => void;
}

const AVATAR_PX = 128;

// The API takes the picture as a JSON string, so a 4MB phone photo has to
// become a few KB before it leaves the browser. createImageBitmap rejects a
// non-image, which doubles as the client-side type check.
async function toAvatarDataUrl(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file);
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = AVATAR_PX;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas unavailable");
  // Centre-crop to a square first so a wide photo isn't squashed.
  const side = Math.min(bitmap.width, bitmap.height);
  ctx.drawImage(
    bitmap,
    (bitmap.width - side) / 2,
    (bitmap.height - side) / 2,
    side,
    side,
    0,
    0,
    AVATAR_PX,
    AVATAR_PX,
  );
  bitmap.close();
  return canvas.toDataURL("image/jpeg", 0.8);
}

export default function SettingsPage({ account, onBack, onSaved }: Props) {
  const [displayName, setDisplayName] = useState(account.display_name ?? "");
  const [avatar, setAvatar] = useState(account.avatar ?? "");
  const [shareData, setShareData] = useState(account.share_data);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    try {
      setAvatar(await toAvatarDataUrl(file));
      setSaved(false);
    } catch {
      setError("That file didn't look like an image we can read.");
    } finally {
      // Let the same file be picked again after a failure.
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function handleSave() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      // Sent whole rather than diffed: "" is a meaningful value here (it
      // clears the field), so there is nothing to omit.
      const updated = await updateProfile({
        display_name: displayName.trim(),
        avatar,
        share_data: shareData,
      });
      onSaved(updated);
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't save your settings");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen">
      <div
        className="mx-auto"
        style={{ maxWidth: "620px", padding: "clamp(20px, 4vw, 44px) clamp(16px, 4vw, 32px) 80px" }}
      >
        <button
          onClick={onBack}
          className="inline-flex items-center bg-transparent border-none cursor-pointer text-neutral-700 hover:text-text font-semibold"
          style={{ gap: "var(--space-2)", padding: 0, fontSize: "13.5px" }}
        >
          <ArrowLeft size={16} strokeWidth={2.75} /> Back
        </button>

        <h1 style={{ fontSize: "clamp(24px, 4vw, 32px)", margin: "var(--space-6) 0 var(--space-8)" }}>
          Settings
        </h1>

        <section style={{ marginBottom: "var(--space-8)" }}>
          <h2 style={{ fontSize: "17px", marginBottom: "var(--space-3)" }}>Profile picture</h2>
          <div className="flex items-center" style={{ gap: "var(--space-4)" }}>
            <span
              className="rounded-full bg-accent-200 text-accent-800 inline-flex items-center justify-center overflow-hidden flex-shrink-0"
              style={{ width: 72, height: 72 }}
            >
              {avatar ? (
                <img src={avatar} alt="" className="w-full h-full object-cover" />
              ) : (
                <User size={28} strokeWidth={2.75} />
              )}
            </span>
            <div className="flex flex-wrap" style={{ gap: "var(--space-2)" }}>
              <button
                onClick={() => fileRef.current?.click()}
                className="inline-flex items-center rounded-full border border-divider bg-transparent cursor-pointer font-semibold text-text hover:bg-neutral-200 transition-colors"
                style={{ gap: "var(--space-2)", padding: "var(--space-2) var(--space-3)", fontSize: "13.5px" }}
              >
                <Upload size={14} strokeWidth={2.75} /> Choose image
              </button>
              {avatar && (
                <button
                  onClick={() => {
                    setAvatar("");
                    setSaved(false);
                  }}
                  className="inline-flex items-center rounded-full border border-divider bg-transparent cursor-pointer font-semibold text-neutral-700 hover:bg-neutral-200 transition-colors"
                  style={{ padding: "var(--space-2) var(--space-3)", fontSize: "13.5px" }}
                >
                  Remove
                </button>
              )}
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                onChange={handleFile}
                className="hidden"
              />
            </div>
          </div>
          <p className="text-neutral-600" style={{ fontSize: "12.5px", marginTop: "var(--space-2)" }}>
            Resized to {AVATAR_PX}×{AVATAR_PX} in your browser before it's uploaded.
          </p>
        </section>

        <section style={{ marginBottom: "var(--space-8)" }}>
          <h2 style={{ fontSize: "17px", marginBottom: "var(--space-3)" }}>Display name</h2>
          <input
            value={displayName}
            onChange={(e) => {
              setDisplayName(e.target.value);
              setSaved(false);
            }}
            maxLength={60}
            placeholder={account.email}
            className="w-full bg-neutral-100 border border-divider rounded-md text-text"
            style={{ padding: "var(--space-3)", fontSize: "14px" }}
          />
          <p className="text-neutral-600" style={{ fontSize: "12.5px", marginTop: "var(--space-2)" }}>
            Shown instead of your email. You still sign in with {account.email}.
          </p>
        </section>

        <section style={{ marginBottom: "var(--space-8)" }}>
          <h2 style={{ fontSize: "17px", marginBottom: "var(--space-3)" }}>Data sharing</h2>
          <label className="flex cursor-pointer" style={{ gap: "var(--space-3)" }}>
            <input
              type="checkbox"
              checked={shareData}
              onChange={(e) => {
                setShareData(e.target.checked);
                setSaved(false);
              }}
              style={{ marginTop: "3px", width: 16, height: 16, accentColor: "var(--color-accent)" }}
            />
            <span style={{ fontSize: "14px" }}>
              Include my searches in aggregate analytics
              <span className="block text-neutral-600" style={{ fontSize: "12.5px", marginTop: "var(--space-1)" }}>
                Turning this off keeps future searches out of our internal totals.
                Either way they stay in your own history, and searches already
                recorded keep the setting they were made under.
              </span>
            </span>
          </label>
        </section>

        {error && (
          <p className="text-accent-700" style={{ fontSize: "14px", marginBottom: "var(--space-3)" }}>
            {error}
          </p>
        )}

        <div className="flex items-center" style={{ gap: "var(--space-3)" }}>
          <button
            onClick={handleSave}
            disabled={busy}
            className="inline-flex items-center rounded-full bg-accent text-neutral-100 border-none cursor-pointer font-semibold hover:bg-accent-600 transition-colors disabled:opacity-60"
            style={{ padding: "var(--space-3) var(--space-6)", fontSize: "14px" }}
          >
            {busy ? "Saving…" : "Save changes"}
          </button>
          {saved && !busy && (
            <span className="text-accent-2-700 font-semibold" style={{ fontSize: "13.5px" }}>
              Saved
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
