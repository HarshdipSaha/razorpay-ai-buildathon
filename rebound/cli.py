from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from rebound.audit.log import AuditLog
from rebound.ingest.store import EventStore
from rebound.policy.gate import PolicyGate
from rebound.sim.clock import SimClock, RealClock
from rebound.sim.fake_razorpay import SimulatedRazorpayClient
from rebound.sim.scenarios import generate_scenarios
from rebound.sim.batch import run_batch
from rebound.sim.report import build_report, render_markdown
from rebound.sim.report_html import render_html
from rebound.pipeline import PipelineContext

DATA_DIR = Path(".rebound_data")


def _make_context(clock, simulate_razorpay: bool = False) -> PipelineContext:
    DATA_DIR.mkdir(exist_ok=True)
    executor_client = None
    llm_client = None

    if simulate_razorpay:
        # `demo`/batch mode: no Razorpay login or API keys required, ever.
        executor_client = SimulatedRazorpayClient()
    elif os.environ.get("RAZORPAY_KEY_ID"):
        import razorpay
        executor_client = razorpay.Client(auth=(os.environ["RAZORPAY_KEY_ID"], os.environ["RAZORPAY_KEY_SECRET"]))

    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        llm_client = anthropic.Anthropic()

    return PipelineContext(
        store=EventStore(DATA_DIR / "events.db"),
        audit=AuditLog(DATA_DIR / "audit.jsonl"),
        gate=PolicyGate.from_yaml(Path(__file__).parent / "policy" / "policy.yaml"),
        executor_client=executor_client,
        llm_client=llm_client,
        clock=clock,
        llm_cache_dir=str(DATA_DIR / "llm_cache"),
    )


def cmd_demo(args: argparse.Namespace) -> None:
    # Fresh state each run so the demo is reproducible from a clean clone.
    for f in ("events.db", "audit.jsonl"):
        p = DATA_DIR / f
        if p.exists():
            p.unlink()
    ctx = _make_context(SimClock(0.0), simulate_razorpay=True)
    recorded_dir = Path("fixtures/recorded")
    scenarios = generate_scenarios(seed=42, n=60,
                                    recorded_dir=recorded_dir if recorded_dir.exists() else None)
    results = run_batch(ctx, scenarios)
    report = build_report(results)
    Path("report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    Path("report.md").write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    print(f"\nOK: audit chain valid = {ctx.audit.verify()}")


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn
    from rebound.ingest.webhook import create_app
    ctx = _make_context(RealClock())
    app = create_app(db_path=DATA_DIR / "events.db", ctx=ctx)
    uvicorn.run(app, host="0.0.0.0", port=args.port)


def cmd_verify_audit(args: argparse.Namespace) -> None:
    log = AuditLog(DATA_DIR / "audit.jsonl")
    if log.verify():
        print("OK: audit chain is valid")
        sys.exit(0)
    else:
        print(f"FAIL: chain broken at seq {log.first_break()}")
        sys.exit(1)


def _read_audit_records() -> list[dict]:
    path = DATA_DIR / "audit.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def cmd_report(args: argparse.Namespace) -> None:
    report = json.loads(Path("report.json").read_text(encoding="utf-8"))
    if args.html:
        Path("report.html").write_text(render_html(report, audit_records=_read_audit_records()), encoding="utf-8")
        print("wrote report.html")
    else:
        print(render_markdown(report))


def main() -> None:
    # Windows terminals often default stdout to cp1252, which can't encode the
    # arrows/middot in the report text — force utf-8 so `rebound demo`/`report`
    # print cleanly on any platform without changing the report content itself.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    load_dotenv()
    parser = argparse.ArgumentParser(prog="rebound")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo").set_defaults(func=cmd_demo)

    p_serve = sub.add_parser("serve")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.set_defaults(func=cmd_serve)

    sub.add_parser("verify-audit").set_defaults(func=cmd_verify_audit)

    p_report = sub.add_parser("report")
    p_report.add_argument("--html", action="store_true")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
