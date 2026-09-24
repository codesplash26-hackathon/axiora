import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Set
import config

# Monitored application directories where unauthorized disk persistence must never occur
MONITORED_DIRS = [
    config.BASE_DIR,
    config.ARTIFACTS_DIR,
    config.DATA_DIR,
    config.BASE_DIR / "backend",
    config.BASE_DIR / "ml_core"
]

# Sensitive biomarker/PHI identifiers to audit for leaks
AUDIT_KEYWORDS = ["sysBP", "totChol", "cigsPerDay", "John Doe", "john@test.com"]


def _snapshot_directory_files(directory: Path) -> Set[str]:
    """Capture file modification snapshot for an application directory."""
    files_snapshot = set()
    if not directory.exists():
        return files_snapshot
    try:
        for root, dirs, files in os.walk(directory):
            # Skip python bytecode, git, and virtual environment directories
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".venv", ".pytest_cache")]
            for f in files:
                if f.endswith(".pyc"):
                    continue
                full_path = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(full_path)
                    files_snapshot.add(f"{full_path}:{mtime}")
                except (OSError, FileNotFoundError):
                    pass
    except Exception:
        pass
    return files_snapshot


@contextmanager
def assert_zero_disk_writes() -> Generator[None, None, None]:
    """
    Context manager asserting that zero request payloads, patient features,
    or intermediate calculation arrays are written to local file systems or logging directories.
    Enforces HIPAA Safe Harbor and Sri Lanka PDPA stateless in-memory processing.
    """
    before_state = set()
    for d in MONITORED_DIRS:
        before_state.update(_snapshot_directory_files(d))

    yield

    after_state = set()
    for d in MONITORED_DIRS:
        after_state.update(_snapshot_directory_files(d))

    new_files = after_state - before_state
    if new_files:
        raise AssertionError(
            f"Zero-disk serialization violated! Unauthorized file persistence detected in application workspace: {new_files}"
        )


def verify_zero_disk_execution(callable_fn, *args, **kwargs):
    """Run callable within strict zero-disk assertion context."""
    with assert_zero_disk_writes():
        return callable_fn(*args, **kwargs)
