#!/usr/bin/env python3
"""
gen_ceremony_segments.py

Generates speech audio segments for the ceremony "《归来仍是少年》"
using the devotion_tts framework and Edge TTS with optimal voices.

Segments:
1. 01_tracy_opening: 开场旁白 (Tracy, XiaoxiaoNeural)
2. 02_agent_redhorse: 智能体① 赤马 (YunyangNeural / YunjianNeural)
3. 03_agent_firephoenix: 智能体② 火凤 (XiaoyiNeural / HsiaoChenNeural)
4. 04_tracy_intermediate: 过渡旁白 (Tracy, XiaoxiaoNeural)
5. 05_tracy_closing: 收束旁白 (Tracy, XiaoxiaoNeural)
"""

import asyncio
import os
import shutil
import sys
from pydub import AudioSegment
import edge_tts

# Import devotion_tts text cleaner
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from text_cleaner import clean_text_for_tts

SEGMENTS = [
    {
        "id": "01_tracy_opening",
        "title": "开场旁白",
        "character": "Tracy (主持人/旁白)",
        "role_desc": "梁启超《少年中国说》开篇，出走半生引入",
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "-2%",
        "pitch": "+0Hz",
        "text": """一百多年前，梁启超写下《少年中国说》。他说：
“故今日之责任，不在他人，而全在我少年。少年智则国智，少年富则国富，少年强则国强……前途似海，来日方长。美哉我少年中国，与天不老！壮哉我中国少年，与国无疆！”
今日我们从四方归来。出走半生，历经风雨、磨砺与变迁。可心中那份纯真、那份对世界的热爱与希望，依然在。"""
    },
    {
        "id": "02_agent_redhorse",
        "title": "智能体1_赤马",
        "character": "智能体① 赤马 (晴雯歌之后)",
        "role_desc": "沉稳历史见证者，深沉发问出走半生心还在吗",
        "voice": "zh-CN-YunyangNeural",
        "rate": "-3%",
        "pitch": "+0Hz",
        "text": """我见过百年前的少年中国，也见过你们今日的归来。
那时有人写下“少年强则国强”，把希望放在尚未老去的心上。
如今你们从四面八方走来，走过山海，也走过风雨。
出走半生，心还在吗？
少年时的理想与热爱，是否依然在？"""
    },
    {
        "id": "02_agent_redhorse_yunjian",
        "title": "智能体1_赤马_激昂版",
        "character": "智能体① 赤马 (备选声音 - 激昂叙事)",
        "role_desc": "热血昂扬叙事风",
        "voice": "zh-CN-YunjianNeural",
        "rate": "-2%",
        "pitch": "+0Hz",
        "text": """我见过百年前的少年中国，也见过你们今日的归来。
那时有人写下“少年强则国强”，把希望放在尚未老去的心上。
如今你们从四面八方走来，走过山海，也走过风雨。
出走半生，心还在吗？
少年时的理想与热爱，是否依然在？"""
    },
    {
        "id": "03_agent_firephoenix",
        "title": "智能体2_火凤",
        "character": "智能体② 火凤 (女高音之后)",
        "role_desc": "烈火淬炼、涅槃重生，坚定激昂",
        "voice": "zh-CN-XiaoyiNeural",
        "rate": "-2%",
        "pitch": "+0Hz",
        "text": """集香木，赴烈火。
旧的疲惫与彷徨，可以在火中焚尽。
凤凰不是死去，而是在灰烬里重新站起来。
百年前的少年中国在文字里燃烧，百年后的我们，也在远行与归来之间经历了自己的火焰。
年龄会增长，心可以不老。
涅槃之后，仍是少年。"""
    },
    {
        "id": "03_agent_firephoenix_hsiaochen",
        "title": "智能体2_火凤_空灵版",
        "character": "智能体② 火凤 (备选声音 - 清丽空灵)",
        "role_desc": "空灵清雅诗意风",
        "voice": "zh-TW-HsiaoChenNeural",
        "rate": "-2%",
        "pitch": "+0Hz",
        "text": """集香木，赴烈火。
旧的疲惫与彷徨，可以在火中焚尽。
凤凰不是死去，而是在灰烬里重新站起来。
百年前的少年中国在文字里燃烧，百年后的我们，也在远行与归来之间经历了自己的火焰。
年龄会增长，心可以不老。
涅槃之后，仍是少年。"""
    },
    {
        "id": "04_tracy_intermediate",
        "title": "过渡旁白",
        "character": "Tracy (主持人/旁白)",
        "role_desc": "火凤之后、牵丝戏之前，温情过渡",
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "-2%",
        "pitch": "+0Hz",
        "text": """火凤说，集香木，赴烈火。
旧的疲惫、旧的伤痕、旧的彷徨，都可以在火中焚尽。
凤凰不是死去，而是在灰烬里重新站起来。
百年前的少年中国在文字里燃烧。百年后的我们，也在远行与归来之间经历了自己的火焰。
故乡的风在呼唤，牵丝的情在牵绊，可心可以不老。
涅槃之后，仍是少年。"""
    },
    {
        "id": "05_tracy_closing",
        "title": "收束旁白",
        "character": "Tracy (主持人/旁白)",
        "role_desc": "赤马重阳演唱之后，总结点题升华",
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "-2%",
        "pitch": "+0Hz",
        "text": """少年中国在百年前被写下。
凤凰在火中重生。
赤马在重阳的路上问归途，有光在前，便敢前行。
而我们，在此刻相聚。
出走半生，归来仍是少年。
不被岁月磨去锐气，不被苦难磨去善良。
美哉，归来仍是少年。"""
    }
]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "ceremony")
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")

