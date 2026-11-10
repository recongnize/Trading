"""5-step horizontal flow indicator — dark tech glass style with pulse glow."""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtProperty
from PyQt6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


# ── Color palette ──────────────────────────────────────────────────────────
_CYAN = QColor(56, 189, 248)        # #38bdf8 active cyan
_CYAN_BRIGHT = QColor(125, 211, 252) # #7dd3fc
_CYAN_DIM = QColor(56, 189, 248, 40) # rgba glow
_GRAY_NODE = QColor(71, 85, 105)     # #475569 inactive
_GRAY_LINE = QColor(100, 116, 139, 50)
_DONE_GREEN = QColor(34, 197, 94)    # #22c55e
_ERROR_RED = QColor(239, 68, 68)     # #ef4444

_DEFAULT_NAMES = ["数据", "快照", "诊断", "决策", "追问"]
_DEFAULT_CAPTIONS = ["等待连接", "未获取", "等待阶段一", "等待阶段二", "等待完成"]


class _PulseDot(QWidget):
    """Single node: pulsing dot + labels + auto-paint of pulse rings."""

    def __init__(self, name: str, caption: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._name_text = name
        self._caption_text = caption
        self._status = "idle"       # idle | done | active | error
        self._pulse_phase = 0.0     # 0.0 → 1.0, cycling

        self.setMinimumHeight(56)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Labels
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        layout.addStretch(1)

        self._name_label = QLabel(name)
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #e2e8f0; background: transparent;")
        layout.addWidget(self._name_label)

        self._caption_label = QLabel(caption)
        self._caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._caption_label.setStyleSheet("font-size: 10px; color: #64748b; background: transparent;")
        layout.addWidget(self._caption_label)
        layout.addStretch(1)

    # ── status ────────────────────────────────────────────────────────────
    def set_status(self, status: str) -> None:
        self._status = status
        self._update_label_colors()
        self.update()

    def set_caption(self, text: str) -> None:
        self._caption_text = text
        self._caption_label.setText(text)

    def _update_label_colors(self) -> None:
        if self._status == "active":
            self._name_label.setStyleSheet(
                "font-size: 12px; font-weight: 600; color: #7dd3fc; background: transparent;"
            )
        elif self._status == "done":
            self._name_label.setStyleSheet(
                "font-size: 12px; font-weight: 600; color: #86efac; background: transparent;"
            )
        elif self._status == "error":
            self._name_label.setStyleSheet(
                "font-size: 12px; font-weight: 600; color: #fca5a5; background: transparent;"
            )
        else:
            self._name_label.setStyleSheet(
                "font-size: 12px; font-weight: 600; color: #94a3b8; background: transparent;"
            )

    # ── paintEvent: draw dot + pulse rings ────────────────────────────────
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx = w / 2
        cy = 16  # dot center Y (compact)

        # Status → colors
        status_colors = {
            "idle":   (_GRAY_NODE, QColor(0, 0, 0, 0)),
            "active": (_CYAN, _CYAN_DIM),
            "done":   (_DONE_GREEN, QColor(34, 197, 94, 40)),
            "error":  (_ERROR_RED, QColor(239, 68, 68, 40)),
        }
        dot_color, glow_color = status_colors.get(self._status, status_colors["idle"])

        # ── Pulse rings (only active status) ──────────────────────────────
        if self._status == "active":
            for offset in (0.0, 0.33, 0.67):
                phase = (self._pulse_phase + offset) % 1.0
                ring_r = 7 + phase * 14   # grow 7 → 21 (compact)
                alpha = int(220 * (1.0 - phase))
                ring_color = QColor(_CYAN.red(), _CYAN.green(), _CYAN.blue(), alpha)
                pen = QPen(ring_color, 1.2)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                rect = QRectF(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2)
                painter.drawEllipse(rect)

        # ── Center dot ──────────────────────────────────────────────────
        dot_r = 4.5
        if self._status in ("active", "done", "error"):
            grad = QRadialGradient(cx, cy, dot_r * 3.0)
            grad.setColorAt(0, glow_color.lighter(150))
            grad.setColorAt(0.4, glow_color)
            grad.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(grad)
            painter.drawEllipse(QPointF(cx, cy), dot_r * 3.0, dot_r * 3.0)

        # Solid dot
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(dot_color)
        painter.drawEllipse(QPointF(cx, cy), dot_r, dot_r)

        # Inner highlight
        hilite = QColor(255, 255, 255, 80) if self._status == "active" else QColor(255, 255, 255, 40)
        painter.setBrush(hilite)
        painter.drawEllipse(QPointF(cx - 1.5, cy - 1.5), 2, 2)


class FlowBar(QWidget):
    """5-step horizontal flow indicator with pulse animation."""

    PULSE_INTERVAL_MS = 40  # 25 FPS → phase advances 0.04 each frame at 1s period

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("flowBar")
        self.setMinimumHeight(62)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._phase = 0.0
        self._steps: list[_PulseDot] = []
        self._active_index = -1

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(0)

        for name, caption in zip(_DEFAULT_NAMES, _DEFAULT_CAPTIONS, strict=True):
            step = _PulseDot(name, caption)
            layout.addWidget(step, stretch=1)
            self._steps.append(step)

        # Pulse timer (50ms = 20 FPS — smooth enough for pulse, lighter on CPU)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)
        self._timer.stop()  # 初始 idle 状态，有 active 节点时再启动

    def _tick(self) -> None:
        self._phase = (self._phase + 0.05) % 1.0
        for s in self._steps:
            if s._status == "active":
                s._pulse_phase = self._phase
        # 只触发一次整体重绘 — FlowBar 的 paintEvent 画连接线，
        # 子节点 _PulseDot 会被 Qt 自动 repaint（如果它们自身设置了 WA_NeedUpdate）
        self.update()

    # ── Public API (unchanged signatures) ──────────────────────────────────
    def set_step_status(self, index: int, status: str) -> None:
        if 0 <= index < len(self._steps):
            self._steps[index].set_status(status)
            if status == "active":
                self._active_index = index
                if not self._timer.isActive():
                    self._timer.start()
            elif status != "active" and self._active_index == index:
                self._active_index = -1
                # 没有 active 节点了 → 停 timer 省 CPU
                if not any(s._status == "active" for s in self._steps):
                    self._timer.stop()
            self.update()

    def set_step_caption(self, index: int, text: str) -> None:
        if 0 <= index < len(self._steps):
            self._steps[index].set_caption(text)

    def reset_all(self) -> None:
        self._active_index = -1
        self._timer.stop()  # 重置后立即停掉动画
        for step, caption in zip(self._steps, _DEFAULT_CAPTIONS, strict=True):
            step.set_status("idle")
            step.set_caption(caption)
        self.update()

    # ── paintEvent: connecting lines ───────────────────────────────────────
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if len(self._steps) < 2:
            return

        line_y = 16  # same as dot center Y in _PulseDot

        for i in range(len(self._steps) - 1):
            left_step = self._steps[i]
            right_step = self._steps[i + 1]

            left_center = left_step.geometry().center().x()
            right_center = right_step.geometry().center().x()

            # 点亮规则：线段的右端节点是 active 或 done → 点亮
            # 这样激活节点只会点亮它"之前"的线段，不会点亮到下一个节点
            right_status = right_step._status
            lit = right_status in ("active", "done")

            if lit:
                # Gradient cyan line with glow
                grad = QLinearGradient(left_center, line_y, right_center, line_y)
                grad.setColorAt(0, _CYAN_BRIGHT)
                grad.setColorAt(1, _CYAN)
                pen = QPen(QColor(56, 189, 248, 200), 2.0)
                painter.setPen(pen)
                # Glow under-layer
                glow_pen = QPen(QColor(56, 189, 248, 60), 5.0)
                painter.setPen(glow_pen)
                painter.drawLine(QPointF(left_center, line_y), QPointF(right_center, line_y))
                # Main line
                painter.setPen(pen)
                painter.drawLine(QPointF(left_center, line_y), QPointF(right_center, line_y))
            else:
                pen = QPen(_GRAY_LINE, 1.5)
                painter.setPen(pen)
                painter.drawLine(QPointF(left_center, line_y), QPointF(right_center, line_y))
