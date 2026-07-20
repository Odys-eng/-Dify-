from pathlib import Path

import pytest

from ruyi_docx.adapters.mcp import PathPolicy
from ruyi_docx.errors import UnsafePathError


def test_path_policy_allows_paths_below_root(tmp_path: Path) -> None:
    policy = PathPolicy(tmp_path)

    assert policy.resolve("reports/result.docx") == (tmp_path / "reports" / "result.docx").resolve()


def test_path_policy_rejects_traversal(tmp_path: Path) -> None:
    policy = PathPolicy(tmp_path)

    with pytest.raises(UnsafePathError):
        policy.resolve("../outside.docx")
