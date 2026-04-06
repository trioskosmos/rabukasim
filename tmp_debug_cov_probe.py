from pathlib import Path
import os
import subprocess
import tempfile
import scripts.reports.generate_rust_ability_test_coverage as s

print('probe:start', flush=True)
print('probe:module_loaded', flush=True)

print('probe:before_single_test', flush=True)
trace_path = Path('tmp_runtime_trace.jsonl')
trace_path.unlink(missing_ok=True)
with tempfile.TemporaryDirectory(prefix='cov_probe_ps_') as tmp_dir:
    stdout_path = Path(tmp_dir) / 'stdout.txt'
    stderr_path = Path(tmp_dir) / 'stderr.txt'
    ps_command = (
        '[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; '
        f'$env:RUST_ABILITY_COVERAGE_OUT="{trace_path}"; '
        f'cargo test --manifest-path "{s.CARGO_MANIFEST_PATH}" '
        'test_suite::qa::batch_card_specific::tests::test_card_672_private_wars_second_mode_only_targets_opponent_with_three_or_less_blades '
        '-- --exact --nocapture '
        f'2>&1 | Out-File -FilePath "{stdout_path}" -Encoding utf8'
    )
    print(ps_command, flush=True)
    completed = subprocess.run(
        ['powershell.exe', '-NoProfile', '-Command', ps_command],
        cwd=s.ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=180,
    )
    stdout_text = stdout_path.read_text(encoding='utf-8', errors='replace') if stdout_path.exists() else ''
    print('probe:returncode', completed.returncode, flush=True)
    print('probe:stdout_tail', stdout_text[-500:], flush=True)
    print('probe:event_count', len(s.read_runtime_trace(trace_path)), flush=True)
trace_path.unlink(missing_ok=True)
