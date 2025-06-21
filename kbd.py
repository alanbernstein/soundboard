import json
import os
import subprocess
import curses
import threading
import time
import wave
import contextlib


# Map specific keys to specific MP3 files
with open('key-sounds.json', 'r') as f:
    key_sound_map = json.load(f)

MAX_PARALLEL_SOUNDS = 3
PROGRESS_BAR_WIDTH = 20

# State
active_channels = []  # list of dicts: {'proc', 'line', 'sound', 'start_time', 'duration'}
channel_lock = threading.Lock()

def get_wav_duration(path):
    try:
        with contextlib.closing(wave.open(path, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            return frames / float(rate)
    except Exception:
        return 3.0  # fallback

def get_mp3_duration(path):
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', path],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        return float(result.stdout.strip())
    except Exception:
        return 3.0  # fallback

def get_duration(path):
    if path.lower().endswith('.wav'):
        return get_wav_duration(path)
    elif path.lower().endswith('.mp3'):
        return get_mp3_duration(path)
    else:
        return 3.0

def get_player_command(path):
    if path.lower().endswith('.wav'):
        return ['aplay', path]
    elif path.lower().endswith('.mp3'):
        return ['mpg123', path]
    else:
        return ['echo', 'Unsupported file type']

def format_progress(elapsed, total, width):
    filled = int((elapsed / total) * width)
    empty = width - filled
    bar = '█' * filled + '-' * empty
    return "|%s| %.1fs" % (bar, elapsed)

def play_sound(sound_path, stdscr):
    global active_channels

    with channel_lock:
        if len(active_channels) >= MAX_PARALLEL_SOUNDS:
            return

        used_lines = {ch['line'] for ch in active_channels}
        line_num = min(set(range(MAX_PARALLEL_SOUNDS)) - used_lines)

        duration = get_duration(sound_path)
        proc = subprocess.Popen(
            get_player_command(sound_path),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        channel = {
            'proc': proc,
            'line': line_num,
            'sound': sound_path,
            'start_time': time.time(),
            'duration': duration
        }
        active_channels.append(channel)

    def update_progress():
        while True:
            with channel_lock:
                if proc.poll() is not None:
                    break
                elapsed = time.time() - channel['start_time']
                if elapsed >= channel['duration']:
                    proc.terminate()
                    break
                bar = format_progress(elapsed, channel['duration'], PROGRESS_BAR_WIDTH)
                stdscr.addstr(line_num + 1, 0,
                              "Ch %d: %20s %s" %(line_num+1, os.path.basename(sound_path), bar))
                stdscr.clrtoeol()
                stdscr.refresh()
            time.sleep(0.1)

        with channel_lock:
            if channel in active_channels:
                active_channels.remove(channel)
            stdscr.addstr(line_num + 1, 0, "%s" % (' ' * 80))
            stdscr.refresh()

    threading.Thread(target=update_progress, daemon=True).start()

def stop_all_sounds(stdscr):
    global active_channels
    with channel_lock:
        for ch in active_channels:
            if ch['proc'].poll() is None:
                ch['proc'].terminate()
            stdscr.addstr(ch['line'] + 1, 0, "%s" % (' ' * 80))
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
            stdscr.addstr(MAX_PARALLEL_SOUNDS + 2, 0, "No sound mapped for: %s     " % {repr(key)})
            stdscr.refresh()

curses.wrapper(main)
