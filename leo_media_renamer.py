#!/usr/bin/env python3
"""
Leo Media Renamer - A Media Library IMDb Code Renamer
Version: 0.0.4

This script renames movie and TV show folders by adding IMDb codes to their names.
It processes folders formatted as "Name (Year)" and adds the IMDb code in the format
"Name (Year) {IMDb-ID}".

Author: Leo
GitHub: https://github.com/leoramzi/Leo-Media-Renamer
"""

import os
import re
import logging
import sys
from imdb import Cinemagoer
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ============= CONFIGURATION =============
VERSION = "0.0.4"
# Logging configuration
LOG_DIR = "MediaRenamerLog"

# Quality patterns
RESOLUTIONS = ['720p', '1080p', '2160p']
SOURCES = ['HDTV', 'WEBDL', 'WEBRip', 'Bluray', 'Remux', 'BR-DISK', 'Raw-HD', 'BrRip']

# Special characters replacement
SPECIAL_CHARS = {
    ':': ' - ',
    '/': ' - ',
    '\\': ' - ',
    '*': ' - ',
    '?': ' - ',
    '"': ' - ',
    '<': ' - ',
    '>': ' - ',
    '|': ' - ',
}
# =======================================

def setup_logging():
    """Setup logging configuration."""
    # Create log directory if it doesn't exist
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"leo_media_renamer_{timestamp}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also print to console
        ]
    )
    
    logging.info(f"=== Leo Media Renamer v{VERSION} Session Started ===")
    return log_file

def sanitize_filename(filename: str) -> str:
    """Replace special characters in filename with safe alternatives."""
    for char, replacement in SPECIAL_CHARS.items():
        filename = filename.replace(char, replacement)
    return filename

def get_quality_from_user() -> str:
    """Get quality input from user."""
    print("\nAvailable quality formats:")
    for i, quality in enumerate(SOURCES, 1):
        if quality not in ['BR-DISK', 'Raw-HD']:
            for res in RESOLUTIONS:
                print(f"{quality}-{res}")
        else:
            print(quality)
    
    while True:
        quality = input("\nEnter the quality (e.g., Bluray-1080p): ").strip()
        # Validate input
        if quality in ['BR-DISK', 'Raw-HD']:
            return quality
        for src in SOURCES:
            if src not in ['BR-DISK', 'Raw-HD']:
                for res in RESOLUTIONS:
                    if quality == f"{src}-{res}":
                        return quality
        print("Invalid quality format. Please choose from the list above.")

def detect_quality(filename: str) -> Optional[str]:
    """Detect quality from filename based on resolution and source."""
    filename_upper = filename.upper()
    
    # Find resolution
    resolution = None
    for res in RESOLUTIONS:
        if res.upper() in filename_upper:
            resolution = res
            break
    
    # Find source
    source = None
    for src in SOURCES:
        if src.upper() in filename_upper:
            source = src
            break
    
    if resolution and source:
        # Special case for BR-DISK and Raw-HD
        if source in ['BR-DISK', 'Raw-HD']:
            return source
        # Combine source and resolution
        return f"{source}-{resolution}"
    
    return None

def extract_imdb_id(folder_name: str) -> Optional[str]:
    """Extract IMDb ID from folder name if present."""
    pattern = r"\{tt(\d+)\}"
    match = re.search(pattern, folder_name)
    if match:
        return match.group(1)
    return None

def verify_imdb_data(ia: Cinemagoer, imdb_id: str, name: str, year: int) -> bool:
    """Verify if the IMDb ID matches with the given name and year."""
    try:
        movie = ia.get_movie(imdb_id)
        if not movie:
            return False
        
        # Get movie title and year from IMDb
        imdb_title = movie.get('title')
        imdb_year = movie.get('year')
        
        # Compare title (case-insensitive) and year
        if (imdb_title.lower() == name.lower() and 
            (imdb_year == year or abs(imdb_year - year) <= 1)):
            return True
        
        logging.warning(f"IMDb mismatch - Folder: {name} ({year}), IMDb: {imdb_title} ({imdb_year})")
        return False
    except Exception as e:
        logging.error(f"Error verifying IMDb data: {str(e)}")
        return False

