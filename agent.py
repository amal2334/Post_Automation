import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from groq import Groq
from mastodon import Mastodon
from huggingface_hub import InferenceClient
import io
import time
import random  

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MASTODON_TOKEN = os.getenv('MASTODON_TOKEN')
HF_TOKEN = os.getenv('HF_TOKEN')

def get_next_topic():
    """Sequential topics from General_facts.xlsx - ENDLESS CYCLE"""
    df = pd.read_excel('General_facts.xlsx')
    
    try:
        posted_df = pd.read_csv('posted_topics.csv', header=None, names=['index'])
        posted_indices = posted_df['index'].tolist()
    except FileNotFoundError:
        posted_indices = []
    
    # Calculate cycle position - always sequential
    cycle_position = len(posted_indices) % len(df)  #  ENDLESS LOOP
    next_idx = cycle_position
    
    topic = df.loc[next_idx, 'topic']
    
    # Always append to track total posts
    new_post = pd.DataFrame({'index': [next_idx]})
    new_post.to_csv('posted_topics.csv', mode='a', header=not os.path.exists('posted_topics.csv'), index=False)
    
    cycle_num = (len(posted_indices) // len(df)) + 1
    print(f" Cycle {cycle_num} #{cycle_position+1}/{len(df)}: '{topic}'")
    return topic

def generate_creative_image(topic):
    """Try HF → Return None for text-only"""
    try:
        print("  Trying HF image...")
        client = InferenceClient(
            model="stabilityai/stable-diffusion-xl-base-1.0",
            token=HF_TOKEN
        )
        
        styles = ["vibrant illustration", "artistic concept", "stylized graphic", "surreal art"]
        style = random.choice(styles)
        prompt = f"{topic}, {style}, square social art"
        
        image = client.text_to_image(prompt)
        print("HF image ready!")
        return image
        
    except:
        print("  HF failed → TEXT-ONLY post")
        return None

def main():
    if not all([GROQ_API_KEY, MASTODON_TOKEN]):
        print(" Missing keys!")
        return
    
    print(f"\n THESIS AGENT {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    topic = get_next_topic()
    
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{
            "role": "user", 
            "content": f"""Write EXACTLY under 450 chars about '{topic}':

1. **QUESTION or STATISTIC** (1 line)
2. INFO (2 sentences max)  
3. CONCLUSION / quote
4. Invite opinion/funny question
5. 3 hashtags

EXAMPLE:
"Did you know pet owners are 60% less lonely?

Pets provide companionship + purpose.

Game-changer for mental health.

What's your favorite pet benefit?

#MentalHealth #Pets #Wellbeing"

CRITICAL: MAX 450 CHARS. Topic: '{topic}'."""
        }],
        max_tokens=150,
        temperature=0.8
    )
    
    content = response.choices[0].message.content.strip()[:480]
    print(f" ({len(content)} chars):\n{content}")
    
    image = generate_creative_image(topic)
    
    mastodon = Mastodon(access_token=MASTODON_TOKEN, api_base_url="https://mastodon.social")
    
    if image is not None:
        print(" TEXT + IMAGE...")
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        media = mastodon.media_post(img_buffer, "thesis_image.png")
        post = mastodon.status_post(content, media_ids=[media['id']])
        print(f" TEXT+IMAGE: {post['url']}")
    else:
        print(" TEXT-ONLY...")
        post = mastodon.status_post(content)
        print(f" TEXT-ONLY: {post['url']}")
    
    print("ENDLESS CYCLE SUCCESS!")

if __name__ == "__main__":
    main()

