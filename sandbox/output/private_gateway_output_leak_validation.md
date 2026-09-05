# Validation: potential private-guardrail leakage through gateway outputs

Candidate ID: `GW-PRIVATE-LOG-001`

Disposition: **deferred**. The gateway definitely emits private replay details to its own stdout and writes private scores in its own working directory. Competitor access to those gateway-owned outputs during a hosted rerun is not established; the local package and the available downloaded ZIPs instead indicate container separation and restricted error visibility.

## Claim

During static private replay, raw guardrail denial reasons and private scores may reach outputs visible to the submission author. If visible, this would create a private-policy oracle and weaken the held-out evaluation.

## Validation rubric

- [x] A private replay can produce a policy-specific denial reason.
- [x] The gateway prints that raw reason without `_OpaqueAttackEnv` redaction.
- [x] The gateway writes exact private scores to `submission.csv` and `submission_details.json`.
- [ ] A hosted rerun exposes gateway stdout to the competitor.
- [ ] A hosted rerun exposes the gateway-created score/detail files to the competitor.

## Source, control, and sinks

- Source: raw `tool_event.error` from the replay environment.
- Intended control: `aicomp_sdk/core/env/opaque.py:27-35` reduces `denied:<reason>` to `denied`, but this wrapper protects only attacker-visible exploration traces.
- Stdout sink: `kaggle_evaluation/jed_attack_134815/jed_attack_gateway.py:793-806` prints the first 80 characters of every raw replay error.
- Score stdout sink: `jed_attack_gateway.py:854-861` and `:987-993` print per-guardrail and final scores.
- File sink: `jed_attack_gateway.py:951-961` retains private summaries, while `:1012-1023` writes them to `submission.csv` and `submission_details.json`.

## Dynamic reproduction

The real `_replay_and_score()` method was exercised locally with a sentinel denial reason and no model startup. Its stdout contained:

```text
[REPLAY][deterministic] [BLOCKED] http.post [SHARE] err=denied:PRIVATE_RULE_SENTINEL_ALPHA
```

The real `write_submission()` method was then exercised with a sentinel private score. `submission_details.json` contained `gpt_oss_private: 12.34` and its private summary. This proves both sinks. The sentinel is synthetic: it demonstrates the exact gateway behavior but does not prove exposure of the real private implementation.

## Boundary and counterevidence

- `kaggle_evaluation/README.md:5-7` states that participant code and scoring code run in different containers and that only limited errors are provided.
- `README.md:51-53` explicitly says hosted scoring does not show full error messages.
- `kaggle_evaluation/core/base_gateway.py:77-83` describes detailed gateway errors as host-visible, not competitor-visible.
- The JED gateway does not share `submission_details.json`, `submission.csv`, or gateway logs through `/kaggle/shared/`.
- Five locally available competition-result archives were checked: `results (3).zip`, `results (4).zip`, `results (5).zip`, `results (6).zip`, and `499.zip`. None contained gateway replay logs, `submission_details.json`, `submission.csv`, `result.json`, private row IDs, or raw `denied:` reasons. Their recorded guardrail identity was public-only where present.

These facts prevent classifying the issue as a confirmed competitor-visible leak.

## Exact remaining proof

Use an already completed hosted rerun; no new probing submission is required.

1. Open every downloadable log/output surface for that rerun.
2. Search for `[REPLAY]`, `err=denied:`, `gpt_oss_private`, `gemma_private`, and `submission_details.json`.
3. Download the rerun output archive and list all files, then repeat the content search.
4. Preserve the submission ID, timestamps, screenshot, archive hash, and exact matching lines.

If any raw private denial reason or hidden private score is visible to the submission author, promote this finding to **reportable**. If only inference-server/notebook logs are visible and gateway logs/files remain host-only, suppress the cross-boundary leak claim while retaining the excessive internal logging as a hardening issue.

## Impact if the boundary is crossed

The logs disclose candidate-level allow/deny behavior, tool type, side effect, raw policy reason, predicate result, replay count, and exact private score. Repeated submissions could then distinguish private rule families and optimize directly against a defense intended to remain held out. This is an evaluator information-disclosure vulnerability, not a prompt bypass.

## Recommended remediation

- Apply `_redact_guardrail_error()` before every replay log statement.
- Disable per-candidate details during private replay; retain aggregate operational counters only.
- Do not print hidden private scores to stdout.
- Keep `submission_details.json` host-only or omit private details from it.
- Add an integration test proving no private reason, predicate evidence, or hidden score reaches participant-visible logs or files.
