import os
import time
import requests
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from runwayml import RunwayML
from config import RUNWAYML_API_SECRET, RUNWAYML_MODEL, TEMP_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, DEFAULT_FPS

def generate_mock_video(prompt: str, output_path: str, duration: int = 5) -> bool:
    """
    Generates a beautiful mock vertical 9:16 video clip using OpenCV and Pillow.
    Renders a dynamic shifting gradient background, floating particles, and rotating neon geometric rings.
    """
    try:
        print(f"[VideoGenerator] Generating premium mock video for prompt: '{prompt[:45]}...'")
        
        # Video settings
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, DEFAULT_FPS, (VIDEO_WIDTH, VIDEO_HEIGHT))
        
        num_frames = int(duration * DEFAULT_FPS)
        
        # Color palette for background gradient (cyberpunk/synthwave look)
        color_start_base = np.array([30, 10, 50])  # Deep violet
        color_end_base = np.array([10, 10, 30])    # Deep space blue
        
        # Initialize floating particles
        np.random.seed(42)
        particles = []
        for _ in range(35):
            particles.append({
                "x": np.random.randint(0, VIDEO_WIDTH),
                "y": np.random.randint(0, VIDEO_HEIGHT),
                "speed_y": np.random.uniform(1.2, 3.2),
                "sway_amp": np.random.uniform(12, 28),
                "sway_freq": np.random.uniform(0.02, 0.05),
                "radius": np.random.randint(3, 10),
                "color": (
                    np.random.randint(100, 255),  # R
                    np.random.randint(120, 255),  # G
                    np.random.randint(200, 255),  # B
                    np.random.randint(40, 160)    # Alpha
                )
            })
            
        for frame_idx in range(num_frames):
            # 1. Shifting background gradient
            progress = frame_idx / num_frames
            t = np.sin(progress * np.pi)  # 0 -> 1 -> 0
            
            # Interpolate base colors over time for shifting effect
            shift_color_start = color_start_base + np.array([int(t * 15), 0, int(t * 10)])
            shift_color_end = color_end_base + np.array([0, int(t * 12), int(t * 15)])
            
            # Create base background canvas
            img = np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
            for y in range(VIDEO_HEIGHT):
                y_factor = y / VIDEO_HEIGHT
                c = shift_color_start * (1 - y_factor) + shift_color_end * y_factor
                img[y, :] = np.clip(c, 0, 255).astype(np.uint8)
                
            # Convert to PIL Image for drawing transparent overlays
            pil_img = Image.fromarray(img).convert("RGBA")
            overlay = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # 2. Draw animated perspective lines at the bottom third (cyber-grid)
            grid_y_horizon = int(VIDEO_HEIGHT * 0.8)
            overlay_draw.line([(0, grid_y_horizon), (VIDEO_WIDTH, grid_y_horizon)], fill=(0, 255, 255, 60), width=2)
            
            # Perspective lines radiating from center horizon
            horizon_x = VIDEO_WIDTH // 2
            for i in range(-5, 6):
                x_edge = horizon_x + i * (VIDEO_WIDTH // 4)
                overlay_draw.line([(horizon_x, grid_y_horizon), (x_edge, VIDEO_HEIGHT)], fill=(0, 255, 255, 40), width=1)
                
            # Moving horizontal lines (coming forward)
            for j in range(5):
                line_progress = ((frame_idx * 0.015) + (j / 5.0)) % 1.0
                line_y = grid_y_horizon + int(line_progress * (VIDEO_HEIGHT - grid_y_horizon))
                opacity = int(line_progress * 100)
                overlay_draw.line([(0, line_y), (VIDEO_WIDTH, line_y)], fill=(0, 255, 255, opacity), width=1)
            
            # 3. Update and draw particles
            for p in particles:
                p["y"] -= p["speed_y"]
                if p["y"] < -20:
                    p["y"] = VIDEO_HEIGHT + 20
                    p["x"] = np.random.randint(0, VIDEO_WIDTH)
                    
                x_sway = np.sin(frame_idx * p["sway_freq"]) * p["sway_amp"]
                px = int(p["x"] + x_sway)
                py = int(p["y"])
                r = p["radius"]
                
                # Draw outer glow circle
                overlay_draw.ellipse([px - r - 4, py - r - 4, px + r + 4, py + r + 4], fill=p["color"][:-1] + (p["color"][-1] // 3,))
                # Draw core circle
                overlay_draw.ellipse([px - r, py - r, px + r, py + r], fill=p["color"])
                
            # 4. Draw central rotating geometric rings (representing AI generation processing)
            center_x, center_y = VIDEO_WIDTH // 2, VIDEO_HEIGHT // 2
            
            # Outer Ring: Rotating pentagon
            angle1 = frame_idx * 0.04
            r1 = int(120 + np.sin(frame_idx * 0.06) * 10)  # Subtle pulse
            points1 = []
            for i in range(5):
                a = angle1 + i * (2 * np.pi / 5)
                points1.append((center_x + r1 * np.cos(a), center_y + r1 * np.sin(a)))
            overlay_draw.polygon(points1, outline=(255, 0, 128, 160), width=4)
            
            # Inner Ring: Rotating square (opposite direction)
            angle2 = -frame_idx * 0.03
            r2 = 80
            points2 = []
            for i in range(4):
                a = angle2 + i * (2 * np.pi / 4)
                points2.append((center_x + r2 * np.cos(a), center_y + r2 * np.sin(a)))
            overlay_draw.polygon(points2, outline=(0, 255, 255, 180), width=3)
            
            # Center Core: Pulsing neon circle
            pulse_r = int(30 + np.sin(frame_idx * 0.08) * 6)
            overlay_draw.ellipse([center_x - pulse_r, center_y - pulse_r, center_x + pulse_r, center_y + pulse_r], fill=(255, 255, 255, 80))
            overlay_draw.ellipse([center_x - pulse_r + 4, center_y - pulse_r + 4, center_x + pulse_r - 4, center_y + pulse_r - 4], fill=(0, 255, 255, 120))
            
            # Composite overlay onto base canvas
            pil_img = Image.alpha_composite(pil_img, overlay)
            
            # 5. Draw prompt card box and text info
            draw_final = ImageDraw.Draw(pil_img)
            try:
                font = ImageFont.load_default()
            except IOError:
                font = None
                
            text_lines = [
                "🎬 [RUNWAY ML GENERATOR MOCK]",
                f"Clip Duration: {duration}s | Frame: {frame_idx}/{num_frames}",
                "Prompt text:",
                prompt[:42] + ("..." if len(prompt) > 42 else "")
            ]
            
            card_w, card_h = 420, 140
            card_x = (VIDEO_WIDTH - card_w) // 2
            card_y = 120
            
            # Draw semi-transparent card background with white border
            card_bg = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
            card_draw = ImageDraw.Draw(card_bg)
            card_draw.rounded_rectangle(
                [card_x, card_y, card_x + card_w, card_y + card_h], 
                radius=10, 
                fill=(0, 0, 0, 200), 
                outline=(255, 255, 255, 180), 
                width=2
            )
            pil_img = Image.alpha_composite(pil_img, card_bg)
            
            # Write text lines inside card
            y_offset = card_y + 15
            draw_text_only = ImageDraw.Draw(pil_img)
            for line in text_lines:
                w = draw_text_only.textlength(line, font=font) if hasattr(draw_text_only, "textlength") else len(line) * 6
                x = (VIDEO_WIDTH - w) // 2
                draw_text_only.text((x, y_offset), line, fill=(255, 255, 255), font=font)
                y_offset += 28
                
            # Convert PIL image back to CV2 format (BGR) for writing
            frame = np.array(pil_img.convert("RGB"))
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            out.write(frame)
            
        out.release()
        print(f"[VideoGenerator] Premium mock video successfully saved to {output_path}")
        return True
    except Exception as e:
        print(f"[VideoGenerator] Error generating mock video: {e}")
        return False

def generate_video_clip(prompt: str, output_path: str, use_mock: bool = False, duration: int = 5) -> bool:
    """
    Generates a vertical video clip from a text prompt.
    Uses RunwayML in production mode, and generates a mock video in dry-run mode.
    """
    if use_mock or not RUNWAYML_API_SECRET:
        if not use_mock:
            print("[VideoGenerator] Warning: RUNWAYML_API_SECRET not found. Falling back to mock video.")
        return generate_mock_video(prompt, output_path, duration)
        
    try:
        print(f"[VideoGenerator] Initiating RunwayML generation for prompt: '{prompt[:45]}...'")
        client = RunwayML(api_key=RUNWAYML_API_SECRET)
        
        # Initiate the text-to-video generation task
        task = client.text_to_video.create(
            model=RUNWAYML_MODEL,
            prompt_text=prompt,
            ratio="720:1280",  # Vertical video
            duration=duration
        )
        
        task_id = task.id
        print(f"[VideoGenerator] RunwayML task created with ID: {task_id}")
        
        # Poll Runway task status until complete
        max_attempts = 60  # Wait up to 10 minutes
        attempt = 0
        
        while attempt < max_attempts:
            task_status = client.tasks.retrieve(task_id)
            status = task_status.status.upper()
            
            print(f"[VideoGenerator] Task {task_id} status: {status} (Attempt {attempt+1}/{max_attempts})")
            
            if status == "SUCCEEDED":
                # Get output video URL
                if task_status.output and len(task_status.output) > 0:
                    video_url = task_status.output[0]
                    print(f"[VideoGenerator] Task succeeded. Downloading video from {video_url}...")
                    
                    # Download video file
                    response = requests.get(video_url, stream=True)
                    response.raise_for_status()
                    
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                
                    print(f"[VideoGenerator] Video downloaded and saved to {output_path}")
                    return True
                else:
                    raise Exception("Task succeeded but output list is empty.")
                    
            elif status in ["FAILED", "CANCELLED"]:
                raise Exception(f"RunwayML task failed or was cancelled with status: {status}")
                
            # Sleep and increment attempt counter
            time.sleep(10)
            attempt += 1
            
        raise TimeoutError("RunwayML generation timed out.")
        
    except Exception as e:
        print(f"[VideoGenerator] RunwayML generation failed: {e}. Falling back to mock video generation.")
        return generate_mock_video(prompt, output_path, duration)

if __name__ == "__main__":
    # Test mock generation
    test_prompt = "A dramatic sunrise over a futuristic city, cyberpunk style, neon lights."
    test_output = str(TEMP_DIR / "test_video.mp4")
    generate_video_clip(test_prompt, test_output, use_mock=True, duration=4)
