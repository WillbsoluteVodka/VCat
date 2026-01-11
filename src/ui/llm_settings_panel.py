"""Sliding LLM settings panel for chat dialog."""

import asyncio
from typing import Callable, Dict, Optional

from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QFrame,
    QSpinBox,
    QDoubleSpinBox,
)

from src.llm.config import (
    load_llm_config,
    save_llm_config,
    set_default_provider,
    upsert_provider,
    remove_provider,
)
from src.llm.security import encrypt_api_key, decrypt_api_key
from src.llm.openai_provider import OpenAICompatibleProvider


class AsyncWorker(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, coro_factory: Callable):
        super().__init__()
        self._coro_factory = coro_factory

    def run(self):
        try:
            result = asyncio.run(self._coro_factory())
        except Exception as exc:
            self.error.emit(str(exc))
        else:
            self.result.emit(result)


class LLMSettingsPanel(QWidget):
    saved = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_llm_config()
        self._current_provider_name: Optional[str] = None
        self._worker_thread: Optional[QThread] = None
        self._worker: Optional[AsyncWorker] = None
        self._build_ui()
        self._load_config()

    def _build_ui(self):
        self.setObjectName("llmSettingsPanel")
        self.setStyleSheet(
            """
            QWidget#llmSettingsPanel {
                background-color: rgba(24, 24, 28, 240);
                border-left: 1px solid rgba(255, 255, 255, 30);
            }
            QLabel {
                color: #F8FAFC;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
                background-color: rgba(255, 255, 255, 18);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 8px;
                padding: 6px 8px;
                color: #F8FAFC;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
                border: 1px solid #F97316;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
                height: 0;
            }
            QTextEdit {
                min-height: 80px;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("LLM Settings / LLM 设置")
        title.setFont(QFont(".AppleSystemUIFont", 14, QFont.Medium))
        header.addWidget(title)
        header.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedHeight(28)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                color: #F8FAFC;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 8px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 35);
            }
            """
        )
        close_btn.clicked.connect(self._on_close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        layout.addWidget(self._section_title("Provider / 服务商"))
        layout.addWidget(self._build_provider_card())

        layout.addWidget(self._section_title("Generation / 生成"))
        layout.addWidget(self._build_generation_card())

        layout.addWidget(self._section_title("Personality / 人格"))
        layout.addWidget(self._build_personality_card())

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: rgba(248, 250, 252, 0.7);")
        layout.addWidget(self.status_label)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.models_btn = QPushButton("Fetch Models")
        self.models_btn.setCursor(Qt.PointingHandCursor)
        self.models_btn.setFixedHeight(32)
        self.models_btn.setStyleSheet(self._secondary_button_style())
        self.models_btn.clicked.connect(self._on_fetch_models)

        self.save_btn = QPushButton("Test & Save")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedHeight(32)
        self.save_btn.setStyleSheet(self._primary_button_style())
        self.save_btn.clicked.connect(self._on_save)

        button_row.addWidget(self.models_btn)
        button_row.addWidget(self.save_btn)
        layout.addLayout(button_row)

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setFont(QFont(".AppleSystemUIFont", 12, QFont.Medium))
        label.setStyleSheet("color: rgba(248, 250, 252, 0.75);")
        return label

    def _build_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            """
            QFrame {
                background-color: rgba(255, 255, 255, 10);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 12px;
            }
            """
        )
        return card

    def _build_provider_card(self) -> QFrame:
        card = self._build_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        selector_row = QHBoxLayout()
        selector_label = QLabel("Provider / 名称")
        selector_label.setFont(QFont(".AppleSystemUIFont", 11))
        selector_row.addWidget(selector_label)

        self.provider_combo = QComboBox()
        self.provider_combo.setEditable(False)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        selector_row.addWidget(self.provider_combo, 1)

        self.new_btn = QPushButton("New")
        self.new_btn.setCursor(Qt.PointingHandCursor)
        self.new_btn.setFixedHeight(26)
        self.new_btn.setStyleSheet(self._ghost_button_style())
        self.new_btn.clicked.connect(self._on_new_provider)
        selector_row.addWidget(self.new_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setFixedHeight(26)
        self.delete_btn.setStyleSheet(self._ghost_button_style())
        self.delete_btn.clicked.connect(self._on_delete_provider)
        selector_row.addWidget(self.delete_btn)

        layout.addLayout(selector_row)

        self.name_input = self._line_row(layout, "Display Name / 显示名")
        self.endpoint_input = self._line_row(layout, "Endpoint URL / 接口地址")
        self.api_key_input = self._line_row(layout, "API Key / 密钥")
        self.api_key_input.setEchoMode(QLineEdit.Password)

        model_row = QHBoxLayout()
        model_label = QLabel("Model / 模型")
        model_label.setFont(QFont(".AppleSystemUIFont", 11))
        model_row.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        model_row.addWidget(self.model_combo, 1)
        layout.addLayout(model_row)

        hint = QLabel("Example: http://localhost:11434/v1")
        hint.setStyleSheet("color: rgba(248, 250, 252, 0.45);")
        hint.setFont(QFont(".AppleSystemUIFont", 9))
        layout.addWidget(hint)

        return card

    def _build_generation_card(self) -> QFrame:
        card = self._build_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        lang_row = QHBoxLayout()
        lang_label = QLabel("Language / 语言")
        lang_label.setFont(QFont(".AppleSystemUIFont", 11))
        lang_row.addWidget(lang_label)

        self.language_combo = QComboBox()
        self.language_combo.addItem("中文", "zh")
        self.language_combo.addItem("English", "en")
        lang_row.addWidget(self.language_combo, 1)
        layout.addLayout(lang_row)

        temp_row = QHBoxLayout()
        temp_label = QLabel("Temperature")
        temp_label.setFont(QFont(".AppleSystemUIFont", 11))
        temp_row.addWidget(temp_label)

        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        temp_row.addWidget(self.temperature_spin)
        layout.addLayout(temp_row)

        token_row = QHBoxLayout()
        token_label = QLabel("Max Tokens")
        token_label.setFont(QFont(".AppleSystemUIFont", 11))
        token_row.addWidget(token_label)
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(64, 4096)
        token_row.addWidget(self.max_tokens_spin)
        layout.addLayout(token_row)

        timeout_row = QHBoxLayout()
        timeout_label = QLabel("Timeout (s)")
        timeout_label.setFont(QFont(".AppleSystemUIFont", 11))
        timeout_row.addWidget(timeout_label)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 120)
        timeout_row.addWidget(self.timeout_spin)
        layout.addLayout(timeout_row)

        return card

    def _build_personality_card(self) -> QFrame:
        card = self._build_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        label = QLabel("Custom Personality / 自定义人格")
        label.setFont(QFont(".AppleSystemUIFont", 11))
        layout.addWidget(label)

        self.personality_edit = QTextEdit()
        self.personality_edit.setPlaceholderText("Add extra system prompt here...")
        layout.addWidget(self.personality_edit)

        return card

    def _line_row(self, parent_layout: QVBoxLayout, label_text: str) -> QLineEdit:
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setFont(QFont(".AppleSystemUIFont", 11))
        row.addWidget(label)

        line_edit = QLineEdit()
        row.addWidget(line_edit, 1)
        parent_layout.addLayout(row)
        return line_edit

    def _primary_button_style(self) -> str:
        return (
            "QPushButton {"
            "background-color: #F97316;"
            "color: #0F172A;"
            "border: none;"
            "border-radius: 8px;"
            "padding: 6px 12px;"
            "}"
            "QPushButton:hover {"
            "background-color: #FB923C;"
            "}"
        )

    def _secondary_button_style(self) -> str:
        return (
            "QPushButton {"
            "background-color: rgba(255, 255, 255, 20);"
            "color: #F8FAFC;"
            "border: 1px solid rgba(255, 255, 255, 30);"
            "border-radius: 8px;"
            "padding: 6px 12px;"
            "}"
            "QPushButton:hover {"
            "background-color: rgba(255, 255, 255, 40);"
            "}"
        )

    def _ghost_button_style(self) -> str:
        return (
            "QPushButton {"
            "background-color: transparent;"
            "color: #F8FAFC;"
            "border: 1px solid rgba(255, 255, 255, 25);"
            "border-radius: 8px;"
            "padding: 4px 8px;"
            "}"
            "QPushButton:hover {"
            "background-color: rgba(255, 255, 255, 20);"
            "}"
        )

    def _load_config(self):
        self.config = load_llm_config()
        self._refresh_provider_combo()

        self.temperature_spin.setValue(float(self.config.get("temperature", 0.7)))
        self.max_tokens_spin.setValue(int(self.config.get("max_tokens", 1024)))
        self.timeout_spin.setValue(int(self.config.get("timeout_seconds", 30)))

        language = self.config.get("language", "zh")
        index = self.language_combo.findData(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        self.personality_edit.setText(self.config.get("custom_personality", ""))

    def _refresh_provider_combo(self):
        self.provider_combo.blockSignals(True)
        self.provider_combo.clear()
        providers = self.config.get("providers", [])
        for provider in providers:
            self.provider_combo.addItem(provider.get("name", ""))

        self.provider_combo.blockSignals(False)
        if providers:
            default = next((p for p in providers if p.get("is_default")), providers[0])
            self._load_provider(default)
            index = self.provider_combo.findText(default.get("name", ""))
            if index >= 0:
                self.provider_combo.setCurrentIndex(index)
        else:
            self._clear_provider_form()

    def _load_provider(self, provider: Dict):
        self._current_provider_name = provider.get("name")
        self.name_input.setText(provider.get("name", ""))
        self.endpoint_input.setText(provider.get("endpoint_url", ""))
        self.api_key_input.setText(decrypt_api_key(provider.get("encrypted_api_key", "")))

        models = provider.get("available_models", []) or []
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for model in models:
            self.model_combo.addItem(model)
        if provider.get("model_name") and provider.get("model_name") not in models:
            self.model_combo.addItem(provider.get("model_name"))
        if provider.get("model_name"):
            self.model_combo.setCurrentText(provider.get("model_name"))
        self.model_combo.blockSignals(False)

    def _clear_provider_form(self):
        self._current_provider_name = None
        self.name_input.clear()
        self.endpoint_input.clear()
        self.api_key_input.clear()
        self.model_combo.clear()

    def _on_provider_changed(self, index: int):
        providers = self.config.get("providers", [])
        if 0 <= index < len(providers):
            self._load_provider(providers[index])

    def _on_new_provider(self):
        self._clear_provider_form()
        self.provider_combo.setCurrentIndex(-1)
        self._set_status("正在创建新的配置...", False)

    def _on_delete_provider(self):
        name = self.name_input.text().strip()
        if not name:
            self._set_status("请选择要删除的配置。", True)
            return
        self.config = remove_provider(self.config, name)
        save_llm_config(self.config)
        self._load_config()
        self._set_status("配置已删除。", False)
        self.saved.emit()

    def _set_status(self, message: str, is_error: bool):
        color = "#F87171" if is_error else "#F8FAFC"
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(message)

    def _build_provider_from_form(self) -> Dict:
        return {
            "name": self.name_input.text().strip(),
            "endpoint_url": self.endpoint_input.text().strip(),
            "encrypted_api_key": encrypt_api_key(self.api_key_input.text().strip()),
            "model_name": self.model_combo.currentText().strip(),
            "is_default": True,
            "available_models": [self.model_combo.itemText(i) for i in range(self.model_combo.count())],
        }

    def _validate_form(self) -> Optional[str]:
        if not self.name_input.text().strip():
            return "请填写显示名。"
        if not self.endpoint_input.text().strip():
            return "请填写接口地址。"
        if not self.model_combo.currentText().strip():
            return "请填写模型名称。"
        return None

    def _on_fetch_models(self):
        endpoint = self.endpoint_input.text().strip()
        if not endpoint:
            self._set_status("请填写接口地址。", True)
            return

        provider = self._create_provider_for_models()
        if not provider:
            return

        self._run_async_task(provider.list_models, self._on_models_result)

    def _on_save(self):
        error = self._validate_form()
        if error:
            self._set_status(error, True)
            return

        provider = self._create_provider()
        if not provider:
            return

        self._run_async_task(provider.test_connection, self._on_test_result)

    def _create_provider(self) -> Optional[OpenAICompatibleProvider]:
        endpoint = self.endpoint_input.text().strip()
        model = self.model_combo.currentText().strip()
        api_key = self.api_key_input.text().strip()
        if not endpoint or not model:
            self._set_status("请填写完整的接口信息。", True)
            return None
        timeout = int(self.timeout_spin.value())
        return OpenAICompatibleProvider(endpoint, api_key, model, timeout)

    def _create_provider_for_models(self) -> Optional[OpenAICompatibleProvider]:
        endpoint = self.endpoint_input.text().strip()
        api_key = self.api_key_input.text().strip()
        if not endpoint:
            self._set_status("请填写接口地址。", True)
            return None
        timeout = int(self.timeout_spin.value())
        return OpenAICompatibleProvider(endpoint, api_key, "placeholder", timeout)

    def _run_async_task(self, coro_func, on_success):
        self._set_buttons_enabled(False)
        self._worker = AsyncWorker(coro_func)
        self._worker_thread = QThread()
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.result.connect(on_success)
        self._worker.error.connect(self._on_task_error)
        self._worker.result.connect(self._worker_thread.quit)
        self._worker.error.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._cleanup_worker)
        self._worker_thread.start()

    def _cleanup_worker(self):
        self._set_buttons_enabled(True)
        if self._worker:
            self._worker.deleteLater()
        self._worker = None
        if self._worker_thread:
            self._worker_thread.deleteLater()
        self._worker_thread = None

    def _on_task_error(self, message: str):
        self._set_status(f"连接失败: {message}", True)

    def _on_models_result(self, result):
        models, error = result
        if error:
            self._set_status(f"获取模型失败: {error}", True)
            return
        self.model_combo.clear()
        for model in models:
            self.model_combo.addItem(model)
        if models:
            self.model_combo.setCurrentIndex(0)
        self._set_status("模型列表已更新。", False)

    def _on_test_result(self, result):
        ok, message = result
        if not ok:
            self._set_status(f"连接失败: {message}", True)
            return

        provider_data = self._build_provider_from_form()
        self.config = upsert_provider(self.config, provider_data)
        self.config = set_default_provider(self.config, provider_data["name"])
        self.config["temperature"] = float(self.temperature_spin.value())
        self.config["max_tokens"] = int(self.max_tokens_spin.value())
        self.config["timeout_seconds"] = int(self.timeout_spin.value())
        self.config["language"] = self.language_combo.currentData()
        self.config["custom_personality"] = self.personality_edit.toPlainText().strip()

        success, error = save_llm_config(self.config)
        if not success:
            self._set_status(f"保存失败: {error}", True)
            return

        self._set_status("配置已保存。", False)
        self._load_config()
        self.saved.emit()

    def _set_buttons_enabled(self, enabled: bool):
        self.models_btn.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)

    def _on_close(self):
        self.closed.emit()