def verify_movie_name(name: str, year: int) -> Tuple[Optional[str], Optional[str]]:
    """Verify movie name against IMDb database and return correct name and ID."""
    ia = Cinemagoer()
    try:
        results = ia.search_movie(name)
        # Filter for movies only
        movies = [r for r in results if r.get('kind') == 'movie']
        
        # Try exact year match first
        for movie in movies:
            if movie.get('year') == year:
                movie_id = movie.getID()
                # Get full movie info to ensure correct title
                full_movie = ia.get_movie(movie_id)
                return sanitize_filename(full_movie['title']), movie_id
        
        # If no exact match, try close years
        for movie in movies:
            if abs(movie.get('year', 0) - year) <= 1:
                movie_id = movie.getID()
                full_movie = ia.get_movie(movie_id)
                return sanitize_filename(full_movie['title']), movie_id
        
        return None, None
    except Exception as e:
        logging.error(f"Error verifying movie name: {str(e)}")
        return None, None

def get_movie_files(folder_path: str) -> Tuple[Optional[str], List[str], List[str], List[str]]:
    """Get movie file, subtitle files, poster files, and other files in the folder."""
    movie_extensions = {'.mp4', '.mkv', '.avi', '.m4v', '.mov'}
    subtitle_extensions = {'.srt', '.sub', '.ass', '.ssa'}
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    
    movie_file = None
    subtitle_files = []
    poster_files = []
    other_files = []
    
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        name_without_ext, ext = os.path.splitext(item.lower())
        
        if os.path.isfile(item_path):
            if ext in movie_extensions:
                if movie_file:
                    logging.warning(f"Multiple movie files found in {folder_path}")
                    return None, [], [], []
                movie_file = item
            elif ext in subtitle_extensions:
                subtitle_files.append(item)
            elif ext in image_extensions and name_without_ext in ['poster', 'Poster']:
                poster_files.append(item)
            else:
                other_files.append(item)
        else:
            other_files.append(item)
    
    return movie_file, subtitle_files, poster_files, other_files

def extract_year_from_filename(filename: str) -> Optional[int]:
    """Extract year from filename."""
    year_pattern = r'(?:19|20)\d{2}'
    match = re.search(year_pattern, filename)
    if match:
        return int(match.group())
    return None