async def generate_single(seg, output_mp3, retries=5):
    raw_text = seg["text"]
    tts_text = clean_text_for_tts(raw_text)
    voice = seg["voice"]
    rate = seg.get("rate", "+0%")
    pitch = seg.get("pitch", "+0Hz")
    
    print(f"🎙️ Generating [{seg['id']}] using {voice} (rate: {rate}, pitch: {pitch})...")
    
    temp_file = output_mp3 + ".raw.mp3"
    
    for attempt in range(1, retries + 1):
        try:
            communicate = edge_tts.Communicate(
                text=tts_text,
                voice=voice,
                rate=rate,
                pitch=pitch
            )
            await communicate.save(temp_file)
            break
        except Exception as e:
            if attempt == retries:
                raise RuntimeError(f"Failed to generate {seg['id']} after {retries} attempts: {e}")
            await asyncio.sleep(1.5 * attempt)
            
    # Post-process with pydub: add slight padding & normalize
    audio = AudioSegment.from_mp3(temp_file)
    silence_lead = AudioSegment.silent(duration=250)  # 250ms breathing lead
    silence_tail = AudioSegment.silent(duration=400)  # 400ms clean tail
    final_audio = silence_lead + audio + silence_tail
    
    # Export clean high-quality MP3 (192 kbps)
    final_audio.export(output_mp3, format="mp3", bitrate="192k")
    if os.path.exists(temp_file):
        os.remove(temp_file)
        
    duration_s = len(final_audio) / 1000.0
    print(f"  ✅ Saved: {output_mp3} ({duration_s:.1f}s)")
    return duration_s

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    
    print(f"🚀 Starting ceremony TTS generation via devotion_tts (Edge TTS)...")
    print(f"📁 Target Output Dir: {OUTPUT_DIR}")
    print(f"📁 Downloads Dir: {DOWNLOADS_DIR}\n")
    
    results = []
    
    for seg in SEGMENTS:
        filename = f"{seg['id']}.mp3"
        dest_output = os.path.join(OUTPUT_DIR, filename)
        
        dur = await generate_single(seg, dest_output)
        
        # Copy to Downloads
        dest_dl = os.path.join(DOWNLOADS_DIR, filename)
        shutil.copy2(dest_output, dest_dl)
        
        # Also create bilingual friendly name copy in Downloads
        bilingual_name = f"{seg['title']}_{seg['id']}.mp3"
        dest_bilingual = os.path.join(DOWNLOADS_DIR, bilingual_name)
        shutil.copy2(dest_output, dest_bilingual)
        
        results.append({
            "id": seg["id"],
            "title": seg["title"],
            "character": seg["character"],
            "voice": seg["voice"],
            "rate": seg["rate"],
            "duration": dur,
            "downloads_file": dest_dl,
            "bilingual_file": dest_bilingual
        })
        
    print("\n🎉 All ceremony audio segments generated successfully!")
    print("=" * 70)
    for r in results:
        print(f"• {r['id']:<32} | {r['voice']:<24} | {r['duration']:>4.1f}s | {r['character']}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
