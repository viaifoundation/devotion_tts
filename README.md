Devotion Audio TTS
This project generates text-to-speech (TTS) audio for Chinese Bible devotionals, splitting the text into sections read by different voices. It includes scripts to process devotional texts, convert Bible references (e.g., "罗马书 1:17" to "罗马书 1 章 17 節"), and produce MP3 audio files using edge-tts and pydub.
Project Structure

bible_parser.py: Shared module to convert Bible references (e.g., "罗马书 1:17" to "罗马书 1 章 17 節").
gen_devotion_audio.py: Generates audio for a devotional text, splitting into two voices (introduction and main content).
gen_bread_audio.py: Generates audio for another devotional text (similar structure).
verse_devotion.py: Generates audio for verse-focused devotional text (similar structure).
requirements.txt: Lists Python dependencies.
Other files (e.g., tts.py, tts2.py, tts_cleaned.py, m4a2mp3.py, midi.py, devotion.txt) are included for reference but not part of the main workflow.

Setup

Clone the Repository:
git clone git@github.com:michaelhuo/devotion_audio_tts.git
cd devotion_audio_tts

Install Dependencies:
pip install -r requirements.txt

Ensure ffmpeg is installed for pydub:
brew install ffmpeg # On macOS

Update Text:

Edit the TEXT variable in gen_devotion_audio.py, gen_bread_audio.py, or verse_devotion.py with your devotional content.
Ensure the text includes Bible references in the format "Book Chapter:Verse" (e.g., "罗马书 1:17").

Run a Script:
python gen_devotion_audio.py

Output audio will be saved to /Users/mhuo/Downloads/ (e.g., devotion_1014.mp3, bread_1014.mp3, verse_1014.mp3). Update paths in scripts if needed.

Usage
Each script (gen_devotion_audio.py, gen_bread_audio.py, verse_devotion.py):

Converts Bible references using bible_parser.convert_bible_reference.
Splits the text into an introduction (first paragraph, read by FIRST_VOICE) and main content (remaining paragraphs, read by SECOND_VOICE).
Generates MP3 audio with a 0.5-second pause between sections.
Outputs to /Users/mhuo/Downloads/ with unique file names to avoid conflicts.

To customize:

Update FIRST_VOICE and SECOND_VOICE in each script (see supported voices in the script comments).
Modify the TEXT variable with your devotional content.
Adjust OUTPUT and TEMP_DIR paths if needed.

Dependencies
See requirements.txt for the full list. Key dependencies:

edge-tts: For text-to-speech conversion.
pydub: For audio processing and concatenation.
ffmpeg: Required by pydub for MP3 handling.

Notes

Ensure output paths (e.g., /Users/mhuo/Downloads/) are writable.
Generated audio files (.mp3, .aiff) are excluded from the repository via .gitignore.
If scripts are moved to different directories, update the import path for bible_parser (e.g., from ..path.to.bible_parser import convert_bible_reference).

License
MIT License (or replace with your preferred license)
