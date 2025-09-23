import os

# Get the current script's filename
script_name = os.path.basename(__file__)

# Get all files in the current directory
files = [f for f in os.listdir('.') if os.path.isfile(f) and f != script_name]

# Sort files alphabetically
files.sort()

# Rename files starting from 1
for i, filename in enumerate(files, start=1):
    # Get the file extension
    ext = os.path.splitext(filename)[1]
    # Create new filename
    new_name = f"{i}{ext}"
    # Rename the file
    os.rename(filename, new_name)
    print(f"Renamed {filename} to {new_name}")

print("Files Sorted!")
