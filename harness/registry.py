"""Skill 注册表：扫描 skills-src/*/SKILL.md 的 frontmatter。零第三方依赖。

frontmatter 约定字段：
  name / description / version        —— 基本信息
  triggers                            —— 逗号分隔的触发词（正例）
  entry                               —— scripts/ 下入口脚本相对路径；
                                         缺失或文件不存在 → 该 Skill 视为 planned（未实现）
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills-src"


@dataclass
class SkillEntry:
    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    dir: Path | None = None
    entry: Path | None = None

    @property
    def status(self) -> str:
        return "ready" if self.entry else "planned"

    def keywords(self) -> list[str]:
        """触发词 + description 中的中日韩/拉丁词块，供路由打分。"""
        kws = list(self.triggers)
        for run in re.findall(r"[\u4e00-\u9fffA-Za-z0-9\-]{2,}", self.description):
            kws.append(run)
        return sorted({k.lower() for k in kws if len(k) >= 2})


def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    fm: dict[str, str] = {}
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm


def load_skills(skills_dir: Path | None = None) -> list[SkillEntry]:
    root = skills_dir or SKILLS_DIR
    skills = []
    for d in sorted(root.iterdir()) if root.exists() else []:
        sk = d / "SKILL.md"
        if not sk.exists():
            continue
        fm = _parse_frontmatter(sk.read_text(encoding="utf-8"))
        entry_rel = fm.get("entry")
        entry = d / entry_rel if entry_rel else None
        if entry is not None and not entry.exists():
            entry = None
        triggers = [
            t.strip()
            for t in fm.get("triggers", "").replace("，", ",").split(",")
            if t.strip()
        ]
        skills.append(SkillEntry(
            name=fm.get("name", d.name),
            description=fm.get("description", ""),
            triggers=triggers,
            dir=d,
            entry=entry,
        ))
    return skills
