from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from openai import OpenAI
import base64
import os


class GenerateCoverImageInput(BaseModel):
    prompt: str = Field(..., description="英文 image prompt，用於生成封面插圖")


class GenerateCoverImageTool(BaseTool):
    name: str = "generate_cover_image"
    description: str = (
        "根據提供的英文 prompt，呼叫 OpenAI gpt-image-1 生成封面插圖，"
        "並將圖片儲存為 cover.png。"
    )
    args_schema: type[BaseModel] = GenerateCoverImageInput

    def _run(self, prompt: str) -> str:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="medium",
            n=1,
        )

        image_base64 = response.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        output_path = "cover.png"
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        return f"封面插圖已成功生成並儲存為 {output_path}。Prompt：{prompt}"
