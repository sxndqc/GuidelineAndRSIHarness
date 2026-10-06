# Runtime audit, 2026-10-06

Responding to the user's latency question, inspect actual episode traces and the transport ledger (approximately 10,108 requests at inspection).

- Completed request latency: Sol median 10.2 s, p90 14.7 s; Luna median 11.9 s, p90 32.8 s. These measurements include CLI/transport/model work, not pure model inference.
- CAP Sol frozen seed11 B4: 16 evaluation batches, 189 recorded model calls, 9.2 minutes elapsed from first request start to last completion. Four workers overlap batches; within an episode, decisions depend on earlier tool results.
- SNACS Sol moderation seed11 B64: 175 evaluation plus25 adaptation calls, 15.8 minutes elapsed.
- SNACS Sol B0 made33 searches against the empty purchased-example collection, an observed avoidable tool-use inefficiency.
- Each action currently launches a fresh ephemeral Codex CLI process and supplies serialized prior history. This is an implementation overhead, but its isolated contribution has not been profiled; no numerical speedup from persistent sessions is claimed.
- Parsing the7.2MB ledger took approximately0.039s in one check, much smaller than typical per-request wall time. This does not profile all file-lock contention.

The status audit also found the supervisor process absent and its status file stale since19:52 UTC. SNACS Luna's controller was absent while its report still said running; CAP Luna had stopped on an explicitly recorded timeout. Sol children remained active. There was no retained supervisor traceback identifying why it exited, so a tool-session lifetime limit is only a hypothesis, not an established cause.

After separately auditing CAP timeout5851, restart the missing controllers and supervisor as detached processes. Preserve completed episodes, total budgets, models, original settings and transport attempts. Preserve supervisor continuation counts across process restarts. Record recovery limitations in research/process-recovery-20261006.json. Do not describe prior missing in-progress episode traces as exact-history recovery. No predictive-method, sample, reasoning-effort or action-cap change is made in this repair.