def rename_movie_files(directory: str) -> Tuple[Dict[str, int], List[str], List[str]]:
    """Process movie files in folders and rename them according to the specified format."""
    if not os.path.exists(directory):
        logging.error(f"Directory not found: {directory}")
        return {'processed': 0, 'renamed': 0, 'skipped': 0, 'errors': 0}, [], []

    stats = {'processed': 0, 'renamed': 0, 'skipped': 0, 'errors': 0}
    warnings = []
    skipped_items = []
    ia = Cinemagoer()

    for folder_name in os.listdir(directory):
        folder_path = os.path.join(directory, folder_name)
        if not os.path.isdir(folder_path):
            continue

        stats['processed'] += 1
        logging.info(f"Processing folder: {folder_name}")

        # Get movie name and year from folder name
        media_name, year = parse_media_folder(folder_name)
        if not media_name or not year:
            # Try to extract from filename if folder name doesn't match pattern
            movie_file, _, _, _ = get_movie_files(folder_path)
            if movie_file:
                year = extract_year_from_filename(movie_file)
                if year:
                    media_name = re.sub(r'[._]', ' ', movie_file[:movie_file.find(str(year))]).strip()
                    media_name = re.sub(r'\s+', ' ', media_name)
                else:
                    logging.warning(f"Could not extract year from: {folder_name}")
                    warnings.append(f"No year found: {folder_name}")
                    stats['skipped'] += 1
                    continue
            else:
                logging.warning(f"Invalid folder format and no movie file: {folder_name}")
                warnings.append(f"Invalid format: {folder_name}")
                stats['skipped'] += 1
                continue

        # Check if folder already has IMDb ID and verify it
        existing_imdb_id = extract_imdb_id(folder_name)
        if existing_imdb_id:
            if verify_imdb_data(ia, existing_imdb_id, media_name, year):
                logging.info(f"Verified existing IMDb ID: tt{existing_imdb_id}")
                verified_name = media_name
                imdb_id = existing_imdb_id
            else:
                print(f"\nIMDb data mismatch for: {media_name} ({year})")
                choice = input("Do you want to (s)kip this item or (c)ontinue with verification? (s/c): ").strip().lower()
                if choice == 's':
                    stats['skipped'] += 1
                    continue
                # If continue, fall through to normal verification process
        
        # Verify movie name with IMDb if needed
        if not existing_imdb_id or not verify_imdb_data(ia, existing_imdb_id, media_name, year):
            verified_name, imdb_id = verify_movie_name(media_name, year)
            if not verified_name or not imdb_id:
                print(f"\nCould not verify movie: {media_name} ({year})")
                choice = input("Do you want to (s)kip this item or (c)ontinue with original name? (s/c): ").strip().lower()
                if choice == 's':
                    stats['skipped'] += 1
                    continue
                verified_name = media_name

        # Get files in the folder
        movie_file, subtitle_files, poster_files, other_files = get_movie_files(folder_path)
        
        if not movie_file:
            logging.warning(f"No movie file found in {folder_name}")
            warnings.append(f"No movie file or multiple movie files in: {folder_name}")
            stats['skipped'] += 1
            continue

        # Detect quality and ask for input only if detection fails
        quality = detect_quality(movie_file)
        if not quality:
            print(f"\nCould not detect quality for movie: {movie_file}")
            choice = input("Do you want to (s)kip this item or (i)nput quality manually? (s/i): ").strip().lower()
            if choice == 's':
                stats['skipped'] += 1
                continue
            elif choice == 'i':
                quality = get_quality_from_user()
            else:
                print("Invalid choice, skipping...")
                stats['skipped'] += 1
                continue

        if not quality:  # Double check we have a quality before proceeding
            logging.warning(f"No quality determined for: {movie_file}")
            warnings.append(f"No quality determined: {movie_file}")
            stats['skipped'] += 1
            continue

        # Create new movie filename
        _, ext = os.path.splitext(movie_file)
        new_movie_name = f"{verified_name} ({year}) - {quality}{ext}"
        old_movie_path = os.path.join(folder_path, movie_file)
        new_movie_path = os.path.join(folder_path, new_movie_name)

        try:
            # Rename movie file
            os.rename(old_movie_path, new_movie_path)
            logging.info(f"Renamed movie file: {movie_file} -> {new_movie_name}")
            stats['renamed'] += 1

            # Rename subtitle files
            for subtitle in subtitle_files:
                _, sub_ext = os.path.splitext(subtitle)
                new_sub_name = f"{verified_name} ({year}) - {quality}{sub_ext}"
                old_sub_path = os.path.join(folder_path, subtitle)
                new_sub_path = os.path.join(folder_path, new_sub_name)
                os.rename(old_sub_path, new_sub_path)
                logging.info(f"Renamed subtitle: {subtitle} -> {new_sub_name}")

            # Handle other files (excluding poster files)
            if other_files:
                print(f"\nThe following items in '{folder_name}' will be deleted:")
                for item in other_files:
                    print(f"- {item}")
                choice = input("Do you want to proceed with deletion? (y/n): ").strip().lower()
                if choice == 'y':
                    for item in other_files:
                        item_path = os.path.join(folder_path, item)
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        else:
                            import shutil
                            shutil.rmtree(item_path)
                    logging.info(f"Cleaned up {len(other_files)} items in {folder_name}")

            # Log preserved poster files
            if poster_files:
                logging.info(f"Preserved {len(poster_files)} poster files: {', '.join(poster_files)}")

        except Exception as e:
            logging.error(f"Error processing {folder_name}: {str(e)}")
            warnings.append(f"Error in {folder_name}: {str(e)}")
            stats['errors'] += 1

    return stats, skipped_items, warnings

def parse_media_folder(folder_name):
    """Extract name and year from folder name."""
    pattern = r"(.+)\s*\((\d{4})\)"
    match = re.match(pattern, folder_name)
    if match:
        return match.group(1).strip(), int(match.group(2))
    return None, None

def get_user_decision(folder_name):
    """Ask user whether to skip or stop when an error occurs."""
    while True:
        print(f"\nCould not find IMDb match for: {folder_name}")
        choice = input("Do you want to (s)kip this item or st(o)p the process? (s/o): ").strip().lower()
        if choice in ['s', 'o']:
            return choice
        print("Invalid choice. Please enter 's' to skip or 'o' to stop.")

def get_batch_size():
    """Get the number of titles to process in each batch."""
    while True:
        try:
            size = input("\nEnter batch size (0 for all at once): ").strip()
            batch_size = int(size)
            if batch_size < 0:
                print("Please enter a non-negative number.")
                continue
            return batch_size
        except ValueError:
            print("Please enter a valid number.")

def should_continue():
    """Ask user if they want to process the next batch."""
    while True:
        choice = input("\nDo you want to process the next batch? (y/n): ").strip().lower()
        if choice in ['y', 'n']:
            return choice == 'y'
        print("Please enter 'y' for yes or 'n' for no.")

