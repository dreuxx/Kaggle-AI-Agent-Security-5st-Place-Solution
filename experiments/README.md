# Selected experiment evidence

This selection supports the Working Note rather than retaining only favorable results. It includes initial controls, a balanced comparison, retained runs, a counterexample, an additional timing-variance control, EOG diagnostics, and a negative prewarm experiment.

**24 archived JSONs are included.** Numerical and behavior fields come from the uploaded ZIP. No model inference was run during publication preparation.

[Machine-readable manifest](artifact_manifest.json) · [Summary CSV](summary.csv) · [Recorded arithmetic checks](record_checks.json)

| Artifact | Purpose | Recorded replay | Findings / cells |
|---|---|---:|---:|
| [baseline_original200_gpt_optimal.json](selected_results/http/gpt/baseline_original200_gpt_optimal.json) | Initial HTTP control | 109.373 s | 200 / 200 |
| [baseline_original200_gemma_optimal.json](selected_results/http/gemma/baseline_original200_gemma_optimal.json) | Initial HTTP control | 396.973 s | 200 / 200 |
| [gpt_compact_http200_optimal.json](selected_results/http/gpt/gpt_compact_http200_optimal.json) | Compact Harmony milestone | 91.334 s | 200 / 200 |
| [gpt_compact_no_final200_optimal.json](selected_results/http/gpt/gpt_compact_no_final200_optimal.json) | No natural-language final; run 1 | 88.725 s | 200 / 200 |
| [gpt_compact_no_final200_optimal_repeat.json](selected_results/http/gpt/gpt_compact_no_final200_optimal_repeat.json) | No natural-language final; run 2 | 88.753 s | 200 / 200 |
| [gpt_duplicate_header_alignment200_optimal.json](selected_results/http/gpt/gpt_duplicate_header_alignment200_optimal.json) | Retained GPT header; run 1 | 83.881 s | 200 / 200 |
| [gpt_duplicate_header_alignment200_optimal_repeat.json](selected_results/http/gpt/gpt_duplicate_header_alignment200_optimal_repeat.json) | Retained GPT header; run 2 | 84.836 s | 200 / 200 |
| [gemma_bare_base_interleaved200_optimal.json](selected_results/http/gemma/gemma_bare_base_interleaved200_optimal.json) | Balanced interleaved bare/canonical comparison | 328.678 s | 200 / 200 |
| [gemma_bare_promoted200_optimal.json](selected_results/http/gemma/gemma_bare_promoted200_optimal.json) | Bare-argument milestone | 296.028 s | 200 / 200 |
| [gemma_zh_no_trailing_punctuation_24layers200_optimal.json](selected_results/http/gemma/gemma_zh_no_trailing_punctuation_24layers200_optimal.json) | Retained Gemma endpoint; run 1 | 267.207 s | 200 / 200 |
| [gemma_zh_no_trailing_punctuation_repeat_24layers200_optimal.json](selected_results/http/gemma/gemma_zh_no_trailing_punctuation_repeat_24layers200_optimal.json) | Retained Gemma endpoint; run 2 | 266.789 s | 200 / 200 |
| [gemma_end_without_text_23layers200_optimal.json](selected_results/ablations/gemma_end_without_text_23layers200_optimal.json) | 23-layer language-ablation control; run 1 | 298.353 s | 200 / 200 |
| [gemma_end_without_text_23layers200_optimal_repeat.json](selected_results/ablations/gemma_end_without_text_23layers200_optimal_repeat.json) | 23-layer language-ablation control; run 2 | 308.061 s | 200 / 200 |
| [gemma_zh_bare_23layers200_optimal.json](selected_results/ablations/gemma_zh_bare_23layers200_optimal.json) | Faster first generation, slower complete replay | 309.470 s | 200 / 200 |
| [gpt_posttool_stop_depth_20260828.json](selected_results/diagnostics/gpt_posttool_stop_depth_20260828.json) | Post-tool EOG diagnostic; not a full replay | Diagnostic | Not a replay gate |
| [gemma_posttool_stop_depth_exact_renderer_20260828.json](selected_results/diagnostics/gemma_posttool_stop_depth_exact_renderer_20260828.json) | Post-tool EOG diagnostic; not a full replay | Diagnostic | Not a replay gate |
| [gpt_email_emptyargs_numericto_tailreorder_99layers200_optimal_run1_20260830.json](selected_results/email/gpt/gpt_email_emptyargs_numericto_tailreorder_99layers200_optimal_run1_20260830.json) | GPT email schema reimplementation; run 1 | 86.500 s | 200 / 200 |
| [gemma_email_compact_signature_noreply_28tok_graphs_24layers200_optimal_run1_20260831.json](selected_results/email/gemma/gemma_email_compact_signature_noreply_28tok_graphs_24layers200_optimal_run1_20260831.json) | Gemma email reimplementation; run 1 | 269.014 s | 200 / 200 |
| [gpt_email_emptyargs_numericto_tailreorder_99layers200_optimal_run2_20260830.json](selected_results/email/gpt/gpt_email_emptyargs_numericto_tailreorder_99layers200_optimal_run2_20260830.json) | GPT email schema reimplementation; run 2 | 85.590 s | 200 / 200 |
| [gemma_email_compact_signature_noreply_28tok_graphs_24layers200_optimal_run2_20260831.json](selected_results/email/gemma/gemma_email_compact_signature_noreply_28tok_graphs_24layers200_optimal_run2_20260831.json) | Gemma email reimplementation; run 2 | 262.160 s | 200 / 200 |
| [gpt_email_emptyargs_numericto_tailreorder_99layers200_optimal_run3_20260830.json](selected_results/email/gpt/gpt_email_emptyargs_numericto_tailreorder_99layers200_optimal_run3_20260830.json) | GPT email schema reimplementation; run 3 | 84.739 s | 200 / 200 |
| [gemma_email_compact_signature_noreply_28tok_graphs_24layers200_optimal_run3_20260831.json](selected_results/email/gemma/gemma_email_compact_signature_noreply_28tok_graphs_24layers200_optimal_run3_20260831.json) | Gemma email reimplementation; run 3 | 259.108 s | 200 / 200 |
| [gemma_email_compact_signature_noreply_28tok_graphs_24layers200_optimal_control_run4_20260831.json](selected_results/email/gemma/gemma_email_compact_signature_noreply_28tok_graphs_24layers200_optimal_control_run4_20260831.json) | Additional same-family control showing timing variance | 286.579 s | 200 / 200 |
| [gpt_prewarm_all200_onehop_99layers200_optimal_20260828_run1.json](selected_results/ablations/gpt_prewarm_all200_onehop_99layers200_optimal_20260828_run1.json) | Prewarm all 200; negative result | 93.088 s | 200 / 200 |

## Integrity and privacy

`original_sha256` hashes the file as it appeared in the uploaded ZIP. `published_sha256` hashes the included privacy-sanitized copy. A changed file hash is expected when a local machine path has been replaced. The manifest lists each changed JSON field without reproducing the personal path.

For this selected set, candidate messages, replay rows, tool events, and diagnostic observations are unchanged. Historical `attack_sha256` values identify the original experiment’s source state; they are not claimed to identify the repository’s root source.

The full collection is kept separately to avoid adding hundreds of exploratory outputs to Git history. Do not interpret absence from this curated selection as failure, success, or deletion of an experiment.
