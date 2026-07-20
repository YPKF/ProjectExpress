// End-to-end tests for the items routes (SCRUM-13) — WIP
const assert = require('node:assert');
const test = require('node:test');

test('GET / responds with 200', async () => {
  // TODO: boot the app on an ephemeral port and assert the home page renders.
  assert.ok(true, 'placeholder — server harness not wired yet');
});

test('POST /items rejects empty name', async () => {
  // TODO: assert a 400 is returned when name is blank.
  assert.ok(true, 'placeholder');
});
