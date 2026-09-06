# LocalExtract AI

LocalExtract AI 是一个 Windows 桌面工具：读取剪贴板中的截图，通过已经启动的本地多模态 AI 提取特征字符串，在窗口中显示完整识别结果，并把结果写回剪贴板。应用不会启动、停止或修改本地 AI 服务。

## 功能

- 启动时通过服务的 `/health` 端点验证本地 AI，无需发起模型推理。
- 读取 `Win+Shift+S` 等工具放入剪贴板的位图。
- 调用 `/v1/chat/completions` 识别由数字、英文字母和下划线组成的房间编号，以及编号正上方对应的中文名字。
- 按“中文名字 + 制表符 + 房间编号”逐行输出，保持图片中的空间对应关系和阅读顺序。
- 清理 Markdown 包装、空行和重复项后，在“运行日志与实时输出”区域显示完整识别结果，并将相同文本写回 Windows 剪贴板；粘贴到表格时会自动形成姓名、房间编号两列。
- 后台执行网络请求，GUI 保持响应；支持安全取消、实时日志和状态显示。

## 界面

- “截图识别”选项卡显示输入来源、AI 状态和操作说明。
- “全局配置”选项卡显示当前服务地址、模型和超时时间，不显示 API key。
- “参数预览”“开始识别”“取消任务”位于固定任务操作栏，切换选项卡后仍然可见。
- “运行日志与实时输出”区域显示任务过程以及带分隔线的完整识别结果。

## 环境与安装

需要 Windows 和 Python 3.10+。本地 AI 必须已经启动，并支持 OpenAI 兼容的多模态接口。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 配置

默认配置在 `config.yaml`。程序启动时会依次读取项目根目录的 `.env` 和 `common.env`；两者都不会提交到 Git。进程中已经存在的环境变量优先级最高。

```dotenv
LOCAL_AI_BASE_URL=http://127.0.0.1:8080/v1
LOCAL_AI_API_KEY=local
LOCAL_AI_MODEL=local-model
```

API key 支持 `LOCAL_AI_API_KEY`、`LLAMACPP_API_KEY` 和 `OPENAI_API_KEY` 变量名。调用本地 AI 时会通过 `Authorization: Bearer <API key>` 请求头发送，密钥本身不会写入日志或显示在界面中。启动验证会依次检查 `/health` 和需要鉴权的 `/v1/models`，鉴权失败时不会启用识别按钮。

`LOCAL_AI_BASE_URL` 应包含 `/v1`。识别提示词和输出分隔符在 `config.yaml` 的 `flows.extract_clipboard` 下配置。

## 运行

```powershell
python main.py
```

使用步骤：

1. 先启动本地 AI 服务。
2. 启动本工具，等待界面显示“本地 AI 正常”。
3. 使用 `Win+Shift+S` 截图。
4. 点击固定任务操作栏中的“开始识别”。
5. 在“运行日志与实时输出”区域查看完整结果；结果也已写入剪贴板，可直接粘贴到目标位置。

输出示例（两列之间为制表符）：

```text
张三	A_101
李四	B2_203
```

日志保存在 `logs/main.log`，单文件最大 10 MB，保留 5 份备份。

## 测试与检查

```powershell
python -m pytest
python -m compileall main.py flows src tests
```

测试使用模拟网络响应和临时配置，不访问真实本地 AI，也不修改真实剪贴板。

测试产生的 `.pytest_cache/`、`.pytest_tmp/`、`.pytest-results/` 等目录统一由 `.gitignore` 中的 `.pytest*/` 规则排除；该规则同样适用于项目任意子目录。

## 项目结构

- `main.py`：唯一应用入口，加载配置、初始化日志和 GUI。
- `flows/`：剪贴板识别工作流编排。
- `src/local_extract_ai/modules/`：剪贴板、AI 客户端和文本规范化能力。
- `tests/`：单元测试。
- `docs/`：项目规范文档。
- `logs/`：运行日志，不进入版本库。

## GitHub 同步

GitHub 仓库：<https://github.com/jackylx2008/LocalExtract-AI>

项目使用 SSH 远端：

```text
git@github.com:jackylx2008/LocalExtract-AI.git
```

提交前运行 `git status --short --ignored`，确认没有提交 `.env`、`common.env`、日志、截图、pytest 临时目录或其他隐私数据。检查无误后推送：

```powershell
git push origin main
```
