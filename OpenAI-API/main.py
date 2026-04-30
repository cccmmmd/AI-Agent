import os

import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def generate_x_post(usr_input: str) -> str:
    
    prompt = f"""
        你是一位專業的社群媒體經理，擅長在 X 上撰寫容易引發瘋傳且具備高互動性的貼文。
        你的任務是根據使用者提供的 usr_input（輸入內容），生成一篇簡潔有力、且量身打造的貼文。
        請避免使用標籤Hashtags以及大量的表情符號（可以少量使用，但切勿過多）。
        貼文請保持簡短且聚焦，並以乾淨、易讀的方式編排結構，善用換行與空行來提升閱讀體驗。
        以下是使用者提供、需要你據此生成貼文的 usr_input：
        <topic>
        {usr_input}
        </topic>
    """
    payload = {
        "model": "gpt-4o",
        "input": prompt
    }
    response = requests.post(
        "https://api.openai.com/v1/responses",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
    )
    response_text = (
        response.json().get("output", [{}])[0].get("content", [{}])[0].get("text", "")
    )
    return response_text


def main():
    # user input => AI (LLM) to generate X post => output post

    usr_input = input("這次文章的主題想要討論什麼? ")
    x_post = generate_x_post(usr_input)
    print("Generated X post")
    print(x_post)


if __name__ == "__main__":
    main()