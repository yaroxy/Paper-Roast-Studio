# Please make sure the requests library is installed
# pip install requests
import base64
import os
import requests
from dotenv import load_dotenv
import re

class OCRClient:
    def __init__(self, api_url=None, token=None):
        load_dotenv()
        self.api_url = api_url or os.getenv("API_URL")
        self.token = token or os.getenv("TOKEN")

    def parse_pdf_bytes(self, file_bytes):
        if not self.api_url or not self.token:
            return "缺少 API_URL 或 TOKEN 环境变量", []
        file_data = base64.b64encode(file_bytes).decode("ascii")
        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "file": file_data,
            "fileType": 0,
            "useDocOrientationClassify": False,
            "useDocUnwarping": False,
            "useChartRecognition": False,
        }
        verify_ssl = os.getenv("VERIFY_SSL", "true").lower() not in ("false", "0", "no")
        try:
            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=30, verify=verify_ssl)
        except requests.exceptions.RequestException as e:
            return f"网络请求错误：{e}", []
        if resp.status_code != 200:
            return f"请求失败：HTTP {resp.status_code}", []
        result = resp.json().get("result", {})
        md_docs = []
        images = []
        for res in result.get("layoutParsingResults", []):
            md_text = res.get("markdown", {}).get("text", "")
            for img_path, img_url in res.get("markdown", {}).get("images", {}).items():
                if img_path and img_url:
                    md_text = md_text.replace(img_path, img_url)
                images.append(img_url)
            for _, img_url in res.get("outputImages", {}).items():
                images.append(img_url)
            md_text = re.sub(r"!\[(.*?)\]\((.*?)\)", r"<p align=\"center\"><img src=\"\2\" alt=\"\1\"/></p>", md_text)
            md_docs.append(md_text)
        markdown_combined = "\n\n".join([m for m in md_docs if m]) or "未解析到内容"
        return markdown_combined, images

    def parse_pdf_bytes_pages(self, file_bytes):
        if not self.api_url or not self.token:
            return []
        file_data = base64.b64encode(file_bytes).decode("ascii")
        headers = {
            "Authorization": f"token {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "file": file_data,
            "fileType": 0,
            "useDocOrientationClassify": False,
            "useDocUnwarping": False,
            "useChartRecognition": False,
        }
        verify_ssl = os.getenv("VERIFY_SSL", "true").lower() not in ("false", "0", "no")
        try:
            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=30, verify=verify_ssl)
        except requests.exceptions.RequestException:
            return []
        if resp.status_code != 200:
            return []
        result = resp.json().get("result", {})
        pages = []
        for res in result.get("layoutParsingResults", []):
            md_text = res.get("markdown", {}).get("text", "")
            page_images = []
            for img_path, img_url in res.get("markdown", {}).get("images", {}).items():
                if img_path and img_url:
                    md_text = md_text.replace(img_path, img_url)
                if img_url:
                    page_images.append(img_url)
            for _, img_url in res.get("outputImages", {}).items():
                if img_url:
                    page_images.append(img_url)
            md_text = re.sub(r"!\[(.*?)\]\((.*?)\)", r"<p align=\"center\"><img src=\"\2\" alt=\"\1\"/></p>", md_text)
            pages.append({"markdown": md_text, "images": page_images})
        return pages

    def parse_pdf_file(self, path):
        with open(path, "rb") as f:
            return self.parse_pdf_bytes(f.read())