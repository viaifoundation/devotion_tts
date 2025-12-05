from pydub import AudioSegment
try:
    s = AudioSegment.silent(duration=100)
    segments = [s, s]
    # Check if join exists
    if hasattr(s, "join"):
        print("AudioSegment.join exists")
        res = s.join(segments)
        print("Join result length:", len(res))
    else:
        print("AudioSegment.join DOES NOT exist")
except Exception as e:
    print(f"Error checking join: {e}")

text = """Line 1

Line 2"""
split_res = text.split("nn")
print(f"Split 'nn' result: {split_res} (Length: {len(split_res)})")
