# Leo Media Renamer

A Python script that automatically adds IMDb codes to your movie and TV show folder names. Perfect for organizing your media library with proper IMDb identifiers.

![Version](https://img.shields.io/badge/version-0.0.5-blue.svg)

## Features

- Renames both movie and TV show folders
- Adds IMDb codes in a clean format: "Name (Year) {IMDb-ID}"
- Smart IMDb verification:
  - Optional IMDb verification with user prompt
  - Intelligent title comparison (ignores colon differences)
  - Multiple options for mismatches (skip/use IMDb/exit)
- Movie file handling:
  - Renames movie files with quality information
  - Preserves poster files automatically
  - Renames matching subtitle files
  - Optional cleanup of other files
- Batch processing with customizable batch size
- Interactive menu system with exit options
- Post-completion options to start over or exit
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
git clone https://github.com/leoramzi/Leo-Media-Renamer.git
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
1. Present initial menu:
   ```
   What would you like to do?
   1. Rename Movie - Folders
   2. Rename Movie - Files
   3. TV Shows - Folders
   4. Exit
   ```

2. If you choose to process media:
   - Prompt for IMDb verification (for movie files)
   - Ask for media library path
   - For folders: Ask for batch size
     - Enter 0 to process all items at once
     - Enter a number (e.g., 50) to process that many items at a time
   - Process the items:
     - Shows progress for current batch
     - Asks for confirmation when needed

3. After completion, present options:
   ```
   What would you like to do next?
   1. Start a new renaming session
   2. Exit
   ```

### IMDb Verification
When IMDb verification is enabled:
```
IMDb data mismatch for: Movie Name (2024)
IMDb title: Actual Movie Name (2024)

Options:
s - Skip this movie
i - Use IMDb title
e - Exit to main menu
```
- Enter 's' to skip this movie and continue
- Enter 'i' to use the IMDb title
- Enter 'e' to exit to main menu

### Batch Processing
The script supports processing files in batches:
```
Enter batch size (0 for all at once): 50

Processing batch 1 (items 1 to 50 of 150)
[Processing details...]

Batch 1 complete:
Processed: 50
Renamed: 45
Skipped: 3
Errors: 2

Do you want to process the next batch? (y/n):
```

### Search Behavior
- For Movies: 
  - Searches and matches exact movie titles with the same year
  - Intelligently handles title differences (e.g., colons)
  - Provides options for mismatches
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
- Batch processing allows for better control over large libraries
- You can exit the program at any time from the main menu
- After completing a session, you can start a new one or exit
- Poster files (named "poster" with common image extensions) are automatically preserved

## Version History
See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## Contributing
Feel free to open issues or submit pull requests with improvements.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
