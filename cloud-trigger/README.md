# DD bot trigger (Cloudflare Worker)

Starts the Double Double Bot GitHub Action on time, with the Claude app closed and the PC off.

GitHub starts this repository's own scheduled runs many hours late (2026-11-09 to 2026-11-20: mostly between 9 PM and 2 AM Eastern, a few days between 5 and 7 PM). A manual dispatch starts within seconds, and a Cloudflare cron trigger fires on the minute. This Worker sends one request at each trigger: dispatch `daily_dd_discord.yml` with `step=auto`. The workflow's first step, `tools/ci_gate.py`, reads the New York clock and the run log and decides whether that run posts the five, takes the pre-tip snapshot or does nothing, so extra dispatches are harmless.

Nothing here holds state. The only secret is a GitHub token, stored as a Worker secret and never committed.

## Schedule

All times in the first two columns are UTC. Every trigger dispatches `step=auto`.

| Cron | Fires at | Eastern, standard time | Eastern, daylight time |
|---|---|---|---|
| `55 18-20 * * *` | 18:55, 19:55, 20:55 | 1:55, 2:55, 3:55 PM | 2:55, 3:55, 4:55 PM |
| `25 19-20 * * *` | 19:25, 20:25 | 2:25, 3:25 PM | 3:25, 4:25 PM |
| `40 22-23 * * *` | 22:40, 23:40 | 5:40, 6:40 PM | 6:40, 7:40 PM |
| `10 23,0 * * *` | 23:10, 00:10 | 6:10, 7:10 PM | 7:10, 8:10 PM |

The gate acts on the first daily dispatch at or after 2:50 PM Eastern, which is 2:55 PM in both seasons, and on the first pre-tip dispatch inside 6:30 to 7:30 PM Eastern, which is 6:40 PM. The other dispatches are backups and stop within seconds.

## One-time setup, about ten minutes

1. Create the GitHub token at https://github.com/settings/personal-access-tokens/new. Name it `dd-bot-trigger`, set the expiration to one year, choose Only select repositories and pick `gazette1/double-double`, and under Repository permissions set Actions to Read and write. Generate it and copy it. Do not paste it into a chat or commit it.
2. In this folder run `npm install`. This installs Wrangler, Cloudflare's command line tool, into this folder only.
3. Run `npx wrangler login`. It opens the browser to sign in to the free Cloudflare account.
4. Run `npx wrangler secret put GITHUB_TOKEN` and paste the token at the prompt.
5. Run `npm run deploy`. It publishes the Worker and registers the four cron triggers, four of the five that the free plan allows.

## Check it

- `npm test` runs the local tests (no network).
- `npx wrangler tail` streams the Worker's logs. A good dispatch logs `dispatched, attempt 1`.
- `gh run list --repo gazette1/double-double` shows `workflow_dispatch` runs at the minutes above. The 2:55 PM Eastern one posts the five: the commit author is dd-bot and the run log gets a `post_top` row.
- The Cloudflare dashboard shows each cron run under Workers, dd-bot-trigger, Logs. A failed dispatch is thrown, so it shows as an error there.

## Notes

- The token expires after the chosen period. GitHub emails a warning a week before. Create a new one and run step 4 again.
- To change the times, edit `crons` in `wrangler.toml` (UTC) and run `npm run deploy`. To stop the Worker, run `npx wrangler delete`.
- The cron list in the workflow file stays as a late backup. The Claude app task `dd-bot-330pm-fallback` stays a backstop until this has posted for a few days.
