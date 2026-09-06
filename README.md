# LocalExtract AI

LocalExtract AI 是一个 Windows 桌面工具：读取剪贴板中的截图，通过已经启动的本地多模态 AI 提取特征字符串，并把结果写回剪贴板。应用不会启动、停止或修改本地 AI 服务。

## 功能

- 启动时通过服务的 `/health` 端点验证本地 AI，无需发起模型推理。
- 读取 `Win+Shift+S` 等工具放入剪贴板的位图。
- 调用 `/v1/chat/completions` 识别编号、序列号、版本号、网址等特征字符串。
- 清理 Markdown 包装、空行和重复项后，将文本写回 Windows 剪贴板。
- 后台执行网络请求，GUI 保持响应；支持安全取消、实时日志和状态显示。

## 环境与安装

需要 Windows 和 Python 3.10+。本地 AI 必须已经启动，并支持 OpenAI 兼容的多模态接口。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 配置

默认配置在 `config.yaml`。需要本机差异时，将 `common.env.example` 复制为 `common.env` 并修改；该文件不会提交到 Git。

```dotenv
LOCAL_AI_BASE_URL=http://127.0.0.1:8080/v1
LOCAL_AI_API_KEY=local
LOCAL_AI_MODEL=local-model
```

`LOCAL_AI_BASE_URL` 应包含 `/v1`。识别提示词和输出分隔符在 `config.yaml` 的 `flows.extract_clipboard` 下配置。

## 运行

```powershell
python main.py
```

使用步骤：

1. 先启动本地 AI 服务。
2. 启动本工具，等待界面显示“本地 AI 正常”。
3. 使用 `Win+Shift+S` 截图。
4. 点击“开始识别”。完成后直接到目标位置粘贴结果。

日志保存在 `logs/main.log`，单文件最大 10 MB，保留 5 份备份。

## 测试与检查

```powershell
python -m pytest
python -m compileall main.py flows src tests
```

测试使用模拟网络响应和临时配置，不访问真实本地 AI，也不修改真实剪贴板。

## 项目结构

- `main.py`：唯一应用入口，加载配置、初始化日志和 GUI。
- `flows/`：剪贴板识别工作流编排。
- `src/local_extract_ai/modules/`：剪贴板、AI 客户端和文本规范化能力。
- `tests/`：单元测试。
- `docs/`：项目规范文档。
- `logs/`：运行日志，不进入版本库。

## GitHub 同步

提交前检查 `git status --short --ignored`，确认没有提交 `common.env`、日志、截图或其他隐私数据。远端优先使用 SSH；首次初始化仓库后再按实际仓库地址添加 `origin`。
