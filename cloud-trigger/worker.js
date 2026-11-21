// DD bot trigger: a Cloudflare Worker whose cron triggers start the Double Double Bot GitHub Action on time.
//
// Russ, 2026-11-08: "this shouldnt rely on claude coder being open to run it should run everyday like how the
// strikeout did". GitHub starts this repository's scheduled runs many hours late (mostly 9 PM to 2 AM Eastern,
// checked 2026-11-09 to 2026-11-20), but a workflow_dispatch starts within seconds and a Cloudflare cron trigger
// fires on the minute. So this Worker sends one request per trigger: dispatch the workflow with step=auto.
// tools/ci_gate.py, the workflow's first step, decides from the New York clock and the run log whether that run
// posts the five, takes the pre-tip snapshot or does nothing, so extra dispatches are harmless.
//
// Secret (npx wrangler secret put GITHUB_TOKEN): a fine-grained token for the one repository, Actions read and write.
// Vars (wrangler.toml [vars]): GITHUB_REPO, GITHUB_WORKFLOW, GITHUB_REF. RETRY_WAIT_MS is only for the tests.

const ATTEMPTS = 3;
const WAIT_MS = 4000;
// 401, 403, 404 and 422 mean the token, the repository, the workflow or the input is wrong; a retry cannot fix them.
const NO_RETRY = new Set([401, 403, 404, 422]);

async function dispatch(env) {
  const url = `https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/${env.GITHUB_WORKFLOW}/dispatches`;
  const wait = Number(env.RETRY_WAIT_MS ?? WAIT_MS);
  let last = "";
  for (let attempt = 1; attempt <= ATTEMPTS; attempt++) {
    try {
      const r = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_TOKEN}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "dd-bot-trigger",
        },
        body: JSON.stringify({ ref: env.GITHUB_REF || "main", inputs: { step: "auto" } }),
      });
      if (r.status === 204) return { ok: true, attempt };
      last = `HTTP ${r.status} ${(await r.text()).slice(0, 200)}`;
      if (NO_RETRY.has(r.status)) break;
    } catch (e) {
      last = String(e);
    }
    if (attempt < ATTEMPTS) await new Promise((resolve) => setTimeout(resolve, wait));
  }
  return { ok: false, error: last };
}

export default {
  // Cron trigger: dispatch the workflow. A failure is thrown so the Cloudflare dashboard shows the run as failed.
  async scheduled(event, env) {
    const out = await dispatch(env);
    if (!out.ok) {
      console.log(`cron ${event.cron}: dispatch failed, ${out.error}`);
      throw new Error(`dispatch failed: ${out.error}`);
    }
    console.log(`cron ${event.cron}: dispatched, attempt ${out.attempt}`);
  },
  async fetch() {
    return new Response("DD bot trigger is alive.", { status: 200 });
  },
};
