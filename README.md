# Leo Media Renamer

A Python script that automatically adds IMDb codes to your movie and TV show folder names. Perfect for organizing your media library with proper IMDb identifiers.

![Version](https://img.shields.io/badge/version-0.0.2-blue.svg)

## Features

- Renames both movie and TV show folders
- Adds IMDb codes in a clean format: "Name (Year) {IMDb-ID}"
- Interactive handling of unmatched items
- Detailed logging of all operations
- Support for close year matches for TV shows (±1 year)
- Skips already tagged folders
- Comprehensive end-of-operation reporting with:
  - Operation statistics
  - List of skipped items with reasons
  - List of warnings and errors

## Requirements
- Python 3.x
- cinemagoer (IMDbPY) package

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Leo-Media-Renamer.git
cd Leo-Media-Renamer
```

2. Install the required package:
```bash
pip install cinemagoer
```

## Usage

Run the script:
```bash
python leo_media_renamer.py
```

The script will:
1. Ask you to choose the type of media (Movies or TV Shows)
2. Prompt you to enter the path to your media library
3. Process all media folders and add IMDb codes to their names
4. If it can't find an IMDb match for any folder:
   - Ask if you want to skip that folder or stop the entire process
   - Type 's' to skip the current folder and continue
   - Type 'o' to stop processing completely
5. Generate a detailed log file of all operations in the "MediaRenamerLog" folder
6. Display a comprehensive report showing:
   - Operation statistics
   - List of skipped items with reasons
   - List of warnings and errors

### Search Behavior
- For Movies: Searches and matches exact movie titles with the same year
- For TV Shows: 
  - Searches specifically for TV series and mini-series
  - Matches exact year first
  - If no exact match, considers shows within ±1 year of the target year
  - Filters out non-TV results (movies, video games, etc.)

### Error Handling
When the script cannot find an IMDb match for a folder, it will:
```
Could not find IMDb match for: Movie Name (2024)
Do you want to (s)kip this item or st(o)p the process? (s/o):
```
- Enter 's' to skip this folder and continue with the next one
- Enter 'o' to stop the entire process
All decisions are logged in the log file for reference.

### Logging and Reporting
The script provides two types of feedback:

1. Log Files:
- Created in the "MediaRenamerLog" folder
- Named with timestamp (e.g., `leo_media_renamer_20240315_143022.log`)
- Contains detailed operation logs including:
  - Date and time of each operation
  - All folder renames (before and after)
  - Detailed IMDb search results and matches
  - Search process details
  - User decisions
  - Errors and warnings

2. End-of-Operation Report:
```
=== Operation Report ===
Total folders processed: X
Successfully renamed: X
Skipped: X
Errors: X

=== Skipped Items ===
- Already tagged: Movie Name (Year)
- Non-directory: File Name

=== Warnings ===
- Invalid format: Incorrect Folder Name
- No IMDb match (skipped): Movie Name (Year)
```

### Example
If you have folder structures like:

Movies:
```
D:\Movies\
  ├── The Matrix (1999)
  ├── Inception (2010)
  └── The Dark Knight (2008)
```

After running the script and selecting "Movies" and the path "D:\Movies", the folders will be renamed to:
```
D:\Movies\
  ├── The Matrix (1999) {tt0133093}
  ├── Inception (2010) {tt1375666}
  └── The Dark Knight (2008) {tt0468569}
```

TV Shows:
```
D:\TV Shows\
  ├── Breaking Bad (2008)
  ├── The Office (2005)
  └── Stranger Things (2016)
```

After running the script and selecting "TV Shows" and the path "D:\TV Shows", the folders will be renamed to:
```
D:\TV Shows\
  ├── Breaking Bad (2008) {tt0903747}
  ├── The Office (2005) {tt0386676}
  └── Stranger Things (2016) {tt4574334}
```

## Notes
- The script only processes folders that match the pattern "Name (Year)"
- Folders that already contain IMDb codes (have "{" in their names) are skipped
- All operations are logged with timestamps for tracking and debugging
- Each session creates a new log file in the MediaRenamerLog folder
- The script validates the provided path before processing
- You can stop the process at any time when encountering an error
- For TV shows, the script considers shows within one year of the target year if an exact match isn't found

## Version History
See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## Contributing
Feel free to open issues or submit pull requests with improvements.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
