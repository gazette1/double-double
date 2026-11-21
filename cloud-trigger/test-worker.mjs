// Local tests for worker.js with fetch replaced: node test-worker.mjs (no network, no dependencies).
import assert from "node:assert/strict";
import worker from "./worker.js";

const env = {
  GITHUB_REPO: "gazette1/double-double",
  GITHUB_WORKFLOW: "daily_dd_discord.yml",
  GITHUB_REF: "main",
  GITHUB_TOKEN: "test-token",
  RETRY_WAIT_MS: "1",
};
const realFetch = globalThis.fetch;
const realLog = console.log;

async function run(responses) {
  const calls = [];
  let i = 0;
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init });
    const next = responses[Math.min(i++, responses.length - 1)];
    if (next instanceof Error) throw next;
    return new Response(next.status === 204 ? null : (next.body ?? ""), { status: next.status });
  };
  console.log = () => {};
  let error = null;
  try {
    await worker.scheduled({ cron: "55 19 * * *" }, env);
  } catch (e) {
    error = e;
  }
  console.log = realLog;
  globalThis.fetch = realFetch;
  return { calls, error };
}

let n = 0;
function ok(name) {
  n += 1;
  console.log(`ok ${n}  ${name}`);
}

{
  const { calls, error } = await run([{ status: 204 }]);
  assert.equal(error, null);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "https://api.github.com/repos/gazette1/double-double/actions/workflows/daily_dd_discord.yml/dispatches");
  assert.equal(calls[0].init.method, "POST");
  assert.equal(calls[0].init.headers.Authorization, "Bearer test-token");
  assert.equal(calls[0].init.headers.Accept, "application/vnd.github+json");
  assert.ok(calls[0].init.headers["User-Agent"]);
  assert.deepEqual(JSON.parse(calls[0].init.body), { ref: "main", inputs: { step: "auto" } });
  ok("one POST with the token, the workflow file, ref main and step auto");
}
{
  const { calls, error } = await run([{ status: 502 }, { status: 204 }]);
  assert.equal(error, null);
  assert.equal(calls.length, 2);
  ok("a 502 is retried and the second attempt succeeds");
}
{
  const { calls, error } = await run([{ status: 401, body: "Bad credentials" }]);
  assert.equal(calls.length, 1);
  assert.match(error.message, /401/);
  ok("a 401 is not retried and the run fails visibly");
}
{
  const { calls, error } = await run([{ status: 422, body: "Unexpected inputs" }]);
  assert.equal(calls.length, 1);
  assert.match(error.message, /422/);
  ok("a 422 is not retried and the run fails visibly");
}
{
  const { calls, error } = await run([new Error("network down")]);
  assert.equal(calls.length, 3);
  assert.match(error.message, /network down/);
  ok("a network error is tried three times and then fails visibly");
}
{
  const { calls, error } = await run([{ status: 500 }]);
  assert.equal(calls.length, 3);
  assert.match(error.message, /500/);
  ok("repeated 500s stop after three attempts and fail visibly");
}
{
  const r = await worker.fetch();
  assert.equal(r.status, 200);
  ok("a plain request only answers that the Worker is alive");
}
console.log(`all ${n} tests passed`);
