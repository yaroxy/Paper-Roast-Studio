import gradio as gr
import os
from importlib.machinery import SourceFileLoader
from ocr import OCRClient

QwenAPIClient = SourceFileLoader("qwen_api", os.path.join(os.path.dirname(__file__), "qwen-api.py")).load_module().QwenAPIClient

client = OCRClient()
qwen_client = QwenAPIClient()

def handle(file):
    if file is None:
        return gr.update(choices=[], value=None), "未选择文件", [], "", []
    with open(file.name, "rb") as f:
        file_bytes = f.read()
    pages = client.parse_pdf_bytes_pages(file_bytes)
    if not pages:
        return gr.update(choices=[], value=None), "解析失败或未解析到内容", [], "", []
    choices = [f"第{i+1}页" for i in range(len(pages))]
    first = pages[0]
    total_pages = len(pages)
    total_images = sum(len(p.get("images", [])) for p in pages)
    analysis = (
        "**解析摘要**\n\n"
        f"- 页数：{total_pages}\n"
        f"- 图片：{total_images}\n\n"
        "正在生成解读内容..."
    )
    return gr.update(choices=choices, value=choices[0]), first.get("markdown", ""), first.get("images", []), analysis, pages

def build_ui():
    with gr.Blocks() as demo:
        gr.Markdown("# Paper Roast Studio")
        gr.HTML("""
        <style>
        .gradio-container { max-width: 1600px !important; }
        .center-gallery img { 
          display: block; 
          margin: auto; 
          max-width: 100%; 
          max-height: 100%; 
          width: auto !important; 
          height: auto !important; 
          object-fit: contain; 
        }
        .center-md img {
          display: block;
          margin: 0 auto;
          max-width: 100%;
          height: auto;
        }
        /* Markdown 文本保持默认左对齐，仅图片居中 */
        .center-gallery .gallery-item,
        .center-gallery .thumbnail,
        .center-gallery .image-container,
        .center-gallery .grid-item,
        .center-gallery > * {
          display: flex; 
          justify-content: center; 
          align-items: center; 
        }
        </style>
        """)
        with gr.Row():
            file_input = gr.File(label="上传PDF", file_types=[".pdf"])
            submit = gr.Button("解析")
            page_selector = gr.Dropdown(label="选择页码", choices=[], interactive=True)
            pages_state = gr.State([])
        with gr.Row():
            with gr.Column(scale=2):
                md_output = gr.Markdown(elem_classes=["center-md"])
                gallery_output = gr.Gallery(label="解析图片", columns=2, rows=2, height=500, elem_classes=["center-gallery"])
            with gr.Column(scale=1):
                analysis_output = gr.Markdown(label="解读内容", value="将在此显示解读内容")
        submit.click(fn=handle, inputs=file_input, outputs=[page_selector, md_output, gallery_output, analysis_output, pages_state])
        
        def generate_analysis_stream(pages):
            if not pages:
                yield ""
                return
            markdown_context = "\n\n".join([p.get("markdown", "") for p in pages if p.get("markdown")])
            image_urls = []
            for p in pages:
                image_urls.extend([u for u in p.get("images", []) if u])
            dedup = []
            seen = set()
            for u in image_urls:
                if u not in seen:
                    seen.add(u)
                    dedup.append(u)
            image_urls = dedup
            prompt = (
                "解读一下并总结这段内容，然后以简洁的 Markdown 输出，并标注引用依据。\n\n"
                + markdown_context
            )
            reasoning_buf = ""
            answer_buf = ""
            yield "**模型思考**\n\n" + "" + "\n\n" + "**解读内容**\n\n" + ""
            stream = qwen_client.stream_chat_with_images(image_urls, prompt)
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                    reasoning_buf += delta.reasoning_content
                else:
                    if delta.content:
                        answer_buf += delta.content
                yield "**模型思考**\n\n" + (reasoning_buf or "无") + "\n\n" + "**解读内容**\n\n" + (answer_buf or "")

        submit.click(fn=handle, inputs=file_input, outputs=[page_selector, md_output, gallery_output, analysis_output, pages_state]).then(
            fn=generate_analysis_stream,
            inputs=pages_state,
            outputs=analysis_output,
        )

        def change_page(selected, pages):
            if not pages:
                return "", []
            try:
                idx = [f"第{i+1}页" for i in range(len(pages))].index(selected)
            except ValueError:
                idx = 0
            page = pages[idx]
            return page.get("markdown", ""), page.get("images", [])

        page_selector.change(fn=change_page, inputs=[page_selector, pages_state], outputs=[md_output, gallery_output])

        with gr.Row():
            with gr.Column(scale=1):
                qa_question = gr.Textbox(label="详细问题", placeholder="请输入你的问题（基于解析内容）", lines=3)
                qa_submit = gr.Button("提问")
                qa_answer = gr.Markdown(label="回答")
            with gr.Column(scale=1):
                rebuttal_input = gr.Textbox(label="Rebuttal 输入", placeholder="提出反驳或验证点", lines=3)
                rebuttal_submit = gr.Button("生成 Rebuttal")
                rebuttal_output = gr.Markdown(label="Rebuttal 输出")

        def answer_question_stream(question, pages):
            if not question:
                yield "请先输入问题。"
                return
            if not pages:
                yield "尚未解析到文档内容，无法回答。"
                return
            markdown_context = "\n\n".join([p.get("markdown", "") for p in pages if p.get("markdown")])
            image_urls = []
            for p in pages:
                image_urls.extend([u for u in p.get("images", []) if u])
            dedup = []
            seen = set()
            for u in image_urls:
                if u not in seen:
                    seen.add(u)
                    dedup.append(u)
            image_urls = dedup[:8]
            prompt = (
                "请基于提供的文档内容精准回答用户问题，并指出引用依据。\n\n"
                + markdown_context
                + "\n\n用户问题：" + question
            )
            reasoning_buf = ""
            answer_buf = ""
            yield "**模型思考**\n\n" + "" + "\n\n" + "**回答**\n\n" + ""
            stream = qwen_client.stream_chat_with_images(image_urls, prompt)
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                    reasoning_buf += delta.reasoning_content
                else:
                    if delta.content:
                        answer_buf += delta.content
                yield "**模型思考**\n\n" + (reasoning_buf or "无") + "\n\n" + "**回答**\n\n" + (answer_buf or "")

        def handle_rebuttal_stream(prompt, pages):
            if not prompt:
                yield "请先输入 Rebuttal 内容。"
                return
            if not pages:
                yield "尚未解析到文档内容，无法生成 Rebuttal。"
                return
            markdown_context = "\n\n".join([p.get("markdown", "") for p in pages if p.get("markdown")])
            image_urls = []
            for p in pages:
                image_urls.extend([u for u in p.get("images", []) if u])
            dedup = []
            seen = set()
            for u in image_urls:
                if u not in seen:
                    seen.add(u)
                    dedup.append(u)
            image_urls = dedup[:8]
            prompt_text = (
                "根据以下文档内容，针对用户的 Rebuttal 输入生成严谨的反驳与证据链，明确引用出处。\n\n"
                + markdown_context
                + "\n\nRebuttal 输入：" + prompt
            )
            reasoning_buf = ""
            answer_buf = ""
            yield "**模型思考**\n\n" + "" + "\n\n" + "**Rebuttal 输出**\n\n" + ""
            stream = qwen_client.stream_chat_with_images(image_urls, prompt_text)
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                    reasoning_buf += delta.reasoning_content
                else:
                    if delta.content:
                        answer_buf += delta.content
                yield "**模型思考**\n\n" + (reasoning_buf or "无") + "\n\n" + "**Rebuttal 输出**\n\n" + (answer_buf or "")

        qa_submit.click(fn=answer_question_stream, inputs=[qa_question, pages_state], outputs=[qa_answer])
        rebuttal_submit.click(fn=handle_rebuttal_stream, inputs=[rebuttal_input, pages_state], outputs=[rebuttal_output])
    return demo

if __name__ == "__main__":
    ui = build_ui()
    ui.launch()