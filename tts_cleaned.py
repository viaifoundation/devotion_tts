# Make sure you have ffmpeg installed: brew install ffmpeg
# Save this script as tts_cleaned.py and run: python3 tts_cleaned.py

import subprocess
from pydub import AudioSegment
import os

# Save the cleaned Chinese-only text
text = """
弟兄姊妹们：今天是教会四十天的“爱在行动”的灵修系列的第二十五天，
分享的是第五周（六月二日到六月六日）的主题《亲子关系》中的最后一篇：《有其父必有其子》。

一位儿子长大后成为医生，接受采访时被问到：“为什么选择医学？”
他回答说：“因为我看到我父亲每天无私地照顾病人，从不计较回报。我只是想像他一样。”

孩子也许不会立刻听你说什么，但他们可能会模仿你怎么活。
中国有句古话，“有其父必有其子”。看看硅谷很多华人孩子的下一代学习计算机技术，也不是没有关系。

灵修经文：
行为纯正的义人，他的儿女是有福的。出自箴言第二十章第七节。

释经反思：
箴言二十章第七节指出，“行为纯正”的父亲，不仅自己蒙福，也使儿女得着恩惠。
这并不是说只要父亲正直，孩子就自动成圣，而是强调父亲的生命榜样对下一代的属灵影响深远。

“行为纯正”的意思包括诚实、敬畏上帝、言行一致。
希伯来原文“塔姆”代表完全和正直的意思。
有其父必有其子！一个义人的生活，会为家庭带来稳固的根基与属灵的传承。

英文圣经有一句话翻译为：
一个行为正直的义人，他的儿子们将会蒙福。
其中“正直”这个词，是我们非常珍惜的品格。
这也是为什么我特别鼓励父母在制定家庭价值观盾牌时，一定要保留“正直”这个属灵品质。

现实应用：
在现代社会，孩子的价值观、情绪管理和属灵习惯，常常都是从父母身上学来的。
尤其是父亲在家的态度，对神的敬虔和对人的尊重，会成为孩子未来模仿的蓝图。

你可能觉得自己并不属灵，但你的真实、悔改和坚持，就是孩子眼中的属灵榜样。

今日行动建议：
想一想：你希望你的孩子，或属灵的孩子，从你身上学到什么？
如果你计划带领全家制定家庭价值观盾牌，请试着和孩子一起讨论“正直”的重要性，并鼓励他们坚持这一点。

你也可以主动和孩子或门徒分享你属灵生命中的一个挣扎，以及神如何带你经历突破。
如果你过去在榜样上有亏欠，今天就向神祷告，请他帮助你重新成为一个义人的榜样。

祷告：
亲爱的主，求你帮助我活出一个值得被模仿的生命。
让我在言语、行为和态度上，都能显出敬虔与真实。
愿我成为孩子眼中的榜样，引导他们更靠近你。
即使我软弱失败，求你用恩典修补，用圣灵继续成全。
奉主耶稣的名祷告，阿们。
"""

# Step 1: Save the cleaned text to a file
with open("devotion_day25_cleaned.txt", "w") as f:
    f.write(text)

# Step 2: Use macOS 'say' command to generate .aiff audio using Ting-Ting voice
aiff_output = "devotion.aiff"
subprocess.run(["say", "-v", "Ting-Ting", "-f", "devotion_day25_cleaned.txt", "-o", aiff_output])

# Step 3: Convert AIFF to MP3 using ffmpeg
mp3_output = "devotion_day25.mp3"
audio = AudioSegment.from_file(aiff_output, format="aiff")
audio.export(mp3_output, format="mp3")

print(f"✅ MP3 已生成：{mp3_output}")

