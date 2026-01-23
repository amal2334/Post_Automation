import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from groq import Groq
from mastodon import Mastodon
from huggingface_hub import InferenceClient
from PIL import Image
import io
import time
import random  


load_dotenv()


GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MASTODON_TOKEN = os.getenv('MASTODON_TOKEN')
HF_TOKEN = os.getenv('HF_TOKEN')


def get_next_topic():
    """Sequential topics (fixed CSV handling)."""
    df = pd.read_excel('General_facts.xlsx')
    
    try:
        posted_df = pd.read_csv('posted_topics.csv', header=None, names=['index'])
        posted_indices = posted_df['index'].tolist()
    except FileNotFoundError:
        posted_indices = []
    
    # Next available
    available = df[~df.index.isin(posted_indices)]
    
    if len(available) == 0:
        print("✅ Cycle complete! Resetting...")
        posted_indices = []
        available = df
    
    next_idx = available.index[0]
    topic = available.iloc[0]['topic']
    
    # Append to CSV (create if missing)
    new_post = pd.DataFrame({'index': [next_idx]})
    new_post.to_csv('posted_topics.csv', mode='a', header=not os.path.exists('posted_topics.csv'), index=False)
    
    print(f"📊 {len(posted_indices)+1}/30: '{topic}'")
    return topic


def generate_creative_image(topic):
    """Creative images."""
    client = InferenceClient(
        model="stabilityai/stable-diffusion-xl-base-1.0",
        token=HF_TOKEN
    )
    
    styles = [
        "vibrant illustration, warm tones",
        "artistic concept, earth colors", 
        "stylized graphic, autumn palette",
        "surreal art, golden lighting"
    ]
    
    style = random.choice(styles) 
    prompt = f"data science {topic}, {style}, square social art"
    
    image = client.text_to_image(prompt)
    return image


def main():
    if not all([GROQ_API_KEY, MASTODON_TOKEN, HF_TOKEN]):
        print("❌ Missing keys!")
        return
    
    print(f"\n🎯 THESIS AGENT {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    topic = get_next_topic()
    
    # Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"400 char Mastodon post '{topic}'. 3 hashtags end."}],
        max_tokens=150
    )
    content = response.choices[0].message.content.strip()[:450]
    print(f"📝 ({len(content)} chars): {content}")
    
    # HF Image
    image = generate_creative_image(topic)
    
    # BytesIO
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # Mastodon
    mastodon = Mastodon(access_token=MASTODON_TOKEN, api_base_url="https://mastodon.social")
    media = mastodon.media_post(img_buffer, "thesis_image.png")
    post = mastodon.status_post(content, media_ids=[media['id']])
    
    print(f"🎉 LIVE: {post['url']}")


if __name__ == "__main__":
    main()
