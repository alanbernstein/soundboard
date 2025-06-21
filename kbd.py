import os
import subprocess
import curses
import threading
import time

# Map specific keys to specific MP3 files
key_sound_map = {
    'a': 'audio/animals/dolphin.mp3',
    'b': 'audio/animals/eagle.mp3',
    '1': 'audio/animals/frog.mp3',
    '2': 'audio/animals/horse.mp3',
    '0': 'audio/animals/owl.mp3',
    'c': 'audio/fx/airhorn-repeat.mp3',
    'd': 'audio/fx/glass.mp3',
    'e': 'audio/fx/awooga.mp3',
    'f': 'audio/fx/bell.mp3',
    'g': 'audio/fx/boing.mp3',
    'h': 'audio/fx/bomb-whistle.mp3',
    'i': 'audio/fx/buzzer.mp3',
    'j': 'audio/fx/cash-register.mp3',
    'k': 'audio/fx/crowd-gasp.mp3',
    'l': 'audio/fx/crowd.mp3',
    'm': 'audio/fx/door.mp3',
    'n': 'audio/fx/dream-sequence.mp3',
    'o': 'audio/fx/fast-forward.mp3',
    'p': 'audio/fx/flourish.mp3',
    'q': '',
    'r': 'audio/fx/gun.mp3',
    's': 'audio/fx/laughing-diddy-kid.mp3',
    't': 'audio/fx/magic-wand.mp3',
    'u': 'audio/fx/punch.mp3',
    'v': 'audio/fx/rimshot.mp3',
    'w': 'audio/fx/scratch.mp3',
    'x': 'audio/fx/scream-howie.mp3',
    'y': 'audio/fx/scream-wilhelm.mp3',
    'z': 'audio/fx/shotgun-blast.mp3',
    '3': 'audio/fx/shotgun-reload.mp3',
    '4': 'audio/fx/siren.mp3',
    '5': 'audio/fx/splat.mp3',
    '6': 'audio/fx/sting-evil.mp3',
    '7': 'audio/fx/trombone.mp3',
    '8': 'audio/fx/vase-break.mp3',
    '9': 'audio/fx/wa-wa-wa-wa.mp3',
}

MAX_PARALLEL_SOUNDS = 3
SOUND_DURATION_SECONDS = 3

# State
active_channels = []  # list of dicts: {'proc': ..., 'line': ..., 'sound': ...}
channel_lock = threading.Lock()

def play_sound(sound_path, stdscr):
    global active_channels

    with channel_lock:
        if len(active_channels) >= MAX_PARALLEL_SOUNDS:
            return

        # Find first available line number (0 to MAX-1)
        used_lines = {ch['line'] for ch in active_channels}
        line_num = min(set(range(MAX_PARALLEL_SOUNDS)) - used_lines)

        if sound_path.endswith('.mp3'):
            player = 'mpg123'
        elif sound_path.endswith('.wav'):
            player = 'aplay'
        proc = subprocess.Popen([player, sound_path],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

        active_channels.append({'proc': proc, 'line': line_num, 'sound': sound_path})

        stdscr.addstr(line_num + 1, 0, f"Channel {line_num+1}: {os.path.basename(sound_path)} started      ")
        stdscr.clrtoeol()
        stdscr.refresh()

    def stop_after_delay():
        time.sleep(SOUND_DURATION_SECONDS)
        with channel_lock:
            if proc.poll() is None:
                proc.terminate()
            # Clean up display and channel list
            for ch in active_channels:
                if ch['proc'] == proc:
                    stdscr.addstr(ch['line'] + 1, 0, f"Channel {ch['line']+1}:                        ")
                    stdscr.clrtoeol()
                    stdscr.refresh()
                    active_channels.remove(ch)
                    break

    threading.Thread(target=stop_after_delay, daemon=True).start()

def stop_all_sounds(stdscr):
    global active_channels
    with channel_lock:
        for ch in active_channels:
            if ch['proc'].poll() is None:
                ch['proc'].terminate()
            stdscr.addstr(ch['line'] + 1, 0, f"Channel {ch['line']+1}:                        ")
            stdscr.clrtoeol()
        stdscr.refresh()
        active_channels.clear()

def main(stdscr):
    curses.cbreak()
    stdscr.nodelay(False)
    stdscr.clear()
    stdscr.addstr(0, 0, "Press keys to play sounds. SPACE = stop all, Q = quit\n")
    stdscr.refresh()

    while True:
        key = stdscr.get_wch()

        if key in ('q', 'Q'):
            stop_all_sounds(stdscr)
            stdscr.addstr(MAX_PARALLEL_SOUNDS + 2, 0, "Quitting.")
            stdscr.refresh()
            break

        if key == ' ':
            stop_all_sounds(stdscr)
            stdscr.addstr(MAX_PARALLEL_SOUNDS + 2, 0, "All sounds stopped.     ")
            stdscr.refresh()
            continue

        sound = key_sound_map.get(key)
        if sound:
            play_sound(sound, stdscr)
        else:
            stdscr.addstr(MAX_PARALLEL_SOUNDS + 2, 0, f"No sound mapped for: {repr(key)}     ")
            stdscr.refresh()

curses.wrapper(main)