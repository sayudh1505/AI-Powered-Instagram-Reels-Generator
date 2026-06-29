import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip, vfx
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
from config import ASSETS_DIR, CATEGORY_SETTINGS, VIDEO_WIDTH, VIDEO_HEIGHT

def create_subtitle_clip(text: str, duration: float, font_size: int = 46, font_color = (255, 255, 255)) -> ImageClip:
    """
    Creates a transparent ImageClip with styled subtitle text overlay.
    Avoids ImageMagick dependency issues by rendering text using Pillow.
    """
    # Create transparent canvas (RGBA)
    canvas = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    
    # Select font
    font = None
    # List of common system fonts to try
    font_paths = [
        "arial.ttf",          # Windows standard
        "msyh.ttc",           # Windows alternate
        "Helvetica.ttf",      # macOS standard
        "LiberationSans-Regular.ttf" # Linux standard
    ]
    
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, font_size)
            break
        except IOError:
            continue
            
    if font is None:
        font = ImageFont.load_default()

    # Split text into lines if too long for screen width
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        # Check width of test line
        if hasattr(draw, "textlength"):
            w = draw.textlength(test_line, font=font)
        else:
            w = len(test_line) * (font_size * 0.5)
            
        if w < (VIDEO_WIDTH - 80): # Margin of 40px on each side
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    # Calculate starting y position (lower third of screen)
    line_height = font_size + 8
    total_height = len(lines) * line_height
    y_start = int(VIDEO_HEIGHT * 0.75) - (total_height // 2)

    for i, line in enumerate(lines):
        line_y = y_start + (i * line_height)
        
        # Calculate x coordinate to center the line
        if hasattr(draw, "textlength"):
            line_w = draw.textlength(line, font=font)
        else:
            line_w = len(line) * (font_size * 0.5)
            
        line_x = (VIDEO_WIDTH - line_w) // 2
        
        # Draw background shadow/outline for contrast
        outline_color = (0, 0, 0, 255)
        outline_width = 3
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((line_x + dx, line_y + dy), line, fill=outline_color, font=font)
                    
        # Draw main text
        draw.text((line_x, line_y), line, fill=font_color + (255,), font=font)

    # Convert PIL RGBA image to numpy arrays for MoviePy
    img_array = np.array(canvas)
    rgb_array = img_array[:, :, :3]
    alpha_array = img_array[:, :, 3] / 255.0  # Normalize to 0.0-1.0
    
    # Create the ImageClip and its alpha mask
    text_clip = ImageClip(rgb_array).with_duration(duration)
    mask_clip = ImageClip(alpha_array, is_mask=True).with_duration(duration)
    
    return text_clip.with_mask(mask_clip).with_position(("center", "center"))

def compile_reel(scenes_data: list, output_video_path: str, category: str = "educational") -> bool:
    """
    Compiles generated video clips, voiceovers, and subtitles into a single Instagram Reel.
    Merges background music if available in the assets folder.
    """
    try:
        print("[VideoCompiler] Starting compilation pipeline...")
        settings = CATEGORY_SETTINGS.get(category.lower(), CATEGORY_SETTINGS["educational"])
        subtitle_color = settings.get("subtitle_color", (255, 255, 255))
        subtitle_font_size = settings.get("subtitle_font_size", 44)
        
        processed_clips = []
        
        # 1. Assemble individual scenes
        for scene in scenes_data:
            num = scene["scene_number"]
            video_path = scene["video_path"]
            audio_path = scene["audio_path"]
            overlay_text = scene["overlay_text"]
            
            print(f"[VideoCompiler] Processing Scene {num}: {overlay_text}")
            
            # Load assets
            video_clip = VideoFileClip(video_path)
            voice_clip = AudioFileClip(audio_path)
            
            audio_duration = voice_clip.duration
            
            # Synchronize video duration with audio duration
            if video_clip.duration < audio_duration:
                # Loop video to match audio
                print(f"[VideoCompiler] Loop video from {video_clip.duration:.2f}s to {audio_duration:.2f}s")
                video_clip = video_clip.with_effects([vfx.Loop(duration=audio_duration)])
            else:
                # Crop video to match audio
                print(f"[VideoCompiler] Crop video from {video_clip.duration:.2f}s to {audio_duration:.2f}s")
                video_clip = video_clip.subclipped(0, audio_duration)
                
            # Set audio
            video_clip = video_clip.with_audio(voice_clip)
            
            # Generate and composite subtitle overlay
            subtitle_clip = create_subtitle_clip(
                text=overlay_text, 
                duration=audio_duration, 
                font_size=subtitle_font_size, 
                font_color=subtitle_color
            )
            
            # Combine video and subtitle
            scene_composite = CompositeVideoClip([video_clip, subtitle_clip])
            processed_clips.append(scene_composite)
            
        # 2. Concatenate all scenes
        print("[VideoCompiler] Concatenating scenes...")
        final_video = concatenate_videoclips(processed_clips, method="compose")
        total_duration = final_video.duration
        print(f"[VideoCompiler] Concatenated video duration: {total_duration:.2f} seconds")
        
        # 3. Add background music if available
        bg_music_path = None
        default_music_name = settings.get("default_music", "")
        default_music_path = ASSETS_DIR / default_music_name
        
        if default_music_path.exists():
            bg_music_path = default_music_path
        else:
            # Look for any mp3 in assets as fallback
            mp3_files = list(ASSETS_DIR.glob("*.mp3"))
            if mp3_files:
                bg_music_path = mp3_files[0]
                print(f"[VideoCompiler] Default music '{default_music_name}' not found. Using fallback: {bg_music_path.name}")
                
        if bg_music_path:
            print(f"[VideoCompiler] Mixing background music: {bg_music_path.name}...")
            bg_music = AudioFileClip(str(bg_music_path))
            
            # Loop music to match video duration and scale down volume
            bg_music = bg_music.loop(duration=total_duration)
            bg_volume = settings.get("bg_music_volume", 0.1)
            bg_music = bg_music.with_volume_scaled(bg_volume)
            
            # Composite original audio (voiceover) and music
            voiceover_audio = final_video.audio
            composite_audio = CompositeAudioClip([voiceover_audio, bg_music])
            final_video = final_video.with_audio(composite_audio)
        else:
            print("[VideoCompiler] Background music not found in assets directory. Compiling with voiceover only.")
            
        # 4. Write final output file
        print(f"[VideoCompiler] Writing final output video to: {output_video_path}")
        
        # Using libx264/aac for high compatibility with platforms (9:16 vertical standard)
        final_video.write_videofile(
            output_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            preset="medium",
            logger=None  # Cleans up console logs
        )
        
        # Close all clips to release file system handles
        final_video.close()
        for clip in processed_clips:
            clip.close()
            
        print("[VideoCompiler] Video compilation successfully completed!")
        return True
        
    except Exception as e:
        print(f"[VideoCompiler] Compile error: {e}")
        return False
