import os
import json
from mutagen import File
from mutagen.id3 import (
    ID3,
    TXXX,
    TPE1,
    TIT2,
    TALB,
    TCON,
    TCOM,
    TDRC,
    APIC,
    ID3NoHeaderError,
)
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE


def clear_audio_metadata(file_path):
    try:
        if file_path.lower().endswith(".mp3"):
            # For MP3 files
            try:
                audio = MP3(file_path, ID3=ID3)
                # Remove existing ID3 tags
                if audio.tags:
                    audio.delete()
                    audio.save()
                # Create new empty ID3 tag
                audio.add_tags()
                audio.save()
            except ID3NoHeaderError:
                # File has no ID3 tag
                audio = MP3(file_path)
                audio.add_tags()
                audio.save()

        elif file_path.lower().endswith(".flac"):
            # For FLAC files
            audio = FLAC(file_path)
            audio.delete()
            audio.save()

        elif file_path.lower().endswith((".ogg", ".oga")):
            # For Ogg Vorbis files
            audio = OggVorbis(file_path)
            audio.delete()
            audio.save()

        elif file_path.lower().endswith(".wav"):
            # For WAV files
            try:
                audio = WAVE(file_path)
                # WAV files can have ID3 tags
                if audio.tags:
                    audio.delete()
                    audio.save()
            except:
                pass

        elif file_path.lower().endswith((".m4a", ".aac")):
            print(
                f"  Note: Metadata clearing for {os.path.basename(file_path)} may be limited (AAC/M4A format)"
            )

        elif file_path.lower().endswith(".wma"):
            print(
                f"  Note: Metadata clearing for {os.path.basename(file_path)} may be limited (WMA format)"
            )

        return True

    except Exception as e:
        print(
            f"  Warning: Could not clear metadata for {os.path.basename(file_path)}: {str(e)}"
        )
        return False


def is_file_already_numbered(filename):
    name, ext = os.path.splitext(filename)
    return name.isdigit()


def get_sound_id(folder_name, file_number):
    return f"{folder_name}-{file_number}"


def is_sound_in_json(data, sound_id):
    for category in data["categories"]:
        for item in category["categoryItems"]:
            if item["soundID"] == sound_id:
                return True
    return False


