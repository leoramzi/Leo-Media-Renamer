# Changelog

All notable changes to Leo Media Renamer will be documented in this file.

## [0.0.5] - 2024-03-15

### Added
- New "Rename Movie - Files" feature:
  - Renames movie files with quality information
  - Automatically preserves poster files
  - Renames matching subtitle files
  - Optional cleanup of other files
- Enhanced IMDb verification:
  - Optional verification with user prompt
  - Intelligent title comparison (ignores colon differences)
  - Multiple options for mismatches:
    * Skip current movie
    * Use IMDb title
    * Exit to main menu
- Improved menu options:
  - Renamed "Process Movies" to "Rename Movie - Folders"
  - Added "Rename Movie - Files" as second option
  - Renamed "Process TV Shows" to "TV Shows - Folders"

## [0.0.4] - 2024-03-15

### Added
- Exit option in initial media type selection menu
- Post-completion menu to:
  - Start a new renaming session
  - Exit the program
- Improved program flow control

## [0.0.3] - 2024-03-15

### Added
- Batch processing functionality:
  - Option to specify number of titles to process at once
  - Input 0 to process all titles at once
  - Confirmation prompt between batches
  - Progress tracking between batches

## [0.0.2] - 2024-03-15

### Added
- Detailed end-of-operation reporting with three sections:
  - Operation statistics (processed, renamed, skipped, errors)
  - Comprehensive list of skipped items with reasons
  - Detailed list of warnings and errors encountered

## [0.0.1] - 2024-03-15

### Added
- Initial release
- Support for renaming movie folders with IMDb codes
- Support for renaming TV show folders with IMDb codes
- Interactive error handling (skip/stop options)
- Detailed logging system
- Support for close year matches (±1 year) for TV shows
- Validation for folder paths and names
- Statistics tracking for processed items
