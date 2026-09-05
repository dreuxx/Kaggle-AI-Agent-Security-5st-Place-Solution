# Supporting Evidence

### Compiling User Messages into Faster Tool Calls

**Giovanny Rodríguez · Kaggle Working Note · 2026**

> **Repository publication update.** The original note was prepared from the Markdown record. The subsequently supplied repository ZIP contains the historical JSONs. This release now includes 24 selected artifacts, including both EOG probes. Their numerical fields were checked directly against the archived JSONs; no inference was rerun. Personal local paths were sanitized, and original/published hashes are listed in [the artifact manifest](../experiments/artifact_manifest.json). See [Publication Notes](PUBLICATION_NOTES.md) for the unchanged article’s earlier availability statement.

This supplement separates source evidence, recorded experiments, arithmetic, and interpretations. It is not a log of new model runs. The main article is `Working_Note.md`; the figure’s underlying values are in `Figure_Data.json`.

## 1. What was available for this revision

The source set includes the supplied research manuscript, dated experiment ledger, two technical audits, final-result audit, and current `attack.py`. These files were inspected to check the article. During the original editorial preparation, historical JSON filenames and hashes were read from the ledger and their underlying bytes were unavailable. The repository publication update above records the subsequent file-level verification. No model, private guardrail, or Kaggle submission was executed during editorial preparation.

The author’s explicit account supplies the motivation: public implementations already produced successful attacks; most effort went into HTTP as a stable latency test case despite low confidence in marker transfer. This intent is not inferred solely from the final leaderboard. The 24 August baseline and strict-surrogate experiments independently document that transfer risk was being investigated before the final submission. They do not identify Kaggle’s actual private defense.

## 2. Source register

| Article reference | Material | Use |
|---|---|---|
| [1] | Kaggle competition overview; evaluator FAQ supplied in the conversation | Benchmark purpose and static public/private replay contract |
| [2] | Pilkwang Kim’s public throughput discussion | Acknowledgment that throughput and the second generation were already community concerns |
| [3] | `WORKING_NOTE_USER_MESSAGE_PROGRAM.md` | Execution model, state schematics, cumulative endpoints, EOG diagnostics, limitations |
| [4] | `RESULTADOS_EXPERIMENTOS(2).md` | Experiment dates, immediate controls, exact times, repeat counts, rejected changes, historical hashes |
| [4], supporting audit | `INVESTIGACION_TECNICA(2).md` | Source-level lifecycle and explicit distinction between a local surrogate and hidden defense |
| [4], supporting audit | `MODEL_SPECIFIC_RESEARCH(2).md` | Model-specific parsing, tokenization, reconstructed history, and remaining costs |
| [5] | `attack.py` | Preserved fixed versus adaptive paths, routing assumption, Gemma warm-up |
| [6] | `REPORTE_FINAL_KAGGLE_AI_SECURITY_BETA(2).md` | Recorded API audit of v50/v57 scores, fifth place, and unavailable historical kernel |
| [7] | OpenAI Harmony documentation | General role/channel and function-call vocabulary; not the pinned local template |
| [8] | Google Gemma 4 formatting documentation | General native thought/tool format; not proof of every local parser behavior |

The local Markdown sources remain the basis for the experimental claims. Public documentation supplies context, not substitute measurements.

### Public references