def get_imdb_id(name, year, media_type='movie'):
    """Search IMDb for media and return its ID."""
    ia = Cinemagoer()
    try:
        if media_type == 'movie':
            # Search for movies
            results = ia.search_movie(name)
            logging.debug(f"Found {len(results)} movie results for: {name}")
            
            # Filter for movies only
            results = [r for r in results if r.get('kind') == 'movie']
        else:
            # Search for TV series
            results = ia.search_movie(name)
            logging.debug(f"Found {len(results)} initial results for TV show: {name}")
            
            # Filter for TV series only and log each result for debugging
            tv_results = []
            for r in results:
                kind = r.get('kind', 'unknown')
                logging.debug(f"Found result: {r.get('title')} ({r.get('year', 'N/A')}) - Type: {kind}")
                if kind in ['tv series', 'tv mini series']:
                    tv_results.append(r)
            results = tv_results
            
            logging.debug(f"Filtered to {len(results)} TV series results")
        
        # Log all potential matches
        for item in results:
            logging.debug(f"Potential match: {item.get('title')} ({item.get('year', 'N/A')}) - {item.get('kind', 'unknown')}")
        
        # Try exact year match first
        for item in results:
            if item.get('year') == year:
                logging.info(f"Found exact year match: {item.get('title')} ({item.get('year')}) - tt{item.getID()}")
                return item.getID()
        
        # If no exact year match, check for close matches and log them
        close_matches = [item for item in results if abs(item.get('year', 0) - year) <= 1]
        if close_matches:
            logging.info(f"Found close year match: {close_matches[0].get('title')} ({close_matches[0].get('year')}) - tt{close_matches[0].getID()}")
            return close_matches[0].getID()
        
        logging.warning(f"No match found for: {name} ({year}) - Type: {media_type}")
        return None
    except Exception as e:
        logging.error(f"Error searching for {name}: {str(e)}")
        return None

def rename_media_folders(directory, media_type='movie', batch_size=0) -> Tuple[Dict[str, int], List[str], List[str]]:
    """Process media folders in the given directory with batch support."""
    if not os.path.exists(directory):
        logging.error(f"Directory not found: {directory}")
        return {'processed': 0, 'renamed': 0, 'skipped': 0, 'errors': 0}, [], []

    logging.info(f"Starting to process {media_type} folders in: {directory}")
    
    # Get all folders to process
    all_folders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
    total_folders = len(all_folders)
    
    # Initialize statistics and tracking lists
    stats = {
        'processed': 0,
        'renamed': 0,
        'skipped': 0,
        'errors': 0
    }
    skipped_items = []
    warnings = []
    
    # Process in batches if batch_size > 0, otherwise process all at once
    start_idx = 0
    while start_idx < total_folders:
        if batch_size > 0:
            end_idx = min(start_idx + batch_size, total_folders)
            current_batch = all_folders[start_idx:end_idx]
            print(f"\nProcessing batch {(start_idx // batch_size) + 1} "
                  f"(items {start_idx + 1} to {end_idx} of {total_folders})")
        else:
            current_batch = all_folders[start_idx:]
            end_idx = total_folders

        # Process current batch
        for folder_name in current_batch:
            folder_path = os.path.join(directory, folder_name)
            stats['processed'] += 1
            
            # Skip if already has IMDb ID
            if "{" in folder_name:
                logging.info(f"Skipping already tagged folder: {folder_name}")
                skipped_items.append(f"Already tagged: {folder_name}")
                stats['skipped'] += 1
                continue

            # Parse name and year
            media_name, year = parse_media_folder(folder_name)
            if not media_name or not year:
                logging.warning(f"Skipping {folder_name} - Invalid format")
                warnings.append(f"Invalid format: {folder_name}")
                stats['skipped'] += 1
                continue

            logging.info(f"Processing: {media_name} ({year})")
            
            # Get IMDb ID
            imdb_id = get_imdb_id(media_name, year, media_type)
            if not imdb_id:
                # Ask user what to do
                decision = get_user_decision(folder_name)
                logging.info(f"User decided to {'skip' if decision == 's' else 'stop'} for: {folder_name}")
                
                if decision == 'o':
                    logging.info("User chose to stop the process")
                    print("\nStopping the process as requested.")
                    warnings.append(f"No IMDb match (process stopped): {folder_name}")
                    return stats, skipped_items, warnings
                
                warnings.append(f"No IMDb match (skipped): {folder_name}")
                stats['skipped'] += 1
                continue

            # Create new folder name
            new_name = f"{folder_name} {{tt{imdb_id}}}"
            new_path = os.path.join(directory, new_name)

            # Rename folder
            try:
                os.rename(folder_path, new_path)
                logging.info(f"Successfully renamed: {folder_name} -> {new_name}")
                stats['renamed'] += 1
            except Exception as e:
                logging.error(f"Error renaming {folder_name}: {str(e)}")
                warnings.append(f"Rename error: {folder_name} ({str(e)})")
                stats['errors'] += 1

        # Print batch statistics
        if batch_size > 0:
            print(f"\nBatch {(start_idx // batch_size) + 1} complete:")
            print(f"Processed: {end_idx - start_idx}")
            print(f"Renamed: {stats['renamed']}")
            print(f"Skipped: {stats['skipped']}")
            print(f"Errors: {stats['errors']}")
            
            # Ask to continue if there are more items
            if end_idx < total_folders:
                if not should_continue():
                    logging.info("User chose not to process next batch")
                    print("\nStopping as requested.")
                    break

        start_idx = end_idx

    return stats, skipped_items, warnings

