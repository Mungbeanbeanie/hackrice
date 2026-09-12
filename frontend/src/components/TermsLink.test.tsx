import { expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import SignInPage from "@/components/SignInPage";

// jsdom has no HTMLDialogElement — stub just enough of showModal to observe it.
const showModal = vi.fn();
Object.defineProperty(HTMLElement.prototype, "showModal", { value: showModal, writable: true });

test("the terms checkbox gates the form, and opening the terms does not tick it", () => {
  render(<SignInPage onGoLanding={() => {}} onSignedIn={() => {}} onContinueAsGuest={() => {}} />);
  const box = screen.getByRole("checkbox") as HTMLInputElement;

  expect(box.required).toBe(true);

  // The link sits inside the checkbox's <label>; without preventDefault the
  // label forwards the click through and ticking the box becomes an accident.
  screen.getByRole("button", { name: "Terms" }).click();
  expect(showModal).toHaveBeenCalled();
  expect(box.checked).toBe(false);
});
