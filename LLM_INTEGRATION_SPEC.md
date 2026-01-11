# VCat LLM 智能对话集成方案

## 需求概要

将 VCat 桌面宠物的对话系统从硬编码响应升级为可配置的 LLM 智能对话，支持用户自行配置 API（OpenAI、Ollama、LM Studio 等）。

---

## 核心需求清单

| 类别 | 需求 | 优先级 |
|------|------|--------|
| API集成 | OpenAI兼容格式 + Provider抽象层 | P0 |
| 多配置 | 支持保存多个API配置并快速切换 | P0 |
| 密钥安全 | 加密存储API Key（基于机器ID） | P0 |
| 连接测试 | 保存时自动测试，失败则拒绝保存 | P0 |
| 模型选择 | 动态获取可用模型列表 | P0 |
| 流式输出 | 支持逐字显示响应 | P0 |
| 人格系统 | 默认猫咪System Prompt + 用户可自定义 | P0 |
| 短期记忆 | 会话内完整上下文 | P0 |
| 命令扩展 | /help, /new, /memory, /settings | P0 |
| 首次引导 | 强制配置向导 | P0 |
| 错误处理 | 完全阻断，显示错误并要求修复 | P0 |
| 双语UI | 中英文支持 | P0 |
| 设置入口 | 聊天窗口内齿轮图标 | P0 |
| 长期记忆 | RAG向量检索（本地Embedding） | P1 |
| 历史管理 | 时间线视图（今天/昨天/本周） | P1 |
| 记忆管理 | 查看/搜索/编辑/删除记忆 | P1 |
| 记忆重置 | 一键清空（需二次确认） | P1 |

---

## 技术架构

### 新增文件结构

```
src/
├── llm/                          # LLM集成模块
│   ├── __init__.py
│   ├── provider.py               # 抽象Provider接口
│   ├── openai_provider.py        # OpenAI兼容实现
│   ├── config.py                 # LLM配置管理
│   ├── session.py                # 会话管理
│   ├── personality.py            # 人格/System Prompt
│   └── security.py               # API Key加密
├── memory/                       # RAG记忆模块 (Phase 2)
│   ├── __init__.py
│   ├── embeddings.py             # 本地Embedding模型
│   ├── vector_store.py           # ChromaDB向量存储
│   ├── memory_manager.py         # 记忆提取与检索
│   └── history.py                # 对话历史持久化
├── ui/
│   ├── llm_settings_panel.py     # LLM设置面板
│   └── setup_wizard.py           # 首次配置向导
└── data/                         # 数据存储
    ├── conversations/            # 对话历史JSON
    └── memories/                 # ChromaDB存储
```

### 需修改的现有文件

| 文件 | 修改内容 |
|------|----------|
| `src/chat/handler.py` | 集成LLM Provider，添加流式响应信号 |
| `src/chat/commands.py` | 扩展命令系统 |
| `src/ui/chat_dialog.py` | 流式UI、设置入口、向导触发 |
| `pyproject.toml` | 添加依赖 |

---

## Phase 1 实现计划（核心功能）

### 步骤 1: Provider 抽象层
- 创建 `BaseLLMProvider` 抽象基类
- 定义接口: `chat()`, `test_connection()`, `list_models()`
- 实现 `OpenAICompatibleProvider`（支持 OpenAI/Ollama/LM Studio/vLLM）
- 使用 `httpx` 异步HTTP客户端
- 支持流式响应 (SSE)

### 步骤 2: 安全与配置
- 使用 `cryptography` + 机器硬件UUID 加密 API Key
- 配置存储在 `llm_config.json`
- 支持多Provider配置，标记默认项
- 保存时自动调用 `test_connection()` 验证

### 步骤 3: 会话与人格
- `ChatSession` 管理会话消息历史
- `CatPersonality` 提供默认中/英文猫咪人格
- 用户可追加自定义人格设定
- 默认参数: temperature=0.7, max_tokens=1024, timeout=30s

### 步骤 4: 聊天集成
- 修改 `ChatHandler` 集成LLM
- 未配置时静默回退到硬编码响应
- 使用 Qt Signal/Slot 处理异步流式响应
- 扩展命令: `/new`(新对话), `/memory`(记忆状态), `/settings`(打开设置)

### 步骤 5: UI集成
- 在 `ChatDialog` 头部添加齿轮图标
- 创建滑入式设置面板 `LLMSettingsPanel`
- 创建首次配置向导 `SetupWizard`（含Ollama/LM Studio/OpenAI预设）
- 流式响应气泡逐字显示
- 双语标签支持

---

## Phase 2 实现计划（高级功能）

### 步骤 6: 本地Embedding
- 使用 `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`)
- 懒加载: 首次使用时下载 (~420MB)
- 支持中英文混合文本

### 步骤 7: 向量存储
- 使用 `ChromaDB` 本地持久化
- 存储格式: content + embedding + metadata
- 支持相似度检索 (cosine)

### 步骤 8: 记忆管理
- 自动从对话中提取关键信息
- 基于用户输入检索相关记忆
- 将记忆注入 System Prompt 上下文
- 完整管理UI: 列表/搜索/编辑/删除/清空

### 步骤 9: 对话历史
- JSON持久化每个会话
- 时间线分组视图 (今天/昨天/本周/本月/更早)
- 支持切换查看历史对话

---

## 依赖项

```toml
# Phase 1
httpx = ">=0.27.0"
cryptography = ">=41.0.0"

# Phase 2 (可选)
sentence-transformers = ">=2.2.0"
chromadb = ">=0.4.0"
```

---

## 配置数据结构

### llm_config.json
```json
{
  "language": "zh",
  "custom_personality": "",
  "temperature": 0.7,
  "max_tokens": 1024,
  "timeout_seconds": 30,
  "providers": [
    {
      "name": "My Ollama",
      "endpoint_url": "http://localhost:11434/v1",
      "encrypted_api_key": "",
      "model_name": "qwen2.5:7b",
      "is_default": true,
      "available_models": []
    }
  ]
}
```

---

## 错误处理策略

| 错误类型 | 处理方式 |
|----------|----------|
| 未配置API | 弹出强制配置向导 |
| 连接超时 | 显示 "连接超时喵～请检查网络设置喵～" |
| Key无效 | 显示 "API Key 无效喵～请检查设置喵～" |
| 服务器错误 | 显示 "服务器开小差了喵～稍后再试喵～" |
| 保存失败 | 拒绝保存，显示具体错误 |

---

## 验证方案

### Phase 1 验证
1. 启动应用，首次打开聊天应弹出配置向导
2. 配置 Ollama/LM Studio 本地API，保存时应自动测试
3. 发送消息，应看到流式逐字响应
4. 响应应保持猫咪人格（结尾带"喵～"）
5. `/new` 应开始新对话，清空历史
6. `/help` 应显示命令列表
7. 关闭应用重启，配置应保留

### Phase 2 验证
1. 对话中提到个人信息（如"我叫小明"）
2. 开始新对话后询问相关问题
3. 小猫应能基于记忆回答
4. 记忆管理界面应显示已存储的记忆
5. 删除记忆后应无法再召回
6. 时间线应正确分组历史对话

---

## 关键设计决策

1. **Provider抽象**: 便于未来扩展 Anthropic/Google 等其他格式
2. **机器级加密**: API Key 与机器绑定，换机器需重新配置
3. **懒加载Embedding**: 避免启动时加载大模型影响性能
4. **静默回退**: LLM不可用时自动使用硬编码响应，保证基本可用
5. **Qt异步**: 使用 Signal/Slot 处理流式响应，不阻塞UI
