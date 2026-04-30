import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()


def generate_x_post(usr_input: str) -> str:
    with open("post-examples.json", "r") as f:
        examples = json.load(f)

    examples_str = ""
    for i, example in enumerate(examples, 1):
        examples_str += f"""
        <example-{i}>
            <topic>
            {example['topic']}
            </topic>

            <generated-post>
            {example['post']}
            </generated-post>
        </example-{i}>
        """
    prompt = f"""
        你是一位專業的社群媒體經理，擅長在 X 上撰寫容易引發瘋傳且具備高互動性的貼文。
        你的任務是根據使用者提供的 usr_input（輸入內容），生成一篇簡潔有力、且量身打造的貼文。
        請避免使用標籤Hashtags以及大量的表情符號（可以少量使用，但切勿過多）。
        貼文請保持簡短且聚焦，並以乾淨、易讀的方式編排結構，善用換行與空行來提升閱讀體驗。
        以下是使用者提供、需要你據此生成貼文的 usr_input：
        <topic>
        {usr_input}
        </topic>
        以下是主題與對應生成貼文的範例：
        <examples>
        {examples_str}
        </examples>
        請參考上方範例中的語氣、語言、結構與風格，生成一篇與使用者提供的主題相關且具吸引力的繁體中文貼文。
        請勿直接使用範例中的內容！
    """
    response = client.responses.create(model="gpt-4o", input=prompt)

    return response.output_text


def main():
    # user input => AI (LLM) to generate X post => output post

    usr_input = input("這次文章的主題想要討論什麼? ")
    x_post = generate_x_post(usr_input)
    print("Generated X post")
    print(x_post)


if __name__ == "__main__":
    main()