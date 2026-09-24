import os
import tempfile
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Set

# Monitored directories where unauthorized disk persistence might occur
MONITORED_DIRS = [
    Path(tempfile.gettempdir()),
    Path(__file__).resolve().parent.parent / "artifacts",
    Path(__file__).resolve().parent.parent / "data"
]


def _snapshot_directory_files(directory: Path) -> Set[str]:
    """Capture file modification snapshot for a directory."""
    files_snapshot = set()
    if not directory.exists():
        return files_snapshot
    try:
        for root, _, files in os.walk(directory):
            for f in files:
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
    Context manager asserting that zero new files or disk mutations occur
    during the execution of an inbound request or ML inference pass.
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
            f"Zero-disk serialization violated! Unauthorized file creation or modification detected: {new_files}"
        )


def verify_zero_disk_execution(callable_fn, *args, **kwargs):
    """Run callable within strict zero-disk assertion context."""
    with assert_zero_disk_writes():
        return callable_fn(*args, **kwargs)
