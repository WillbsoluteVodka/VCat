"""First-time LLM setup wizard."""

import asyncio
from typing import Callable, Optional

from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QFrame,
)

from src.llm.config import load_llm_config, save_llm_config, upsert_provider, set_default_provider
from src.llm.security import encrypt_api_key
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


class SetupWizard(QDialog):
    configured = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_llm_config()
        self._worker_thread: Optional[QThread] = None
        self._worker: Optional[AsyncWorker] = None
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("LLM Setup")
        self.setFixedSize(420, 520)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        container = QFrame(self)
        container.setObjectName("wizardContainer")
        container.setStyleSheet(
            """
            QFrame#wizardContainer {
                background-color: #101216;
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 30);
            }
            QLabel {
                color: #F8FAFC;
            }
            QLineEdit, QComboBox {
                background-color: rgba(255, 255, 255, 18);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 8px;
                padding: 6px 8px;
                color: #F8FAFC;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #F97316;
            }
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Connect Your LLM / 连接你的模型")
        title.setFont(QFont(".AppleSystemUIFont", 16, QFont.Medium))
        layout.addWidget(title)

        subtitle = QLabel("Choose a provider preset or fill in details.")
        subtitle.setStyleSheet("color: rgba(248, 250, 252, 0.7);")
        subtitle.setFont(QFont(".AppleSystemUIFont", 11))
        layout.addWidget(subtitle)

        preset_row = QHBoxLayout()
        preset_row.addWidget(self._preset_button("Ollama", self._apply_ollama))
        preset_row.addWidget(self._preset_button("LM Studio", self._apply_lm_studio))
        preset_row.addWidget(self._preset_button("OpenAI", self._apply_openai))
        layout.addLayout(preset_row)

        layout.addWidget(self._line_label("Display Name / 显示名"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        layout.addWidget(self._line_label("Endpoint URL / 接口地址"))
        self.endpoint_input = QLineEdit()
        layout.addWidget(self.endpoint_input)

        layout.addWidget(self._line_label("API Key / 密钥"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.api_key_input)

        layout.addWidget(self._line_label("Model / 模型"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        layout.addWidget(self.model_combo)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: rgba(248, 250, 252, 0.7);")
        layout.addWidget(self.status_label)

        layout.addStretch()

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

        self.close_btn = QPushButton("Close")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setFixedHeight(32)
        self.close_btn.setStyleSheet(self._secondary_button_style())
        self.close_btn.clicked.connect(self.reject)

        button_row.addWidget(self.models_btn)
        button_row.addWidget(self.save_btn)
        button_row.addWidget(self.close_btn)
        layout.addLayout(button_row)

        self._apply_ollama()

    def _preset_button(self, text, callback):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(28)
        btn.setStyleSheet(self._ghost_button_style())
        btn.clicked.connect(callback)
        return btn

    def _line_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setFont(QFont(".AppleSystemUIFont", 11))
        return label

    def _ghost_button_style(self) -> str:
        return (
            "QPushButton {"
            "background-color: rgba(255, 255, 255, 12);"
            "color: #F8FAFC;"
            "border: 1px solid rgba(255, 255, 255, 25);"
            "border-radius: 8px;"
            "padding: 4px 8px;"
            "}"
            "QPushButton:hover {"
            "background-color: rgba(255, 255, 255, 24);"
            "}"
        )

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

    def _set_status(self, message: str, is_error: bool):
        color = "#F87171" if is_error else "#F8FAFC"
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(message)

    def _apply_ollama(self):
        self.name_input.setText("Ollama")
        self.endpoint_input.setText("http://localhost:11434/v1")
        self.model_combo.clear()
        self.model_combo.addItem("qwen2.5:7b")
        self.model_combo.setCurrentText("qwen2.5:7b")
        self.api_key_input.clear()
        self._set_status("已加载 Ollama 预设。", False)

    def _apply_lm_studio(self):
        self.name_input.setText("LM Studio")
        self.endpoint_input.setText("http://localhost:1234/v1")
        self.model_combo.clear()
        self.model_combo.addItem("local-model")
        self.model_combo.setCurrentText("local-model")
        self.api_key_input.clear()
        self._set_status("已加载 LM Studio 预设。", False)

    def _apply_openai(self):
        self.name_input.setText("OpenAI")
        self.endpoint_input.setText("https://api.openai.com/v1")
        self.model_combo.clear()
        self.model_combo.addItem("gpt-4o-mini")
        self.model_combo.setCurrentText("gpt-4o-mini")
        self._set_status("已加载 OpenAI 预设。", False)

    def _validate(self) -> Optional[str]:
        if not self.name_input.text().strip():
            return "请填写显示名。"
        if not self.endpoint_input.text().strip():
            return "请填写接口地址。"
        if not self.model_combo.currentText().strip():
            return "请填写模型名称。"
        return None

    def _create_provider(self) -> Optional[OpenAICompatibleProvider]:
        endpoint = self.endpoint_input.text().strip()
        model = self.model_combo.currentText().strip()
        api_key = self.api_key_input.text().strip()
        if not endpoint or not model:
            return None
        return OpenAICompatibleProvider(endpoint, api_key, model, 30)

    def _create_provider_for_models(self) -> Optional[OpenAICompatibleProvider]:
        endpoint = self.endpoint_input.text().strip()
        api_key = self.api_key_input.text().strip()
        if not endpoint:
            return None
        return OpenAICompatibleProvider(endpoint, api_key, "placeholder", 30)

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

    def _set_buttons_enabled(self, enabled: bool):
        self.models_btn.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.close_btn.setEnabled(enabled)

    def _on_fetch_models(self):
        endpoint = self.endpoint_input.text().strip()
        if not endpoint:
            self._set_status("请填写接口地址。", True)
            return
        provider = self._create_provider_for_models()
        if not provider:
            self._set_status("接口信息不完整。", True)
            return
        self._run_async_task(provider.list_models, self._on_models_result)

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

    def _on_save(self):
        error = self._validate()
        if error:
            self._set_status(error, True)
            return

        provider = self._create_provider()
        if not provider:
            self._set_status("接口信息不完整。", True)
            return

        self._run_async_task(provider.test_connection, self._on_test_result)

    def _on_test_result(self, result):
        ok, message = result
        if not ok:
            self._set_status(f"连接失败: {message}", True)
            return

        provider_data = {
            "name": self.name_input.text().strip(),
            "endpoint_url": self.endpoint_input.text().strip(),
            "encrypted_api_key": encrypt_api_key(self.api_key_input.text().strip()),
            "model_name": self.model_combo.currentText().strip(),
            "is_default": True,
            "available_models": [self.model_combo.itemText(i) for i in range(self.model_combo.count())],
        }

        self.config = upsert_provider(self.config, provider_data)
        self.config = set_default_provider(self.config, provider_data["name"])
        success, error = save_llm_config(self.config)
        if not success:
            self._set_status(f"保存失败: {error}", True)
            return

        self._set_status("配置完成。", False)
        self.configured.emit()
        self.accept()
