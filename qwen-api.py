from openai import OpenAI
from typing import Generator, Tuple, Optional, List
import os
from dotenv import load_dotenv

class QwenAPIClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        load_dotenv()
        key = api_key or os.getenv("DASHSCOPE_API_KEY")
        url = base_url or os.getenv("DASHSCOPE_BASE_URL") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        if not key:
            raise ValueError("缺少 DASHSCOPE_API_KEY 环境变量")
        self.client = OpenAI(api_key=key, base_url=url)

    def stream_chat_with_image(
        self,
        image_url: str,
        text: str,
        enable_thinking: bool = True,
        thinking_budget: int = 1024,
    ) -> Generator:
        completion = self.client.chat.completions.create(
            model="qwen3-vl-plus",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": text},
                    ],
                }
            ],
            stream=True,
            extra_body={"enable_thinking": enable_thinking, "thinking_budget": thinking_budget},
            max_tokens=2048
        )
        for chunk in completion:
            yield chunk

    def stream_chat_with_images(
        self,
        image_urls: List[str],
        text: str,
        enable_thinking: bool = True,
        thinking_budget: int = 1024,
    ) -> Generator:
        content = []
        for url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})
        content.append({"type": "text", "text": text})
        completion = self.client.chat.completions.create(
            model="qwen3-vl-plus",
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
            stream=True,
            extra_body={"enable_thinking": enable_thinking, "thinking_budget": thinking_budget},
            max_tokens=2048
        )
        for chunk in completion:
            yield chunk

    def chat_with_image(
        self,
        image_url: str,
        text: str,
        enable_thinking: bool = True,
        thinking_budget: int = 1024,
    ) -> Tuple[str, str]:
        reasoning = ""
        answer = ""
        is_answering = False
        for chunk in self.stream_chat_with_image(image_url, text, enable_thinking, thinking_budget):
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                reasoning += delta.reasoning_content
            else:
                if delta.content != "" and is_answering is False:
                    is_answering = True
                answer += delta.content
        return reasoning, answer
    
    def chat_with_images(
        self,
        image_urls: List[str],
        text: str,
        enable_thinking: bool = True,
        thinking_budget: int = 1024,
    ) -> Tuple[str, str]:
        reasoning = ""
        answer = ""
        is_answering = False
        for chunk in self.stream_chat_with_images(image_urls, text, enable_thinking, thinking_budget):
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
                reasoning += delta.reasoning_content
            else:
                if delta.content != "" and is_answering is False:
                    is_answering = True
                answer += delta.content
        return reasoning, answer


if __name__ == "__main__":
    client = QwenAPIClient()
    # reasoning, answer = client.chat_with_image(
    #     image_url="https://img.alicdn.com/imgextra/i1/O1CN01gDEY8M1W114Hi3XcN_!!6000000002727-0-tps-1024-406.jpg",
    #     text="请描述这张图片",
    # )
    # print(reasoning)
    # print(answer)

    stream_chat_with_image = client.stream_chat_with_image(
        image_url="https://img.alicdn.com/imgextra/i1/O1CN01gDEY8M1W114Hi3XcN_!!6000000002727-0-tps-1024-406.jpg",
        text="请描述这张图片",
    )
    for chunk in stream_chat_with_image:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if hasattr(delta, "reasoning_content") and delta.reasoning_content is not None:
            print(delta.reasoning_content, end="", flush=True)
        else:
            print(delta.content, end="", flush=True)