import os
import json
import google.generativeai as genai
from config import GEMINI_API_KEY, CATEGORY_SETTINGS, TEMP_DIR

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    model = None

def generate_reel_script(topic: str, category: str) -> dict:
    """
    Generates a structured script and video prompts for an Instagram Reel
    based on a topic and category (motivational, educational, product).
    """
    if not model:
        raise ValueError("Gemini API key is missing. Please check your .env file.")
    
    settings = CATEGORY_SETTINGS.get(category.lower(), CATEGORY_SETTINGS["educational"])
    style_suffix = settings["style_prompt_suffix"]
    
    prompt = f"""
You are an expert Instagram Reels and YouTube Shorts content creator. 
Create an engaging, viral vertical video script based on the following:

Topic: {topic}
Category: {category.upper()}
Visual Style Guideline: {style_suffix}

Guidelines:
1. The total video duration should be around 15 to 20 seconds.
2. Structure the script into exactly 4 sequential scenes/segments.
3. Keep the narration for each scene brief (approx. 10-15 words) so it matches a 4-5 second segment and sounds natural when spoken.
4. For each scene, create a detailed "visual_prompt" for Runway ML (Text-to-Video). The prompt must be cinematic, descriptive, vertical 9:16 aspect ratio, specify subject and motion (e.g. slow zoom, panning), and MUST integrate the style guideline: "{style_suffix}".
5. For each scene, specify the "overlay_text" which represents the subtitle caption that will be displayed on screen. Make it short (3-6 words, high impact) matching the narration.

Return ONLY a valid JSON object matching the following structure:
{{
  "title": "A short, viral title with emojis",
  "category": "{category}",
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "First sentence of narration (e.g., 'Do you want to know the secret to doubling your productivity?')",
      "visual_prompt": "Runway ML visual prompt. Must include camera motion and style keywords.",
      "overlay_text": "DOUBLE YOUR PRODUCTIVITY"
    }},
    {{
      "scene_number": 2,
      "narration": "Second sentence of narration...",
      "visual_prompt": "Runway ML visual prompt...",
      "overlay_text": "THE KEY IS FOCUS"
    }},
    {{
      "scene_number": 3,
      "narration": "Third sentence of narration...",
      "visual_prompt": "Runway ML visual prompt...",
      "overlay_text": "ELIMINATE ALL DISTRACTIONS"
    }},
    {{
      "scene_number": 4,
      "narration": "Fourth sentence of narration (Call to action, e.g., 'Try this today. Comment below and follow for more!')",
      "visual_prompt": "Runway ML visual prompt...",
      "overlay_text": "FOLLOW FOR MORE"
    }}
  ]
}}
"""

    try:
        print(f"[PromptManager] Generating structured {category} script for topic: '{topic}'...")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        script_data = json.loads(response.text)
        
        # Save generated script to temp directory for reference
        output_path = TEMP_DIR / "generated_script.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(script_data, f, indent=2)
            
        print(f"[PromptManager] Script successfully generated and saved to {output_path}")
        return script_data
        
    except Exception as e:
        print(f"[PromptManager] Error generating script: {e}")
        return None

if __name__ == "__main__":
    # Test script generation
    test_topic = "Unlocking maximum mental clarity"
    test_category = "motivational"
    result = generate_reel_script(test_topic, test_category)
    if result:
        print(json.dumps(result, indent=2))
