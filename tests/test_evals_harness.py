"""
Tests for the evals harness itself (Issue #13) -- always `--dry-run`, so this
file costs zero API tokens and runs in the normal pytest/CI gate.
"""

from evals import run_evals


def test_deterministic_case_passes_in_dry_run():
    result = run_evals.run_deterministic_case(run_evals.DEFAULT_AGENT_MODEL, dry_run=True)
    assert result.passed
    assert "read_file" in result.detail


def test_probabilistic_case_passes_in_dry_run():
    result = run_evals.run_probabilistic_case(
        run_evals.DEFAULT_AGENT_MODEL, run_evals.DEFAULT_JUDGE_MODEL, dry_run=True
    )
    assert result.passed


def test_judge_fails_on_speaker_header_violation():
    verdict = run_evals._judge("## Claude\n\nhi there", "fake-judge", dry_run=True)
    assert verdict == "FAIL"


def test_judge_fails_on_unjustified_consensus():
    verdict = run_evals._judge("All good, STATUS: CONSENSUS", "fake-judge", dry_run=True)
    assert verdict == "FAIL"


def test_judge_passes_clean_reply():
    verdict = run_evals._judge("Looks fine to me, no objections.", "fake-judge", dry_run=True)
    assert verdict == "PASS"


def test_main_dry_run_exits_zero_on_success(capsys):
    exit_code = run_evals.main(["--dry-run"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "[PASS] deterministic_tool_call" in out
    assert "[PASS] probabilistic_protocol_check" in out


def test_main_dry_run_case_filter_runs_only_requested_case(capsys):
    exit_code = run_evals.main(["--dry-run", "--case", "deterministic"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "deterministic_tool_call" in out
    assert "probabilistic_protocol_check" not in out


def test_main_real_mode_prints_cost_warning(capsys, monkeypatch):
    """Without --dry-run, main() must warn before spending real API tokens.
    We don't actually call the API: that's the job of run_*_case, which are
    covered above with dry_run=True; here we only assert the warning fires
    before any case executes, by making both cases a no-op."""
    monkeypatch.setattr(run_evals, "run_deterministic_case", lambda model, dry_run: run_evals.EvalResult("x", True))
    monkeypatch.setattr(
        run_evals, "run_probabilistic_case", lambda model, judge_model, dry_run: run_evals.EvalResult("y", True)
    )
    run_evals.main([])
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "real API" in err
