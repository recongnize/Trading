"""多项目管理：保存各币种的配置与分析结果，支持快速切换。"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProjectState:
    """单个项目的状态。"""

    name: str
    data_source: str = "binance"
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    exchange: str = "自动"
    reasoning_text: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "data_source": self.data_source,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "exchange": self.exchange,
            "reasoning_text": self.reasoning_text,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ProjectState":
        return cls(
            name=d.get("name", "未命名"),
            data_source=d.get("data_source", "binance"),
            symbol=d.get("symbol", "BTCUSDT"),
            timeframe=d.get("timeframe", "1h"),
            exchange=d.get("exchange", "自动"),
            reasoning_text=d.get("reasoning_text", ""),
            created_at=d.get("created_at", time.time()),
            updated_at=d.get("updated_at", time.time()),
        )


class ProjectManager:
    """管理多个项目的增删改查与持久化。"""

    def __init__(self, storage_path: str) -> None:
        self._storage_path = storage_path
        self._projects: list[ProjectState] = []
        self._active_name: str | None = None
        self._load()

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not os.path.exists(self._storage_path):
            self._projects = []
            return
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._projects = [ProjectState.from_dict(p) for p in data.get("projects", [])]
            self._active_name = data.get("active_name")
            if not self._projects and self._active_name:
                self._active_name = None
        except Exception:
            self._projects = []
            self._active_name = None

    def save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            data = {
                "projects": [p.to_dict() for p in self._projects],
                "active_name": self._active_name,
            }
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── CRUD ───────────────────────────────────────────────────────────────────

    @property
    def projects(self) -> list[ProjectState]:
        return list(self._projects)

    @property
    def active_name(self) -> str | None:
        return self._active_name

    @property
    def active_project(self) -> ProjectState | None:
        if self._active_name is None:
            return None
        for p in self._projects:
            if p.name == self._active_name:
                return p
        return None

    def set_active(self, name: str) -> None:
        for p in self._projects:
            if p.name == name:
                self._active_name = name
                self.save()
                return

    def add_project(self, project: ProjectState) -> None:
        # 重名处理
        base = project.name
        i = 2
        names = {p.name for p in self._projects}
        while project.name in names:
            project.name = f"{base} ({i})"
            i += 1
        self._projects.append(project)
        self._active_name = project.name
        self.save()

    def remove_project(self, name: str) -> None:
        self._projects = [p for p in self._projects if p.name != name]
        if self._active_name == name:
            self._active_name = self._projects[0].name if self._projects else None
        self.save()

    def rename_project(self, old_name: str, new_name: str) -> None:
        for p in self._projects:
            if p.name == old_name:
                p.name = new_name
                p.updated_at = time.time()
                if self._active_name == old_name:
                    self._active_name = new_name
                break
        self.save()

    def update_project(
        self,
        name: str,
        *,
        data_source: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
        exchange: str | None = None,
        reasoning_text: str | None = None,
    ) -> None:
        for p in self._projects:
            if p.name == name:
                if data_source is not None:
                    p.data_source = data_source
                if symbol is not None:
                    p.symbol = symbol
                if timeframe is not None:
                    p.timeframe = timeframe
                if exchange is not None:
                    p.exchange = exchange
                if reasoning_text is not None:
                    p.reasoning_text = reasoning_text
                p.updated_at = time.time()
                break
        self.save()
