from typing import List, Dict

from zhipuai import ZhipuAI

from config import settings


class LLMService:
    def __init__(self, settings_obj=None):
        if settings_obj is None:
            settings_obj = settings
        self.client = ZhipuAI(api_key=settings_obj.ZHIPUAI_API_KEY)
        self.model = settings_obj.GLM_MODEL
        self.temperature = settings_obj.GLM_TEMPERATURE
        self.max_tokens = settings_obj.GLM_MAX_TOKENS

    def chat(self, messages: List[Dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content

    def stream_chat(self, messages: List[Dict]):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
