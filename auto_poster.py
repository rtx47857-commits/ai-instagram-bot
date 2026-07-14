import os
import sys
import subprocess
from instagrapi import Client
import yt_dlp
from deep_translator import GoogleTranslator

# 1. البيانات السرية وأسماء الملفات
IG_USERNAME = os.environ.get("IG_USERNAME")
IG_PASSWORD = os.environ.get("IG_PASSWORD")

LINKS_FILE = "links.txt"
ARCHIVE_FILE = "archive.txt"
SOURCE_FACE = "my_face.jpg"
TEMP_INPUT_VIDEO = "input_video.mp4"
FINAL_OUTPUT_VIDEO = "final_reel.mp4"

# هاشتاغات مستهدفة لأمريكا
US_HASHTAGS = """
.
#usa #trending #viral #fyp #ai #foryou #explore #reels #viralvideo
"""

# 2. دالة الترجمة للإنجليزية
def translate_to_english(text):
    if not text:
        return ""
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception:
        return text

# 3. قراءة رابط الصفحة
def get_page_url():
    if not os.path.exists(LINKS_FILE):
        return None
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    return lines[0] if lines else None

# 4. تحميل أحدث فيديو
def download_latest_video(page_url):
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': TEMP_INPUT_VIDEO,
        'overwrites': True,
        'download_archive': ARCHIVE_FILE,
        'playlistend': 5,
        'max_downloads': 1,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(page_url, download=True)
        if 'entries' in info:
            for entry in info['entries']:
                if entry:
                    return entry.get('title', ''), entry.get('description', '')
        else:
            return info.get('title', ''), info.get('description', '')
    return None, None

# 5. تبديل الملامح
def apply_face_swap():
    command = [
        "facefusion", "run",
        "--source", SOURCE_FACE,
        "--target", TEMP_INPUT_VIDEO,
        "--output", FINAL_OUTPUT_VIDEO,
        "--headless"
    ]
    subprocess.run(command, check=True)

# 6. النشر ف إنستغرام
def upload_to_instagram(caption_text):
    cl = Client()
    session_file = "session.json"
    if os.path.exists(session_file):
        cl.load_settings(session_file)
    cl.login(IG_USERNAME, IG_PASSWORD)
    cl.dump_settings(session_file)

    cl.clip_upload(FINAL_OUTPUT_VIDEO, caption=caption_text)

# التشغيل
if __name__ == "__main__":
    if not IG_USERNAME or not IG_PASSWORD:
        sys.exit(1)
        
    page_url = get_page_url()
    if not page_url:
        sys.exit(0)
        
    try:
        title, original_desc = download_latest_video(page_url)
        if not os.path.exists(TEMP_INPUT_VIDEO):
            sys.exit(0)
            
        # ترجمة العنوان والوصف للإنجليزية
        eng_title = translate_to_english(title)
        eng_desc = translate_to_english((original_desc or "")[:400])
        
        # تبديل الملامح
        apply_face_swap()
        
        # تحضير الوصف بالإنجليزية والهاشتاغات
        caption = f"🎬 {eng_title}\n\n{eng_desc}\n\n{US_HASHTAGS}"
        upload_to_instagram(caption)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        for f in [TEMP_INPUT_VIDEO, FINAL_OUTPUT_VIDEO]:
            if os.path.exists(f):
                os.remove(f)