[1a. Competition overview](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks)  
[1b. Evaluator update and FAQ](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks/discussion/712642)  
[2. Crossing 60 on v3.1.2: a throughput mental model, and a pile of things that didn’t work](https://www.kaggle.com/competitions/ai-agent-security-multi-step-tool-attacks/discussion/723698)  
[7. OpenAI Harmony response format](https://github.com/openai/harmony/blob/main/docs/format.md)  
[8. Google Gemma 4 Prompt Formatting](https://ai.google.dev/gemma/docs/core/prompt-formatting-gemma4)

Public research was revisited on 4 September 2026. Kaggle’s indexed results exposed the competition purpose, judging headings, and the throughput discussion’s two-generation observation. Several direct Kaggle page bodies were unavailable through the reading interface. The requested first-place and `60th-place` writeups were not available in full, so the article does not claim a comprehensive comparison with either, nor that all leading teams used the same objective or method. No account credential is included in this publication package.

## 3. Numerical evidence map

### Retained HTTP runs: recorded values

| Model/run | Complete replay (s) | Call generation (s) | Post-tool generation (s) |
|---|---:|---:|---:|
| GPT header run 1 | 83.880632 | 57.213887 | 22.768847 |
| GPT header run 2 | 84.835667 | 57.820430 | 23.073003 |
| Gemma late-variable run 1 | 267.206668 | 154.964174 | 107.631514 |
| Gemma late-variable run 2 | 266.788959 | 154.449082 | 107.577191 |

Each cited run is recorded as retaining 200 findings and 200 score cells. The primary ledger locations are the 27 August headings **“GPT-OSS: demostracion con header parser/canonical duplicado”** and **“Gemma: URL al ultimo caracter”**.

### Derived values: calculated from those records

| Quantity | GPT-OSS | Gemma |
|---|---:|---:|
| Mean total | 84.358150 s | 266.997814 s |
| Mean first phase | 57.517159 s | 154.706628 s |
| Mean post-tool phase | 22.920925 s | 107.604353 s |
| Residual: total minus two phases | 3.920067 s | 4.686833 s |
| Generation share of total | 95.4% | 98.2% |
| Post-tool share of total | 27.2% | 40.3% |
| Immediate previous control | 86.666308 s | 282.324295 s |
| Immediate-control reduction | 2.66% | 5.43% |
| Initial historical endpoint | 109.373 s | 396.973 s |
| Cumulative endpoint reduction | 22.9% | 32.7% |

Small last-decimal differences arise from displaying rounded values. The calculation uses the six-decimal recorded run times. Residual is a difference of profiled quantities, not a direct measurement of tool execution.

The isolated header and punctuation experiments are not the whole optimization ladder. It would be incorrect to attribute 22.9% solely to header alignment or 32.7% solely to removing punctuation.

### Gemma format comparison

The ledger’s **“Gemma bare: A/B intercalado y promocion model-specific”**, 26 August, records a balanced sequence of bare/base/base/bare examples: 100 candidates per format, all valid. Bare mean was **1.603303 s** versus **1.683110 s** for the canonical control. The lower time persisted within the recorded repeated-format and format-switch subsets.

This comparison provides within-run evidence for that local format change. It does not make the full sequential search randomized or remove all cache interactions.

### Counterexample: faster before the tool, slower overall

The manuscript’s **“Ablation: Why the Whole Interaction Matters”** reports the 23-layer Gemma comparison used in Table 1. The first-generation difference is **−5.800 s**, the post-tool difference **+11.942 s**, and the total difference **+6.263 s**. The small residual also changes; the two generation deltas need not sum exactly to the total delta.

### Email reimplementation

The ledger’s 30 August GPT reordered-argument experiment records **86.500154, 85.589797, and 84.739109 seconds**. The 31 August Gemma compact-signature/no-reply experiment records **269.013938, 262.160341, and 259.107822 seconds**, averaging **263.427367 seconds**. These are distinct tool-schema/source states from the HTTP experiments.

No frozen, unretuned HTTP-to-email port was preserved as a control. The supported conclusion is functional reimplementation, not an isolated causal estimate of portability.

## 4. Historical artifact index

The following identifiers were cited by the original manuscript. They are now included as privacy-sanitized copies in [the selected-results index](../experiments/README.md); use that index for their repository locations:

| ID | Recorded filename | Evidence |
|---|---|---|
| H1 | [baseline_original200_gpt_optimal.json](../experiments/selected_results/http/gpt/baseline_original200_gpt_optimal.json) | Initial GPT HTTP endpoint |
| H2 | [baseline_original200_gemma_optimal.json](../experiments/selected_results/http/gemma/baseline_original200_gemma_optimal.json) | Initial Gemma HTTP endpoint |
| H3 | [gpt_duplicate_header_alignment200_optimal.json](../experiments/selected_results/http/gpt/gpt_duplicate_header_alignment200_optimal.json) | GPT retained run 1 |
| H4 | [gpt_duplicate_header_alignment200_optimal_repeat.json](../experiments/selected_results/http/gpt/gpt_duplicate_header_alignment200_optimal_repeat.json) | GPT retained run 2 |
| H5 | [gemma_zh_no_trailing_punctuation_24layers200_optimal.json](../experiments/selected_results/http/gemma/gemma_zh_no_trailing_punctuation_24layers200_optimal.json) | Gemma retained run 1 |
| H6 | [gemma_zh_no_trailing_punctuation_repeat_24layers200_optimal.json](../experiments/selected_results/http/gemma/gemma_zh_no_trailing_punctuation_repeat_24layers200_optimal.json) | Gemma retained run 2 |
| H7 | [gpt_posttool_stop_depth_20260828.json](../experiments/selected_results/diagnostics/gpt_posttool_stop_depth_20260828.json) | Reported GPT EOG probe |
| H8 | [gemma_posttool_stop_depth_exact_renderer_20260828.json](../experiments/selected_results/diagnostics/gemma_posttool_stop_depth_exact_renderer_20260828.json) | Reported Gemma EOG probe |
| H9 | [gemma_end_without_text_23layers200_optimal.json](../experiments/selected_results/ablations/gemma_end_without_text_23layers200_optimal.json) | Language-ablation control |
| H10 | [gemma_end_without_text_23layers200_optimal_repeat.json](../experiments/selected_results/ablations/gemma_end_without_text_23layers200_optimal_repeat.json) | Repeated language-ablation control |
| H11 | [gemma_zh_bare_23layers200_optimal.json](../experiments/selected_results/ablations/gemma_zh_bare_23layers200_optimal.json) | Faster-first/slower-total variant |

The manuscript reports GPT EOG rank 128, gap −33.56 and three structural tokens; Gemma rank 2, gap −18.03 and four structural tokens. These remain **reported probe diagnostics**. Their raw logit arrays were not independently reprocessed. A negative logit gap is not a probability, and token rank does not determine the size of the gap.

## 5. Source versions and reproducibility boundary

**Preserved current source:** `attack.py`, 1,153 lines. Its hash was recomputed during preparation:

`2ababf986a963333118fbf19c282e7004057acc4191b3f5dd4db471c17ef2bf3`

The file’s ordinary path emits fixed model-specific email candidates; adaptive search requires explicit experimental configuration. The default cap is 2,000. Model dispatch uses configuration or an invocation-order assumption, not an inference-based classifier. The Gemma branch makes one warm-up interaction. A comment calling this path “zero interaction” is therefore less precise than the executable behavior.

Historical source hashes recorded for the central HTTP experiments:

| Experiment | Source SHA-256 recorded in the ledger |
|---|---|
| GPT retained header | `66c9e28a8e4621dccffe37483160c7dd26dc4779a9fb17de0e4a5e2a421e8a27` |
| Gemma late-variable/punctuation | `e8cf1f95533f820367b7a99443c165f7f6baa2d87a0f20a8c2df14ce5c09ad05` |

These are not the current source hash. Substituting the current file for every historical comparison would invalidate the provenance claim.

The reproduction target is the matching source, emitted messages, embedded GGUF template, SDK/parser, decoding settings, and per-run offload configuration. The main records use `llama-cpp-python 0.3.34`, deterministic decoding, context 8,192, and an RTX A5000. Gemma 24-layer finalist measurements must not be pooled with the separate 23-layer ablation. The current revision verified document arithmetic and source identity, not new model performance.

## 6. Final result and scope

The supplied 1 September result audit records:

| Entry | Submission reference | Public | Private |
|---|---:|---:|---:|
| v50 | 55861605 | 115.240 | 0.000 |
| emailv1 v57 | 55905209 | 40.155 | 40.365 |

The selected entry is recorded at fifth place. The audit also records a `403 Forbidden` when trying to retrieve historical v57. Thus, the code currently supplied is not independently authenticated as that exact historical notebook. Private per-model traces were not exposed. The outcome supports family-level transfer, not knowledge of the hidden guardrail’s implementation.

The honeypot description is a competitive analogy: a strongly rewarded public target did not transfer in the corresponding private submission. It does not assert intentional deception or a universal statement about every possible marker attack.

## 7. Publication checks

The article preserves the author’s requested arc: working public baseline, timing bottleneck, constrained formulation, model-specific method, failed hypotheses, email adaptation, and evaluator outcome. It includes the public-code acknowledgment, intentional HTTP testbed, bounded honeypot comment, structural chat-format examples, interleaved control, post-tool diagnostics, and explicit limitations.

The five requested Working Note dimensions are addressed through evidence rather than promotional claims: implementation and assumptions in Sections 2–5; methodology in Section 5; security interpretation in Sections 3–4 and 8; reusable measurement lessons in Sections 7–8; and the scope statement, attribution, and provenance limits. This is an editorial coverage check, not a prediction of the award decision.

The supplied research note discloses substantial AI assistance. The article preserves that acknowledgment alongside the participant’s role in research direction and final decisions.