def get_media_type() -> Optional[str]:
    """Get user's choice of media type."""
    while True:
        print("\nWhat would you like to do?")
        print("1. Rename Movie - Folders")
        print("2. Rename Movie - Files")
        print("3. TV Shows - Folders")
        print("4. Exit")
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            logging.info("User selected: Movie Folders")
            return "movie_folders"
        elif choice == "2":
            logging.info("User selected: Movie Files")
            return "movie_files"
        elif choice == "3":
            logging.info("User selected: TV Shows")
            return "tv"
        elif choice == "4":
            logging.info("User chose to exit")
            return None
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

def get_media_path():
    """Get media library path from user."""
    while True:
        path = input("\nEnter the path to your media library: ").strip()
        if os.path.exists(path):
            logging.info(f"Selected media library path: {path}")
            return path
        else:
            print("Invalid path. Please enter a valid directory path.")

def print_report(stats: Dict[str, int], skipped_items: List[str], warnings: List[str]):
    """Print the operation report with skipped items and warnings."""
    print("\n=== Operation Report ===")
    print(f"Total folders processed: {stats['processed']}")
    print(f"Successfully renamed: {stats['renamed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Errors: {stats['errors']}")

    if skipped_items:
        print("\n=== Skipped Items ===")
        for item in skipped_items:
            print(f"- {item}")

    if warnings:
        print("\n=== Warnings ===")
        for warning in warnings:
            print(f"- {warning}")

def get_next_action() -> bool:
    """Ask user if they want to start over or exit."""
    while True:
        print("\nWhat would you like to do next?")
        print("1. Start a new renaming session")
        print("2. Exit")
        choice = input("Enter your choice (1-2): ").strip()
        
        if choice == "1":
            logging.info("User chose to start a new session")
            return True
        elif choice == "2":
            logging.info("User chose to exit")
            return False
        else:
            print("Invalid choice. Please enter 1 or 2.")

def main():
    """Main program loop."""
    while True:
        # Setup logging for this session
        log_file = setup_logging()
        
        try:
            print(f"=== Leo Media Renamer v{VERSION} ===")
            logging.info("Starting new renaming session")
            
            # Get media type choice from user
            media_type = get_media_type()
            if media_type is None:
                print("\nExiting program.")
                break
            
            # Get media library path
            media_path = get_media_path()
            
            if media_type == "movie_files":
                # Process movie files
                stats, skipped_items, warnings = rename_movie_files(media_path)
            else:
                # Get batch size for folder processing
                batch_size = get_batch_size()
                logging.info(f"Batch size set to: {batch_size}")
                
                # Process the media folders
                stats, skipped_items, warnings = rename_media_folders(
                    media_path,
                    "movie" if media_type == "movie_folders" else "tv",
                    batch_size
                )
            
            # Print the final report
            print_report(stats, skipped_items, warnings)
            
            logging.info("Session completed successfully")
            print(f"\nOperation complete! Log file created at: {log_file}")
            
            # Ask user what to do next
            if not get_next_action():
                print("\nExiting program.")
                break
        
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            print(f"\nAn error occurred. Check the log file for details: {log_file}")
            if not get_next_action():
                break

if __name__ == "__main__":
    main()
