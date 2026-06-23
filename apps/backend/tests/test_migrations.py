import importlib.util
from pathlib import Path


def test_initial_migration_imports() -> None:
    """The initial migration must import cleanly (catches syntax/import errors)."""
    path = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "versions"
        / "0001_initial_schema.py"
    )
    spec = importlib.util.spec_from_file_location("migration_0001", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "0001_initial"
    assert callable(module.upgrade)
    assert callable(module.downgrade)
    assert "lead_assignments" in module.TENANT_SCOPED_TABLES
