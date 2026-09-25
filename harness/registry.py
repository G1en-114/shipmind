"""Skill 注册表：扫描 skills-src/*/SKILL.md 的 frontmatter。零第三方依赖。

frontmatter 约定字段：
  name / description / version        —— 基本信息
  triggers                            —— 逗号分隔的触发词（正例）
  entry                               —— scripts/ 下入口脚本相对路径；
                                         缺失或文件不存在 → 该 Skill 视为 planned（未实现）
"""
from __future__ import annotations

import json
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
    negative: list[str] = field(default_factory=list)  # 负触发词：命中时应避开本 Skill
    origin: str = "self"          # self=自研 / official=NVIDIA 官方
    executable: bool = False      # 官方 Skill 是否有可执行入口

    @property
    def status(self) -> str:
        if self.origin == "official":
            return "official-exec" if self.executable else "official-advisory"
        return "ready" if self.entry else "planned"

    def keywords(self) -> list[str]:
        """触发词 + description 词元，供路由打分。

        中文按 bigram 切分（与 rag_query 一致）：整段中文作为一个关键词永远
        匹配不上查询，会导致大脑不可用时关键词兜底失效（实测踩过）。
        """
        kws = list(self.triggers)
        for run in re.findall(r"[A-Za-z0-9\-]{2,}", self.description):
            kws.append(run)
        for run in re.findall(r"[一-鿿]{2,}", self.description):
            if len(run) == 2:
                kws.append(run)
            else:
                kws.extend(run[i:i + 2] for i in range(len(run) - 1))
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


def load_official_skills() -> list[SkillEntry]:
    """从 official-skills/manifest.json 加载官方 NVIDIA Skill（vendored 于仓库内）。"""
    manifest = REPO_ROOT / "official-skills" / "manifest.json"
    if not manifest.exists():
        return []
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    installed = REPO_ROOT / "official-skills" / "installed"
    out = []
    for s in data.get("skills", []):
        d = installed / s["name"]
        if not (d / "SKILL.md").exists():
            continue
        out.append(SkillEntry(
            name=s["name"],
            description=s.get("description", ""),
            triggers=[t for t in s.get("description", "").replace("：", " ").split()
                      if len(t) >= 3][:6],
            dir=d,
            entry=(d / s["entry"]) if s.get("executable") and s.get("entry") else None,
            origin="official",
            executable=bool(s.get("executable")),
        ))
    return out


def load_skills(skills_dir: Path | None = None,
                include_official: bool = True) -> list[SkillEntry]:
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
        negative = [
            t.strip()
            for t in fm.get("negative-triggers", "").replace("，", ",").split(",")
            if t.strip()
        ]
        skills.append(SkillEntry(
            name=fm.get("name", d.name),
            description=fm.get("description", ""),
            triggers=triggers, negative=negative,
            dir=d, entry=entry,
        ))
    if include_official:
        skills.extend(load_official_skills())
    return skills
