# AI-DLC — AI-Driven Development Lifecycle

This project is built end-to-end with the **AI-DLC** methodology: an iterative, effort-tracked way of doing LLM-augmented software work where the *process* is as inspectable as the code.

Two moves carry it:

| Move | Runs | Produces |
|---|---|---|
| **Inception** | once per project | the baseline — requirements, architecture, components, stack — under `inception/` |
| **Effort** | every change after that | a numbered folder `efforts/{NNN}-{ref}/` with its own `effort-state.md`, `requirements-delta.md`, and artifacts |

The baseline is the north star; efforts iterate against it. Inception is re-run only if the baseline itself changes.

## Layout

```
aidlc-docs/
├── README.md                 ← this file
├── registry.md               ← DERIVED view of all efforts (rebuilt from effort-state.md files)
├── audit.md                  ← every approval-gate response and scope decision, in order
├── process-log.md            ← chronological log of every AI skill / tool used to build this
├── inception/
│   ├── 00-workspace-detection.md
│   ├── 01-requirements.md    (after idea selection)
│   └── 02-application-design.md
└── efforts/
    └── 001-.../
        ├── effort-state.md
        ├── requirements-delta.md
        └── ...
```

## Conventions in force

- **Depth dial:** `standard` — chosen because the buildathon deadline is 5 Sept 2026; `comprehensive` traceability would cost build time. Rigor, not which stages run.
- **Approval gates:** 2-option prompt (*Request changes* / *Continue*) after each inception artifact stage and each effort plan. Every response is recorded in `audit.md`.
- **Registry is derived:** `registry.md` is rebuilt from the per-effort state files; the filesystem is the source of truth.
- **Effort state machine:** `planning → awaiting-approval → in-progress → complete` (+ `blocked`, `failed`, `abandoned`). Re-running an effort resumes; completed stages are never silently overwritten.
- **Subagent orchestration:** where an effort decomposes into independent units, they are delegated to parallel subagents (the `agent-swarm` peer-parallel pattern). Which pattern was used is recorded in the effort state.

## Why this is here

The Razorpay AI Buildathon judges on *problem taste, build quality, AI judgment, and failure recovery* — and reads "what broke and how you got out" first. AI-DLC makes all four legible: the requirements say why the problem matters, the effort trail shows how it was built, `process-log.md` shows exactly where AI was used (and where it deliberately was not), and `audit.md` records every course-correction.
