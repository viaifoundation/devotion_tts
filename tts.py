import asyncio
import edge_tts

# Cleaned Chinese devotional text
TEXT = """
"弟兄姊妹，欢迎来到晨曦读经，今天由雪峰为我们领读撒母耳记下第16章。今日亮光：撒母耳记下16章11-12节
大卫又对亚比筛和众臣仆说，我亲生的儿子尚且寻索我的性命，何况这便雅悯人呢。由他咒骂吧，因为这是耶和华吩咐他的。或者耶和华见我遭难，为我今日被这人咒骂，就施恩与我。当示每咒骂大卫时，亚比筛要杀他，但大卫阻止了。大卫说由他咒骂吧，因为这是耶和华吩咐他的。这不是说神真的吩咐示每去咒骂，而是大卫认识到这一切都在神的掌管之下。在人生最屈辱的时刻被人咒骂羞辱，大卫没有还口，没有报复，反而存着一颗谦卑受教的心。他说或者耶和华见我遭难，为我今日被这人咒骂，就施恩与我。这是何等美好的生命，把羞辱转化为蒙恩的机会。今天我们在生活中也会遭遇不公的对待，在职场上被同事诽谤，在网络上被人恶意攻击，甚至在教会中被弟兄姊妹误解。我们的第一反应往往是为自己辩护，要证明自己的清白，要让对方付出代价。但大卫给我们另一个选择，就是把这些都看作是神许可的功课。不是说我们要逆来顺受，而是相信神掌管一切，祂能够使万事互相效力，叫爱神的人得益处。当我们受委屈时，不要急着为自己伸冤，而要先到神面前省察，是否有需要学习的功课。即使我们真的无辜，这样的经历也能让我们更体会主耶稣的心肠，祂被骂不还口，被害不说威吓的话。弟兄姊妹，让我们学习大卫的榜样，在受苦中仍然仰望神，相信祂必按公义审判，也必在适当的时候为我们伸冤。

与Robbin传道同心祷告
主，感谢你，因为你是察看人心的神，你知道我们所受的每一个委屈。求你帮助我们在被人误解和攻击时，不凭血气回应，而是存着谦卑的心来到你面前。让我们相信你掌管一切，你必在合适的时候彰显公义。感谢祷告奉耶稣得胜的名祈求，阿们！"
"""

# Use Xiaoxiao for female Mandarin voice (you can try "zh-CN-YunxiNeural" for male)
#VOICE = "zh-CN-XiaoxiaoNeural"
VOICE = "zh-CN-XiaoxiaoNeural"
VOICE = "zh-CN-YunyangNeural"  # 试试比 Yunxi 更沉稳的中文男声
#VOICE = "zh-CN-liaoning-XiaobeiNeural"
OUTPUT = "/Users/mhuo/Downloads/devotion_0623.mp3"

async def main():
    communicate = edge_tts.Communicate(text=TEXT, voice=VOICE)
    await communicate.save(OUTPUT)
    print(f"✅ 已生成 MP3：{OUTPUT}")

asyncio.run(main())

