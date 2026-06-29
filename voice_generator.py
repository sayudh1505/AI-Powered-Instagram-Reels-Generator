import os
from gtts import gTTS
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, CATEGORY_SETTINGS, TEMP_DIR

def generate_voiceover(text: str, output_path: str, use_mock: bool = False, category: str = "educational") -> bool:
    """
    Generates a voiceover file for a given text segment.
    Uses gTTS for mock/free mode, and ElevenLabs for production mode.
    """
    if use_mock or not ELEVENLABS_API_KEY:
        if not use_mock:
            print("[VoiceGenerator] Warning: ELEVENLABS_API_KEY not found. Falling back to free gTTS.")
        try:
            print(f"[VoiceGenerator] Generating mock voiceover (gTTS) for: '{text[:30]}...'")
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_path)
            print(f"[VoiceGenerator] Voiceover saved to {output_path}")
            return True
        except Exception as e:
            print(f"[VoiceGenerator] Error generating mock voiceover: {e}")
            return False
    else:
        try:
            print(f"[VoiceGenerator] Requesting ElevenLabs voiceover for: '{text[:30]}...'")
            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            
            # Retrieve voice settings based on category
            settings = CATEGORY_SETTINGS.get(category.lower(), CATEGORY_SETTINGS["educational"])
            
            audio = client.text_to_speech.convert(
                text=text,
                voice_id=ELEVENLABS_VOICE_ID,
                model_id="eleven_flash_v2_5",  # Low latency, high quality
                voice_settings=VoiceSettings(
                    stability=settings.get("voice_stability", 0.50),
                    similarity_boost=settings.get("voice_similarity", 0.85),
                    style=0.0,
                    use_speaker_boost=True
                )
            )
            
            # Save audio generator chunks to file
            with open(output_path, "wb") as f:
                for chunk in audio:
                    if chunk:
                        f.write(chunk)
                        
            print(f"[VoiceGenerator] ElevenLabs voiceover saved to {output_path}")
            return True
        except Exception as e:
            print(f"[VoiceGenerator] ElevenLabs error: {e}. Falling back to gTTS...")
            # Fallback to gTTS on failure
            try:
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(output_path)
                print(f"[VoiceGenerator] Fallback gTTS voiceover saved to {output_path}")
                return True
            except Exception as fe:
                print(f"[VoiceGenerator] Critical error generating fallback voiceover: {fe}")
                return False

if __name__ == "__main__":
    # Test voice generation in mock mode
    test_text = "This is a test of the automated reels voice generator system."
    test_output = str(TEMP_DIR / "test_voice.mp3")
    generate_voiceover(test_text, test_output, use_mock=True)
