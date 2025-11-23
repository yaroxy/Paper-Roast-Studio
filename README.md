# Paper Roast Studio

一个面向论文与技术文档的解析与解读工作台：
- 将 PDF 解析为 Markdown 并自动替换图片引用为真实 URL（支持图像居中展示）
- 将全文 Markdown 与图片 URL 一并送入 Qwen3-VL 模型进行解读与生成
- 支持解读、问答与 Rebuttal 的流式输出
- 简洁的 Gradio 界面，操作直观

## 界面介绍
- 顶部：标题与样式注入（居中图片渲染）
- 左侧（1/2）：
  - 上传 PDF（支持 `.pdf`）
  - 页码下拉选择：切换展示某一页的 Markdown 与图片
- 中间（1/2）：
  - Markdown 内容（按页展示）
  - 图片画廊（按页展示）
- 右侧（1/3）：
  - 解读内容：在解析完成后由模型生成，实时流式更新
- 底部两栏（各 1/2）：
  - 提问与回答（流式）
  - Rebuttal 输入与输出（流式）

界面逻辑参考：`ui.py:31-75`, `ui.py:101-105`, `ui.py:119-127`

## 功能特性
- PDF 解析为 Markdown 与图片 URL（`ocr.py:1-94`）
- 图片 URL 去重与替换，Markdown 图片居中渲染（`ocr.py:1-94`）
- 多图片输入的 Qwen API 封装（`qwen-api.py:48-70`, `qwen-api.py:96-118`）
- 流式输出：解读、问答、Rebuttal（`ui.py:77-99`, `ui.py:129-154`, `ui.py:156-181`）
- 解读阶段使用全文与全部图片；问答与 Rebuttal 默认最多取 8 张图片（可按需调整）

## 环境准备
- Python 3.10+
- 安装依赖：
  - `pip install gradio openai dotenv requests`

## 环境变量
在项目根目录创建 `.env` 文件：

```
# OCR 服务
API_URL=你的OCR服务地址
TOKEN=你的OCR访问令牌
# 可选：是否验证 SSL（默认 true）
VERIFY_SSL=true

# Qwen / DashScope
DASHSCOPE_API_KEY=你的DashScope密钥
# 可选：自定义兼容模式 URL
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

加载逻辑参考：
- OCR：`ocr.py:6-13`
- Qwen：`qwen-api.py:6-11`

## 使用方法
1. 启动界面：
   - `python ui.py`
   - 控制台将输出 Gradio 访问地址，浏览器打开即可使用
2. 上传 PDF，等待解析完成：
   - 左侧页码可切换查看各页 Markdown 与图片
   - 右侧会先显示解析摘要（页数、图片数），随后自动开始流式生成解读内容
3. 提问与 Rebuttal：
   - 在底部两栏分别输入问题或 Rebuttal，模型将基于全文与图片进行流式回答

## 设计与约束
- 解读阶段：传递全文 Markdown 与全部图片 URL，不做截断（`ui.py:77-99`）
- 问答与 Rebuttal：默认取最多 8 张图片以控制上下文长度（`ui.py:141-145`, `ui.py:171-171`）。如需全部图片，可将切片逻辑移除。
- 文件名 `qwen-api.py` 含 `-`，通过 `SourceFileLoader` 引入（`ui.py:6`）。无需改名即可使用。

## 致谢
- Qwen 与 DashScope 提供多模态大模型能力
- Gradio 提供快速的 Web UI 框架
- OCR 服务提供文档结构化解析能力

---

欢迎提交 Issue 或 PR 来改进体验与功能。