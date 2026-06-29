import os
import sys
import argparse
import shutil
import time
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from config import TEMP_DIR, OUTPUT_DIR, ASSETS_DIR
from prompt_manager import generate_reel_script
from voice_generator import generate_voiceover
from video_generator import generate_video_clip
from video_compiler import compile_reel

def cleanup_temp_files():
    """
    Cleans up all intermediate files generated in the temp directory.
    """
    print("[Orchestrator] Cleaning up intermediate files in temp/...")
    for f in TEMP_DIR.glob("*"):
        try:
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                shutil.rmtree(f)
        except Exception as e:
            print(f"[Orchestrator] Failed to delete {f}: {e}")

def main():
    # Avoid UnicodeEncodeError in Windows terminal output (when printing emojis)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="AI-Powered Instagram Reels Generator")
    parser.add_argument("--topic", type=str, required=False, default=None, help="Main topic/concept for the Reel")
    parser.add_argument(
        "--category", 
        type=str, 
        choices=["motivational", "educational", "product"], 
        default="educational", 
        help="Style and tone category for the Reel"
    )
    parser.add_argument("--mock", action="store_true", help="Run in mock mode using free gTTS and mock video slides")
    parser.add_argument("--clean", action="store_true", help="Delete temporary scene files after generation completes")
    
    args = parser.parse_args()
    
    topic = args.topic
    category = args.category
    mock = args.mock
    clean = args.clean
    
    # Interactive Prompts if no topic is provided via CLI
    if not topic:
        print("\n" + "=" * 60)
        print("         AI INSTAGRAM REELS GENERATOR - INTERACTIVE MODE")
        print("=" * 60)
        try:
            topic = input("Enter the topic/theme for your Reel: ").strip()
            while not topic:
                topic = input("Topic cannot be empty. Enter topic: ").strip()
                
            print("\nSelect a category:")
            print("1. Motivational (epic, cinematic, dramatic)")
            print("2. Educational (clean, minimal, professional) [Default]")
            print("3. Product (sleek, luxury showcase)")
            cat_choice = input("Enter number (1-3) or name: ").strip().lower()
            if cat_choice in ["1", "motivational"]:
                category = "motivational"
            elif cat_choice in ["3", "product"]:
                category = "product"
            else:
                category = "educational"
                
            mock_choice = input("\nRun in Mock Mode (Free/Uses local gTTS & OpenCV slides) [Y/n]? ").strip().lower()
            mock = mock_choice not in ["n", "no"]
            
            clean_choice = input("\nDelete temporary scene files upon completion [y/N]? ").strip().lower()
            clean = clean_choice in ["y", "yes"]
            print()
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled. Exiting.")
            sys.exit(0)
            
    print("=" * 60)
    print("       STARTING INSTAGRAM REELS GENERATOR PIPELINE")
    print(f"       Topic: {topic}")
    print(f"       Category: {category.upper()}")
    print(f"       Mode: {'MOCK (Free)' if mock else 'PRODUCTION (Runway & ElevenLabs)'}")
    print("=" * 60)
    
    start_time = time.time()
    
    # 1. Generate Script
    script_data = generate_reel_script(topic, category)
    if not script_data:
        print("[Orchestrator] Error: Failed to generate script. Exiting.")
        sys.exit(1)
        
    print(f"\n[Orchestrator] Generated Script Title: {script_data.get('title', 'Untitled')}")
    
    # 2. Generate Audio & Video Assets for each scene
    scenes = script_data.get("scenes", [])
    if not scenes:
        print("[Orchestrator] Error: No scenes found in generated script. Exiting.")
        sys.exit(1)
        
    for scene in scenes:
        num = scene["scene_number"]
        narration = scene["narration"]
        visual_prompt = scene["visual_prompt"]
        
        print(f"\n--- Processing Scene {num}/{len(scenes)} ---")
        
        # Paths for generated assets
        scene_audio_path = str(TEMP_DIR / f"scene_{num}_voice.mp3")
        scene_video_path = str(TEMP_DIR / f"scene_{num}_video.mp4")
        
        # A. Voiceover Generation
        voice_success = generate_voiceover(
            text=narration, 
            output_path=scene_audio_path, 
            use_mock=mock, 
            category=category
        )
        if not voice_success:
            print(f"[Orchestrator] Error generating voiceover for Scene {num}. Aborting.")
            sys.exit(1)
            
        # B. Video Clip Generation
        video_success = generate_video_clip(
            prompt=visual_prompt, 
            output_path=scene_video_path, 
            use_mock=mock, 
            duration=5  # Default clip length
        )
        if not video_success:
            print(f"[Orchestrator] Error generating video clip for Scene {num}. Aborting.")
            sys.exit(1)
            
        # Update scene dictionary with generated paths
        scene["audio_path"] = scene_audio_path
        scene["video_path"] = scene_video_path

    # 3. Assemble and Compile Reel
    print("\n--- Compiling Final Reel ---")
    safe_topic = "".join([c if c.isalnum() else "_" for c in topic])[:30]
    output_filename = f"reel_{safe_topic}_{category}_{int(time.time())}.mp4"
    output_path = str(OUTPUT_DIR / output_filename)
    
    compilation_success = compile_reel(
        scenes_data=scenes, 
        output_video_path=output_path, 
        category=category
    )
    
    if not compilation_success:
        print("[Orchestrator] Error compiling the final reel. Exiting.")
        sys.exit(1)
        
    print("\n" + "=" * 60)
    print("       PIPELINE SUCCESSFULLY COMPLETED!")
    print(f"       Output File: {output_path}")
    print(f"       Total Execution Time: {time.time() - start_time:.2f} seconds")
    print("=" * 60)
    
    # 4. Clean up temporary files if requested
    if clean:
        cleanup_temp_files()
    else:
        print("[Orchestrator] Note: Temporary scene files have been kept in the temp/ directory.")

if __name__ == "__main__":
    main()
