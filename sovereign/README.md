SOVEREIGN scaffold (hospital corridor nav v0.1)
Spec defines a deterministic validation contract for one autonomy run.
Sim Run consumes the spec and emits run metadata plus placeholder traces.
Adversary Suite expands configured stress events for evaluation context.
ARS computes per-step aggregate quality scores from state components.
Traces/Artifacts are written to `artifacts/` for reproducibility and audit.
Workflow: Spec → Sim Run → Adversary Suite → ARS → Traces/Artifacts.
Robot is the subject under test in the corridor scenario.
SOVEREIGN is the test harness that evaluates and reports outcomes.
No training/RL or simulator-specific integration is included in this scaffold.
