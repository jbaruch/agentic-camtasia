# Feature-complete 1.0

The operator's 2026-11-06 instruction makes 1.0.0 the final release after all
remaining release-plan gaps are complete. Scope includes closed/deferred issue
families and the [Mac coverage follow-ups](mac-feature-coverage.md#known-follow-ups).
Continue a patch/minor release after each feature. Keep 1.0.0 unpublished until
the completion audit below passes.

On 2026-11-07 the operator deferred quizzes (called "puzzles"), Snagit and
Audiate. Their remaining work, including quiz-specific SCORM session follow-ups,
is excluded from 1.0 and must be skipped until requested again. Existing shipped
support remains documented. Rev/Zoom/cloud
imports retain their pending status.

## Remaining capability families

Each row remains incomplete until its named gaps have concrete implementation
or an exercised native workflow, with the applicable verification evidence.
References define existing support and preserve the remaining limitations.
Closed historical issues retain their original scope; this checklist tracks the
additional 1.0 work independently of those issue states.

Linked moving recording captions ship in 0.53.0, moving-recording stitches in
0.54.0 and moving/held captions in 0.55.0. Mixed/multiple-source caption
composition ships in 0.56.0 through native Groups, including independent child
and source edits with common speed/cropping. The caption row remains pending
for other RTF forms and display controls. Block and active-word backgrounds
ship in 0.59.0; active-word stroke color and glow ship in 0.60.0. Explicit caption-scene sequencing
ships in 0.58.0; interactive scene destinations retain their separate rows. Nonzero audio-file
sample offsets ship in 0.57.0 with distinct physical and nominal caption clocks.

| Status | Remaining gap | Contract and tracking |
| --- | --- | --- |
| Pending | Further effect-specific point/resource controls and linked held/stitched/container forms. | [#2](https://github.com/jbaruch/agentic-camtasia/issues/2), [effects](../skills/camtasia-project/references/advanced-features.md), [cursor paths](../skills/camtasia-project/references/cursors.md). |
| Pending | Group-contained linked moving recording behaviors ship in 0.33.0 and selected native phase-style copying in 0.34.0; further behavior controls and linked owner forms remain. | [#3](https://github.com/jbaruch/agentic-camtasia/issues/3), [behaviors](../skills/camtasia-project/references/behaviors.md), [recording owners](../skills/camtasia-project/references/behavior-recordings.md). |
| Pending | Discrete timed annotation rich styles and effective-state clearing ship in 0.36.0. Native sizing/ligature switches ship in 0.37.0 and static region strength/color/inversion edits in 0.38.0. Standalone keystroke key/style/visibility edits with explicit geometry ship in 0.39.0. Group-contained keystroke edits and native Group sizing ship in 0.40.0. Standalone Sketch Motion drawing-time and stroke controls ship in 0.41.0. Group-contained and trimmed/speed-adjusted Sketch Motion controls ship in 0.42.0. Root and Group-contained text wrapping and outline placement, including retained timed rich states, ship in 0.43.0. Continuous text-outline intervals, coupled easing/removal and Group/trim/speed clocks ship in 0.44.0. Continuous remix fill/stroke intervals, combined text/shape outlines and Group/trim/speed clocks ship in 0.45.0. Group-contained discrete rich-style authoring and effective-state clearing ship in 0.46.0, including selected-child trim/speed clocks and retained continuous outlines. Remaining native shape/text controls still need completion. | [#4](https://github.com/jbaruch/agentic-camtasia/issues/4), [annotation ranges](../skills/camtasia-project/references/annotation-rich-ranges.md), [region controls](../skills/camtasia-project/references/advanced-features.md#static-region-controls), [Group keystrokes](../skills/camtasia-project/references/advanced-features.md#group-contained-keystroke-edits), [text editing](../skills/camtasia-project/references/annotation-text-edits.md). |
| Pending | Global closed-caption styling ships in 0.47.0 and text-only native RTF edits in 0.48.0. Group closed clocks ship in 0.49.0; Group source-word mapping/retiming and parent-clock display bounds ship in 0.50.0. Ordinary-AV stitched parent cues, separate source-word/display clocks and parent retiming ship in 0.51.0. Audio-only stitched clocks, parent cue edits and subframe audio cuts ship in 0.52.0. Root/Group moving recording captions ship in 0.53.0 and same-source moving-recording stitched captions in 0.54.0. Moving/held recording stitch clocks and separate caption layers over silent holds ship in 0.55.0. Mixed/multiple-source caption composition ships in 0.56.0 through native Groups with independent child/source clocks. Nonzero audio-file sample offsets ship in 0.57.0 with separate physical audio and nominal caption clocks. Explicit native Group sequencing for CSML-only caption scenes ships in 0.58.0. Block and active-word backgrounds ship in 0.59.0 with native root/Group preservation and rendering; active-word stroke color and glow ship in 0.60.0 with native UI/helper and root/Group comparisons. Other RTF forms and remaining dynamic display controls still need completion. | [#5](https://github.com/jbaruch/agentic-camtasia/issues/5), [captions](../skills/camtasia-project/references/captions.md). |
| Pending | Additional themed/animated Quick Property controls and theme/resource combinations. | [#6](https://github.com/jbaruch/agentic-camtasia/issues/6), [#7](https://github.com/jbaruch/agentic-camtasia/issues/7), [Quick Properties](../skills/camtasia-project/references/quick-properties.md), [theme duplication](../skills/camtasia-project/references/theme-duplication.md). |
| Pending | Group-contained linked moving recording mattes ship in 0.32.0; native linked-recording stitched parents and unstitched silent holds ship in 0.35.0, including the trimmed-frame picture limitation. Further container forms and any working native point-intensity representation remain. | [#8](https://github.com/jbaruch/agentic-camtasia/issues/8), [recording mattes](../skills/camtasia-project/references/matte-recording-owners.md), [composition](../skills/camtasia-project/references/matte-composition.md). |
| Pending | Linked/placeholder hotspot owners and additional scene/marker clocks. | [#9](https://github.com/jbaruch/agentic-camtasia/issues/9), [hotspot owners](../skills/camtasia-project/references/hotspot-recording-owners.md). |
| Deferred | Linked/audio/placeholder quiz owners, additional scene clocks and feedback destinations. Operator deferred quizzes on 2026-11-07; skip this work for 1.0. | [#10](https://github.com/jbaruch/agentic-camtasia/issues/10), [quiz owners](../skills/camtasia-project/references/quiz-recording-owners.md). |
| Deferred | Remaining quiz-specific SCORM edition resume and interrupted/rejected-save/restart/cancel paths. Skip with the operator's quiz deferral. | [#11](https://github.com/jbaruch/agentic-camtasia/issues/11), [SCORM runtime](../skills/camtasia-project/references/advanced-features.md#suspending-and-resuming-a-quiz-session). |
| Pending | General portable packing, physical fonts and internal/installation render-resource closure beyond existing SVG/Lottie image support. | [#12](https://github.com/jbaruch/agentic-camtasia/issues/12), [media](../skills/camtasia-project/references/media.md), [Lottie](../skills/camtasia-project/references/lottie.md), [SVG](../skills/camtasia-project/references/svg-images.md). |
| Pending | Rev/Zoom/cloud import routes. | [#13](https://github.com/jbaruch/agentic-camtasia/issues/13), [integrations](../skills/camtasia-project/references/advanced-features.md#companion-apps-and-connected-imports). |
| Deferred | Audiate and Snagit companion handoffs. Operator deferred both on 2026-11-07; skip this work for 1.0. | [#13](https://github.com/jbaruch/agentic-camtasia/issues/13), [integrations](../skills/camtasia-project/references/advanced-features.md#companion-apps-and-connected-imports). |
| Pending | Remaining Library lifecycle operations, including permanent deletion, root/ancestor return and modifier/multiple-selection moves. | [#14](https://github.com/jbaruch/agentic-camtasia/issues/14), [Library](../skills/camtasia-project/references/library.md). |

## Caption completion tasks

The caption family remains pending. Its next concrete operations are:

- Capture and exercise block-transition selection and reversal. Existing
  transition-duration editing does not establish these separate controls.
- Exercise dynamic-caption alignment, wrapping, outline placement, sizing and
  ligature controls through the existing annotation route. A file-level probe
  preserves unrelated data and passes structural validation; native caption
  save/reopen and output remain unverified. Reuse that route where its native
  results hold rather than adding a duplicate caption interface.
- Capture remaining line-spacing and rich-style operations. The current native
  placeholder has partial rich ranges; a uniform annotation-rich edit refuses
  that specimen. Preserve its word binding and ranges when establishing the
  remaining editing contract.
- Inventory the other RTF representations against the existing caption-text
  contract, obtain concrete native/imported specimens and implement or exercise
  their remaining operations. Text-only Cocoa RTF support in 0.48.0 does not
  establish complex document content or every imported representation.

Keep unknown operations pending during this inventory. The
[caption reference](../skills/camtasia-project/references/captions.md) records
existing native observations and verification limits.

## Completion audit

- Expand each remaining family into the concrete operations its source contract
  identifies; keep unknown or unimplemented capabilities pending.
- Reuse completed native evidence. Verify each new representation or operation
  in its target build without repeating completed setting matrices.
- Retain deterministic coverage for shipped code and native save/reopen plus
  rendering, player or resource-closure checks appropriate to each operation.
- Verify required companion applications, licenses and accounts before their
  handoffs; prepare concrete disposable inputs before requesting missing access.
- Keep destructive native operations subject to action-time confirmation and
  independently verified recovery under their existing contracts.
- Record completion evidence and the published patch/minor release for each gap.
  A guard, an unsupported/unknown label, a closed issue or a passing narrow test
  alone does not complete a capability.
- Before 1.0.0, audit every active row against the current source, native evidence and
  actual published/installed behavior. Require all nondeferred work to be complete,
  current-head policy approval, passing CI and fresh installed-consumer checks.
- Retain the operator's explicit deferrals as exclusions, not completed capabilities.
- Publish and verify 1.0.0 only after that audit passes. Preserve its source-bound
  tag, publisher and retrievable-asset checks through final cleanup.
