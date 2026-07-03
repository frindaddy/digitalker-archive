import os
import re
import argparse
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError


def natural_key(s):
    parts = re.split(r"(\d+)", s)
    return tuple(int(p) if p.isdigit() else p.lower() for p in parts)


def renumber_folder(folder_path: str, start: int = 1):
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.mp3')]

    # Read existing ID3 track numbers (if present) and sort by them first.
    entries = []
    for f in files:
        file_path = os.path.join(folder_path, f)
        tn = None
        try:
            try:
                audio = EasyID3(file_path)
            except Exception:
                audio = None
            if audio:
                tn_field = audio.get('tracknumber', [None])[0]
                if tn_field:
                    m = re.match(r"(\d+)", str(tn_field))
                    if m:
                        tn = int(m.group(1))
        except Exception:
            tn = None
        entries.append((f, tn))

    # Sort: files with a valid track number first (ascending), then the rest by filename.
    entries.sort(key=lambda x: (x[1] is None, x[1] if x[1] is not None else float('inf'), natural_key(x[0])))

    files = [e[0] for e in entries]

    total = len(files)
    if total == 0:
        print("No mp3 files found in folder.")
        return

    current = start
    for fname in files:
        file_path = os.path.join(folder_path, fname)
        try:
            try:
                audio = EasyID3(file_path)
            except ID3NoHeaderError:
                audio = MP3(file_path)
                audio.add_tags()
                audio.save()
                audio = EasyID3(file_path)

            # Set tracknumber as a single track number (zero-padded per width).
            audio['tracknumber'] = f"{current}"
            audio.save()
            print(f"Set {fname} -> track {current}")
        except Exception as e:
            print(f"Could not update tags for {fname}: {e}")
        current += 1


def build_parser():
    p = argparse.ArgumentParser(description='Renumber MP3 ID3 track numbers in a folder')
    p.add_argument('folder', nargs='?', default='.', help='Target folder containing MP3 files')
    p.add_argument('--start', '-s', type=int, default=1, help='Starting track number (default: 1)')
    return p

if __name__ == '__main__':
    parser = build_parser()
    args = parser.parse_args()
    renumber_folder(args.folder, start=args.start)
