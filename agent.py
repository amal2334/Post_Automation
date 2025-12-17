import os
from dotenv import load_dotenv  # ADD THIS!
import pandas as pd
from datetime import datetime
from groq import Groq
from mastodon import Mastodon
from huggingface_hub import InferenceClient
from PIL import Image
import time

# LOAD .env (LOCAL VS CODE)
load_dotenv()  # ADD THIS!

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MASTODON_TOKEN = os.getenv('MASTODON_TOKEN')
HF_TOKEN = os.getenv('HF_TOKEN')

# DEBUG: Check if keys loaded
print(f"🔑 GROQ: {'OK' if GROQ_API_KEY else 'MISSING'}")
print(f"🔑 Mastodon: {'OK' if MASTODON_TOKEN else 'MISSING'}")
print(f"🔑 HF: {'OK' if HF_TOKEN else 'MISSING'}")

def main():
    if not all([GROQ_API_KEY, MASTODON_TOKEN, HF_TOKEN]):
        print("❌ MISSING API KEYS! Check .env file")
        return
    
    print(f"\n🚀 THESIS AI AGENT {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 1. Excel
    df = pd.read_excel('topics.xlsx')
    topic = df.iloc[0]['topic']
    print(f"✅ Topic: '{topic}'")

    # 2. Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"SHORT 300 char post about '{topic}'. 3 hashtags."}],
        max_tokens=100
    )
    content = response.choices[0].message.content.strip()[:450]
    print(f"📝 Post ({len(content)} chars): {content}")

    # 3. HF Image
    hf_client = InferenceClient(
        model="stabilityai/stable-diffusion-xl-base-1.0",
        token=HF_TOKEN
    )
    image = hf_client.text_to_image(f"data science {topic}, modern blue flat design")
    image_path = f"thesis_image_{int(time.time())}.png"
    image.save(image_path)
    print(f"✅ Image: {image_path}")

    # 4. Mastodon
    mastodon = Mastodon(access_token=MASTODON_TOKEN, api_base_url="https://mastodon.social")
    media = mastodon.media_post(image_path)
    post = mastodon.status_post(content, media_ids=[media['id']])
    print(f"🎉 LIVE: {post['url']}")

if __name__ == "__main__":
    main()