def rename_and_update_sounds(sounds_json_path, sounds_folder_path):
    try:
        # Load existing sounds.json
        with open(sounds_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {sounds_json_path} not found!")
        return
    except json.JSONDecodeError:
        print(f"Error: {sounds_json_path} is not valid JSON!")
        return

    # Walk through the sounds directory
    for root, dirs, files in os.walk(sounds_folder_path):
        # Sort files alphabetically for consistent numbering
        files.sort()

        # Get the relative path from sounds_folder_path
        rel_path = os.path.relpath(root, sounds_folder_path)

        # Skip the root sounds folder itself, only process subfolders
        if rel_path == ".":
            continue

        # Extract folder name for sound ID
        folder_name = os.path.basename(root)

        # Create category name from folder name
        category_name = folder_name.replace("-", " ").title()

        # Determine sound source based on folder name
        if folder_name.lower().startswith("oat1"):
            sound_source = "Open Alpha Playtest #1"
        elif folder_name.lower().startswith("oat2"):
            sound_source = "Open Alpha Playtest #2"
        elif folder_name.lower().startswith("oat3"):
            sound_source = "Open Alpha Playtest #3"
        elif folder_name.lower().startswith("oat4"):
            sound_source = "Open Alpha Playtest #4"
        else:
            sound_source = folder_name  # Fallback to folder name if not OAT format

        # Filter only audio files and sort them properly
        audio_files = [
            f
            for f in files
            if f.lower().endswith(
                (".wav", ".mp3", ".ogg", ".m4a", ".flac", ".aac", ".wma")
            )
        ]
        audio_files.sort()

        # Process each file in the current directory
        for i, filename in enumerate(audio_files, start=1):
            # Get file extension
            ext = os.path.splitext(filename)[1]

            # Create new filename
            new_filename = f"{i}{ext}"

            # Full paths for renaming
            old_file_path = os.path.join(root, filename)
            new_file_path = os.path.join(root, new_filename)

            # Create sound ID
            sound_id = f"{folder_name}-{i}"

            # Check if file is already numbered correctly
            if filename == new_filename:
                print(
                    f"File {filename} in {folder_name}/ is already correctly numbered"
                )

                # Check if this sound is already in JSON
                if not is_sound_in_json(data, sound_id):
                    # File is numbered but not in JSON, add it
                    github_path = f"{rel_path.replace(os.path.sep, '/')}/{new_filename}"

                    # Find or create the category
                    category = None
                    for cat in data["categories"]:
                        if cat["categoryName"] == category_name:
                            category = cat
                            break

                    # If category doesn't exist, create it
                    if category is None:
                        category = {
                            "categoryName": category_name,
                            "categoryDescription": f"Sound files from {folder_name} directory",
                            "categoryItems": []
                        }
                        data["categories"].append(category)
                        print(f"Created new category: {category_name}")

                    new_entry = {
                        "soundID": sound_id,
                        "soundType": folder_name,
                        "soundSource": sound_source,
                        "soundFile": f"https://cdn.jsdelivr.net/gh/HEATLabs/Sound-Bank@main/sounds/{github_path}",
                        "soundName": f"{folder_name} - Sound {i}",
                        "soundDescription": f"Sound file from {folder_name} directory",
                    }

                    category["categoryItems"].append(new_entry)
                    print(f"Added missing entry to JSON: {sound_id}")
                else:
                    print(f"Entry {sound_id} already exists in JSON - skipping")

                # Skip renaming and metadata clearing for already correctly numbered files
                continue

            # Step 1: Clear metadata from the original file
            print(f"Clearing metadata from {filename}...")
            metadata_cleared = clear_audio_metadata(old_file_path)

            if metadata_cleared:
                print(f"  Metadata cleared from {filename}")

            # Step 2: Rename the file
            if os.path.exists(new_file_path) and old_file_path != new_file_path:
                # If target file already exists, we need to handle this carefully
                print(
                    f"  Warning: Target file {new_filename} already exists in {folder_name}/"
                )

                # Find an available number
                j = i + 1
                while True:
                    temp_new_filename = f"{j}{ext}"
                    temp_new_file_path = os.path.join(root, temp_new_filename)
                    if not os.path.exists(temp_new_file_path):
                        new_filename = temp_new_filename
                        new_file_path = temp_new_file_path
                        sound_id = f"{folder_name}-{j}"
                        print(f"  Using alternative number: {new_filename}")
                        break
                    j += 1

            # Only rename if the source and target are different
            if old_file_path != new_file_path:
                os.rename(old_file_path, new_file_path)
                print(f"Renamed {filename} to {new_filename} in {folder_name}/")
            else:
                print(f"File {filename} is already correctly named")

            # Create GitHub raw content URL path (use new filename)
            github_path = f"{rel_path.replace(os.path.sep, '/')}/{new_filename}"

            # Check if this sound is already in JSON
            if not is_sound_in_json(data, sound_id):
                # Find or create the category
                category = None
                for cat in data["categories"]:
                    if cat["categoryName"] == category_name:
                        category = cat
                        break

                # If category doesn't exist, create it
                if category is None:
                    category = {
                        "categoryName": category_name,
                        "categoryDescription": f"Sound files from {folder_name} directory",
                        "categoryItems": []
                    }
                    data["categories"].append(category)
                    print(f"Created new category: {category_name}")

                # Create new entry
                new_entry = {
                    "soundID": sound_id,
                    "soundType": folder_name,
                    "soundSource": sound_source,
                    "soundFile": f"https://cdn.jsdelivr.net/gh/HEATLabs/Sound-Bank@main/sounds/{github_path}",
                    "soundName": f"{folder_name} - Sound {i}",
                    "soundDescription": f"Sound file from {folder_name} directory",
                }

                # Add to JSON data
                category["categoryItems"].append(new_entry)
                print(f"Added to JSON: {new_entry['soundID']}")
            else:
                print(f"Entry {sound_id} already exists in JSON - skipping")

    # Sort the JSON entries by soundID for consistency
    data["categories"].sort(key=lambda x: x["categoryName"])
    for category in data["categories"]:
        category["categoryItems"].sort(key=lambda x: x["soundID"])

    # Save updated JSON
    with open(sounds_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Updated {sounds_json_path} with new sound entries!")


def rename_files_in_current_directory():
    # Get the current script's filename
    script_name = os.path.basename(__file__)

    # Get all files in the current directory
    files = [f for f in os.listdir(".") if os.path.isfile(f) and f != script_name]

    # Sort files alphabetically
    files.sort()

    # Rename files starting from 1, but check for conflicts
    for i, filename in enumerate(files, start=1):
        # Get the file extension
        ext = os.path.splitext(filename)[1]
        # Create new filename
        new_name = f"{i}{ext}"

        # Skip if file is already correctly named
        if filename == new_name:
            print(f"File {filename} is already correctly numbered - skipping")
            continue

        # Check if target file already exists
        if os.path.exists(new_name):
            print(f"Warning: Target file {new_name} already exists!")
            # Find an available number
            j = i + 1
            while True:
                temp_new_name = f"{j}{ext}"
                if not os.path.exists(temp_new_name):
                    new_name = temp_new_name
                    print(f"Using alternative number: {new_name}")
                    break
                j += 1

        # Rename the file
        os.rename(filename, new_name)
        print(f"Renamed {filename} to {new_name}")


def main():
    print("Starting file processing...")

    # Configuration
    SOUNDS_JSON_PATH = "../../Website-Configs/sounds.json"
    SOUNDS_FOLDER_PATH = "../sounds"

    # Step 1: Rename files in current directory
    print("\n=== Step 1: Renaming files in current directory ===")
    rename_files_in_current_directory()

    # Step 2: Rename sound files in their folders, clear metadata, and update JSON
    print(
        "\n=== Step 2: Renaming sound files, clearing metadata, and updating sounds.json ==="
    )
    rename_and_update_sounds(SOUNDS_JSON_PATH, SOUNDS_FOLDER_PATH)

    print("\n=== Processing Complete! ===")


if __name__ == "__main__":
    main()
