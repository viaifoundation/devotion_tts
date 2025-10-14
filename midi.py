from midiutil import MIDIFile

notes_44 = [
    (60, 1), (62, 0.5), (62, 0.5),
    (64, 1), (62, 1),
    (64, 1), (64, 1),
    (64, 1), (64, 1),

    (67, 1), (64, 1), (60, 1),
    (69, 1),
    (65, 1), (64, 1),
    (60, 1), (60, 1),

    (64, 1), (67, 1), (64, 1),
    (64, 1), (69, 1),
    (69, 1), (65, 1),
    (64, 1), (64, 1),

    (60, 1), (62, 1), (60, 1),
    (60, 1), (69, 1),
    (64, 1), (0, 1),
    (65, 1), (60, 1)
]

midi = MIDIFile(1)
track, channel, time, tempo, volume = 0, 0, 0, 90, 100
midi.addTempo(track, time, tempo)

for pitch, duration in notes_44:
    if pitch > 0:
        midi.addNote(track, channel, pitch, time, duration, volume)
    time += duration

with open("kaozhu_bidesheng_44.mid", "wb") as f:
    midi.writeFile(f)

print("MIDI 文件已生成：kaozhu_bidesheng_44.mid")

