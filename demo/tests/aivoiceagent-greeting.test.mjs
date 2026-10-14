import assert from "node:assert/strict";
import test from "node:test";

import { shouldSendStartupGreeting } from "../s2s-realtime-client.js";

const greeting = "Start the conversation now with a brief, spontaneous greeting in character.";

test("normal standalone demo greeting is unchanged", () => {
  assert.equal(
    shouldSendStartupGreeting(
      { startupGreeting: greeting },
      "ws://127.0.0.1:8765/v1/realtime",
    ),
    true,
  );
});

test("Java-managed H5 config always disables fake user greeting", () => {
  assert.equal(
    shouldSendStartupGreeting(
      { startupGreeting: greeting, aivoiceagentManaged: true },
      "http://127.0.0.1:7860/api/calls",
    ),
    false,
  );
});

test("direct Live URL disables fake greeting even if config was missed", () => {
  assert.equal(
    shouldSendStartupGreeting(
      { startupGreeting: greeting },
      "ws://127.0.0.1:8765/v1/realtime?aivoiceagent_token=synthetic",
    ),
    false,
  );
});

test("empty greeting never triggers a response", () => {
  assert.equal(
    shouldSendStartupGreeting(
      { startupGreeting: "" },
      "ws://127.0.0.1:8765/v1/realtime",
    ),
    false,
  );
});
