"""5-metric summary card strip — glass-morphism dark tech style."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


_DEFAULT_METRICS = [
    ("当前趋势", "—", "📈"),
    ("当前市场周期", "—", "🌀"),
    ("下一个市场周期", "—", "🔮"),
    ("支撑区", "—", "🛡️"),
    ("阻力区", "—", "🎯"),
]

_FONT_MONO = '"JetBrains Mono", "Cascadia Mono", "Consolas", "Microsoft YaHei UI", monospace'

# Icon fallback (emoji → unicode-safe label, override if QFontMetrics fails)
_ICON_MAP: dict[str, str] = {}  # icon char → itself, rendered natively


class _MetricCard(QFrame):
    """Single glass-morphism metric card."""

    _BASE_SS = (
        "QFrame {"
        "  background-color: rgba(30, 41, 59, 0.55);"
        "  border: 1px solid rgba(71, 85, 105, 0.30);"
        "  border-radius: 10px;"
        "}"
        "QFrame:hover {"
        "  border-color: rgba(56, 189, 248, 0.40);"
        "  background-color: rgba(30, 41, 59, 0.75);"
        "}"
    )

    def __init__(
        self,
        title: str,
        value: str = "—",
        icon: str = "",
        *,
        primary: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setMinimumWidth(0)
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(self._BASE_SS)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 5, 10, 5)
        outer.setSpacing(6)

        # Icon badge
        if icon:
            icon_label = QLabel(icon)
            icon_label.setFixedSize(22, 22)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet(
                "font-size: 12px; "
                "background-color: rgba(56, 189, 248, 0.10); "
                "border: 1px solid rgba(56, 189, 248, 0.25); "
                "border-radius: 6px;"
            )
            outer.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignVCenter)

        # Text column
        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)

        self._title = QLabel(title)
        self._title.setStyleSheet("font-size: 10px; color: #64748b; letter-spacing: 0.3px;")
        self._title.setWordWrap(False)
        text_col.addWidget(self._title)

        self._value = QLabel(value)
        self._value.setWordWrap(True)
        self._value.setMinimumWidth(0)
        self._value.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
        if primary:
            self._value.setStyleSheet(
                f"font-size: 12px; font-weight: 600; color: #86efac; font-family: {_FONT_MONO};"
            )
        else:
            self._value.setStyleSheet(
                f"font-size: 11px; font-weight: 600; color: #cbd5e1; font-family: {_FONT_MONO};"
            )
        text_col.addWidget(self._value)

        outer.addLayout(text_col, stretch=1)

    def set_value(self, text: str) -> None:
        self._value.setText(text)


class SummaryStrip(QWidget):
    """Responsive strip of five glass-morphism metric cards."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("summaryStrip")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setStyleSheet(
            "background-color: transparent;"
        )

        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(8, 0, 8, 4)
        self._layout.setHorizontalSpacing(8)
        self._layout.setVerticalSpacing(4)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._cards: list[_MetricCard] = []
        for idx, (title, value, icon) in enumerate(_DEFAULT_METRICS):
            card = _MetricCard(title, value, icon, primary=(idx == 0))
            self._cards.append(card)
        self._columns = 0
        self._relayout()

    def set_metrics(self, metrics: dict[str, str]) -> None:
        for card in self._cards:
            title = card._title.text()
            if title in metrics:
                card.set_value(metrics[title])

    def reset(self) -> None:
        for card in self._cards:
            card.set_value("—")

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._relayout()

    def _target_columns(self) -> int:
        return 5

    def _relayout(self) -> None:
        columns = self._target_columns()
        if columns == self._columns and self._layout.count() == len(self._cards):
            return
        self._columns = columns
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget() is not None:
                item.widget().setParent(None)
        for idx, card in enumerate(self._cards):
            row = idx // columns
            col = idx % columns
            self._layout.addWidget(card, row, col)
        for col in range(5):
            self._layout.setColumnStretch(col, 1 if col < columns else 0)
