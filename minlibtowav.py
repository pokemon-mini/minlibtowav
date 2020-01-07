import argparse

VERSION = "1.0.0"

parser = argparse.ArgumentParser(description = "Minlib audio converter v{}".format(VERSION))
parser.add_argument("inp", type = str, help = "Input Minlib song file")
parser.add_argument("-ow", "--outwav", type = str, help = "Output WAV file (optional)")
parser.add_argument("-om", "--outmid", type = str, help = "Output MIDI file (optional)")
parser.add_argument("-s", "--samplerate", type = int, help = "Sampling rate (optional, default = 1000000)")

args = parser.parse_args()

song = bytearray(open(args.inp, "rb").read())

note_lookup = [0x7800, 0x7160, 0x6AE0, 0x6500,
               0x5F40, 0x5A00, 0x54E0, 0x5000,
         0x4BC0, 0x4760, 0x4300, 0x3EC0,
         0x3C00, 0x38B0, 0x3570, 0x3280,
         0x2FA0, 0x2D00, 0x2A70, 0x2800,
         0x25E0, 0x23B0, 0x2180, 0x1F60,
         0x1E00, 0x1C58, 0x1AB8, 0x1940,
         0x17D0, 0x1680, 0x1538, 0x1400,
         0x12F0, 0x11D8, 0x10C0, 0x0FB0,
         0x0F00, 0x0E2C, 0x0D5C, 0x0CA0,
         0x0BE8, 0x0B40, 0x0A9C, 0x0A00,
         0x0978, 0x08EC, 0x0860, 0x07D8,
         0x0780, 0x0716, 0x06AE, 0x0650,
         0x05F4, 0x05A0, 0x054E, 0x0500,
         0x04BC, 0x0476, 0x0430, 0x03EC,
         0x03C0, 0x038B, 0x0357, 0x0328,
         0x02FA, 0x02D0, 0x02A7, 0x0280,
         0x025E, 0x023B, 0x0218, 0x01F6,
         0x01E0, 0x0000]

duty_table = [0x02, 0x04, 0x08, 0x10, 0x20, 0x70]

notelen_lookup = [[0x01, 0x02, 0x04, 0x06, 0x08, 0x0C, 0x10, 0x18, 0x20],
                  [0x01, 0x03, 0x06, 0x09, 0x0C, 0x12, 0x18, 0x24, 0x30],
                  [0x02, 0x04, 0x08, 0x0C, 0x10, 0x18, 0x20, 0x30, 0x40],
                  [0x03, 0x06, 0x0C, 0x12, 0x18, 0x24, 0x30, 0x48, 0x60],
                  [0x04, 0x08, 0x10, 0x18, 0x20, 0x30, 0x40, 0x60, 0x80],
                  [0x05, 0x0A, 0x14, 0x1E, 0x28, 0x3C, 0x50, 0x78, 0xA0],
                  [0x06, 0x0C, 0x18, 0x24, 0x30, 0x48, 0x60, 0x90, 0xC0],
                  [0x07, 0x05, 0x0A, 0x0F, 0x14, 0x1E, 0x28, 0x3C, 0x50],
                  [0x04, 0x07, 0x0E, 0x15, 0x1C, 0x2A, 0x38, 0x54, 0x70],
                  [0x06, 0x09, 0x12, 0x1B, 0x24, 0x36, 0x48, 0x6C, 0x90]]

if args.samplerate:
    sampling_rate = args.samplerate
else:
    sampling_rate = 1000000

duty = 0.5
length = 0
len_multiplier = 0

notes = []

for i in song:

    if i < 74:
        notes.append([notelen_lookup[len_multiplier][length], i, duty])
    elif i < 128:
        print("invalid note: {}".format(i))
    else:
        if i >> 4 == 0x0F:
            if i & 0x0F in [0x00, 0x02]:
                notes.append([60, 0x49, 0.5])
            continue
        elif i >> 4 == 0x0C:
            duty = 1 / duty_table[i & 0x0F]
        elif i >> 4 == 0x0B:
            len_multiplier = i & 0x0F
        elif i >> 4 == 0x0A:
            continue
        elif i >> 4 == 0x09:
            continue
        elif i >> 4 == 0x08:
            length = i & 0x0F

if args.outwav:
    try:
        import numpy, wave, scipy.signal
        
        output = bytearray()
        
        cache = {}
        
        def note(length, note, duty):
            samples = 0.016384 * length * sampling_rate
            if note_lookup[note] != 0:
                freq = 2000000 / note_lookup[note]
                x = numpy.arange(samples)
        
                y = scipy.signal.square(2 * numpy.pi * freq * x / sampling_rate, duty)
        
            else:
                y = int(samples) * [0x80]
        
            return y
        
    except:
        print("The numpy, wave and scipy libraries are required to export WAV files! Please install them first.")
        exit()

if args.outmid:
    try:
        import miditime.miditime
        
        midi_data = list()
        
        midi_file = miditime.miditime.MIDITime(3662.109375, args.outmid)
        
    except:
        print("The miditime library is required to export MIDI files! Please install it first.")
        exit()

counter = 0

next_percent = 100

for k, i in enumerate(notes):
    
    if k >= next_percent:
        print("{}%".format(int(k / len(notes) * 100)))
        next_percent += 100
    
    if args.outwav:
        if (key := " ".join([str(j) for j in i])) not in cache:
            y = note(*i)
            cache[key] = y
        else:
            y = cache[key]
        output.extend([int(j) % 256 for j in y])
    
    if args.outmid:
        if i[1] != 0x49:
            midi_data.append([counter, i[1] + 36, 127, i[0]])
        counter += i[0]

if args.outwav:
    wav_file = wave.open(args.outwav, "wb")
    wav_file.setparams((1, 1, sampling_rate, len(output), "NONE", "none"))
    wav_file.writeframes(output)
    wav_file.close()

if args.outmid:
    midi_file.add_track(midi_data)
    import os, contextlib
    
    with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
        midi_file.save_midi() # neat hack to stop prints
