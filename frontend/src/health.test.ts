import { expect, test } from "vitest";

import { health } from "./health.js";

test("health", () => {
  expect(health()).toEqual({ status: "ok" });
});
