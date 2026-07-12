import time
import json
import os
import sys
from datetime import datetime
from youtube_upload import upload_video

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "OUTPUT"))
QUEUE_FILE = os.path.join(OUTPUT_DIR, "scheduled_uploads.json")

def process_queue():
    if not os.path.exists(QUEUE_FILE):
        return False
        
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        try:
            queue = json.load(f)
        except Exception:
            queue = []
            
    if not queue:
        return False
        
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking scheduled beats...")
    
    # Find all items scheduled for current hour, or items with no specific hour (default to 22)
    current_hour = datetime.now().hour
    
    # Pop the first one that matches the current hour
    item_index = -1
    for i, item in enumerate(queue):
        item_hour = int(item.get("schedule_hour", 22))
        if item_hour == current_hour:
            item_index = i
            break
            
    if item_index == -1:
        return False

    item = queue.pop(item_index)
    
    print(f"Uploading: {item.get('title')}...")
    
    result = upload_video(
        mp4_path=item.get("mp4_path"),
        title=item.get("title", ""),
        description=item.get("description", ""),
        tags=item.get("tags", []),
        category_id=item.get("category_id", "10"),
        privacy_status=item.get("privacy_status", "public"),
        thumbnail_path=item.get("thumbnail_path")
    )
    
    if result.get("success"):
        print(f"âœ… Success: {result.get('video_url')}")
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=4)
        return True
    else:
        print(f"âŒ Upload failed: {result.get('error')}")
        # Insert back to top of queue to retry tomorrow or manually
        queue.insert(0, item)
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=4)
        return False

if __name__ == "__main__":
    print("====================================")
    print("  JETBOX Auto-Uploader Active       ")
    print("  Target Upload Time: Hourly        ")
    print("====================================")
    
    last_upload_date = None
    
    while True:
        try:
            now = datetime.now()
            current_date = now.date()
            
            # Trigger exactly on the hour
            if now.minute == 0:
                if last_upload_date != f"{current_date}_{now.hour}":
                    print(f"\n[SCHEDULE TRIGGER] {now.hour}:00 Initiated...")
                    while process_queue():  # Process all items for this hour
                        time.sleep(5)
                    last_upload_date = f"{current_date}_{now.hour}"
            
            time.sleep(30)
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
            sys.exit(0)
        except Exception as e:
            print(f"Scheduler error: {e}")
            time.sleep(30)

