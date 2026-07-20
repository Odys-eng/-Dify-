from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_generator() -> ModuleType:
    script = Path(__file__).parents[3] / "examples" / "北科大2026" / "12_生成零基础Dify入门.py"
    spec = importlib.util.spec_from_file_location("zero_based_dify_generator", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def test_existing_navigation_still_updates_review_time(tmp_path: Path) -> None:
    generator = _load_generator()
    relative_md = "06-learning-resources/零基础 Dify 入门.md"
    reviewed_at = "2026-07-18T20:00:00+08:00"
    (tmp_path / "manifest.yaml").write_text(
        f"latest_reviewed_at: 2026-07-18T12:00:00+08:00\n  zero_based_dify: {relative_md}\n",
        encoding="utf-8",
    )
    navigation_dir = tmp_path / "00-navigation"
    navigation_dir.mkdir()
    (navigation_dir / "index.md").write_text(
        f"| 零基础 Dify 入门 | `{relative_md}` | 示例 |\n",
        encoding="utf-8",
    )

    generator.update_library_indexes(tmp_path, relative_md, reviewed_at)

    manifest = (tmp_path / "manifest.yaml").read_text(encoding="utf-8")
    assert f"latest_reviewed_at: {reviewed_at}" in manifest
