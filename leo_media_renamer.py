#!/usr/bin/env python3
"""
Leo Media Renamer - A Media Library IMDb Code Renamer
Version: 0.0.5

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
VERSION = "0.0.5"
# Logging configuration
LOG_DIR = "MediaRenamerLog"

# Quality patterns
RESOLUTIONS = ['720p', '1080p', '2160p']
SOURCES = ['HDTV', 'WEBDL', 'WEBRip', 'Bluray', 'Remux', 'BR-DISK', 'Raw-HD', 'BrRip']

# Special characters replacement
SPECIAL_CHARS = {
    ':': ' -',
    '/': ' -',
    '\\': ' -',
    '*': ' -',
    '?': ' -',
    '"': ' -',
    '<': ' -',
    '>': ' -',
    '|': ' -',
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

def verify_imdb_data(ia: Cinemagoer, imdb_id: str, name: str, year: int) -> Tuple[bool, Optional[str]]:
    """Verify if the IMDb ID matches with the given name and year."""
    try:
        movie = ia.get_movie(imdb_id)
        if not movie:
            return False, None
        
        # Get movie title and year from IMDb
        imdb_title = movie.get('title')
        imdb_year = movie.get('year')
        
        # Compare title (case-insensitive) and year
        # First, normalize both titles by removing ':' and extra spaces
        normalized_name = re.sub(r'\s*:\s*', ' ', name.lower())
        normalized_imdb = re.sub(r'\s*:\s*', ' ', imdb_title.lower())
        
        if normalized_name == normalized_imdb and (imdb_year == year or abs(imdb_year - year) <= 1):
            return True, None
        
        # If there's a mismatch, return the IMDb title for user verification
        logging.warning(f"IMDb mismatch - Folder: {name} ({year}), IMDb: {imdb_title} ({imdb_year})")
        return False, imdb_title
    except Exception as e:
        logging.error(f"Error verifying IMDb data: {str(e)}")
        return False, None

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

def get_movie_files(folder_path: str) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Get movie files, subtitle files, poster files, and other files in the folder."""
    movie_extensions = {'.mp4', '.mkv', '.avi', '.m4v', '.mov'}
    subtitle_extensions = {'.srt', '.sub', '.ass', '.ssa'}
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    
    movie_files = []
    subtitle_files = []
    poster_files = []
    other_files = []
    
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        name_without_ext, ext = os.path.splitext(item.lower())
        
        if os.path.isfile(item_path):
            if ext in movie_extensions:
                movie_files.append(item)
            elif ext in subtitle_extensions:
                subtitle_files.append(item)
            elif ext in image_extensions and name_without_ext in ['poster', 'Poster']:
                poster_files.append(item)
            else:
                other_files.append(item)
        else:
            other_files.append(item)
    
    return movie_files, subtitle_files, poster_files, other_files

def extract_year_from_filename(filename: str) -> Optional[int]:
    """Extract year from filename."""
    year_pattern = r'(?:19|20)\d{2}'
    match = re.search(year_pattern, filename)
    if match:
        return int(match.group())
    return None

def rename_movies(directory: str) -> Tuple[Dict[str, int], List[str], List[str]]:
    """Process movie folders and files with the new combined workflow."""
    if not os.path.exists(directory):
        logging.error(f"Directory not found: {directory}")
        return {'processed': 0, 'renamed': 0, 'skipped': 0, 'errors': 0}, [], []

    # Ask about IMDb ID addition
    print("\nDo you want to add IMDb IDs to folder names if they're missing?")
    add_imdb = input("Add IMDb IDs? (y/n): ").strip().lower() == 'y'
    logging.info(f"IMDb ID addition {'enabled' if add_imdb else 'disabled'}")

    # Ask about IMDb verification
    print("\nDo you want to verify existing movie names and IMDb IDs?")
    verify_imdb = input("Verify with IMDb? (y/n): ").strip().lower() == 'y'
    logging.info(f"IMDb verification {'enabled' if verify_imdb else 'disabled'}")

    # Ask about file renaming
    print("\nDo you want to rename movie files inside the folders?")
    rename_files = input("Rename files? (y/n): ").strip().lower() == 'y'
    logging.info(f"File renaming {'enabled' if rename_files else 'disabled'}")

    stats = {'processed': 0, 'renamed': 0, 'skipped': 0, 'errors': 0}
    warnings = []
    skipped_items = []
    ia = Cinemagoer() if (add_imdb or verify_imdb) else None

    for folder_name in os.listdir(directory):
        folder_path = os.path.join(directory, folder_name)
        if not os.path.isdir(folder_path):
            continue

        stats['processed'] += 1
        logging.info(f"Processing folder: {folder_name}")

        # Get movie name and year from folder name
        media_name, year = parse_media_folder(folder_name)
        if not media_name or not year:
            logging.warning(f"Invalid folder format: {folder_name}")
            warnings.append(f"Invalid format: {folder_name}")
            stats['skipped'] += 1
            continue

        verified_name = media_name
        imdb_id = None
        folder_renamed = False

        # Handle IMDb verification and ID addition
        if verify_imdb or add_imdb:
            existing_imdb_id = extract_imdb_id(folder_name)
            
            if existing_imdb_id and verify_imdb:
                matches, imdb_title = verify_imdb_data(ia, existing_imdb_id, media_name, year)
                if matches:
                    logging.info(f"Verified existing IMDb ID: tt{existing_imdb_id}")
                    verified_name = media_name
                    imdb_id = existing_imdb_id
                else:
                    if imdb_title:
                        print(f"\nIMDb data mismatch for: {media_name} ({year})")
                        print(f"IMDb title: {imdb_title}")
                        choice = input("Use IMDb title? (y/n/s=skip): ").strip().lower()
                        if choice == 's':
                            stats['skipped'] += 1
                            continue
                        elif choice == 'y':
                            verified_name = sanitize_filename(imdb_title)
                            imdb_id = existing_imdb_id
                            folder_renamed = True
            
            if not imdb_id and add_imdb:
                verified_name, new_imdb_id = verify_movie_name(media_name, year)
                if new_imdb_id:
                    imdb_id = new_imdb_id
                    folder_renamed = True
                else:
                    print(f"\nCould not find IMDb match for: {media_name} ({year})")
                    choice = input("Skip this movie? (y/n): ").strip().lower()
                    if choice == 'y':
                        stats['skipped'] += 1
                        continue

        # Rename folder if needed
        if folder_renamed or (imdb_id and not extract_imdb_id(folder_name)):
            new_folder_name = f"{verified_name} ({year})"
            if imdb_id:
                new_folder_name += f" {{tt{imdb_id}}}"
            new_folder_path = os.path.join(directory, new_folder_name)
            
            try:
                os.rename(folder_path, new_folder_path)
                logging.info(f"Renamed folder: {folder_name} -> {new_folder_name}")
                folder_path = new_folder_path
                stats['renamed'] += 1
            except Exception as e:
                logging.error(f"Error renaming folder {folder_name}: {str(e)}")
                warnings.append(f"Folder rename error: {folder_name}")
                stats['errors'] += 1
                continue

        # Handle file renaming if enabled
        if rename_files:
            movie_files, subtitle_files, poster_files, other_files = get_movie_files(folder_path)
            
            if not movie_files:
                logging.warning(f"No movie files found in {folder_name}")
                warnings.append(f"No movie files: {folder_name}")
                continue

            # Handle multiple movie files
            if len(movie_files) > 1:
                print(f"\nMultiple movie files found in {folder_name}:")
                for idx, movie_file in enumerate(movie_files, 1):
                    print(f"{idx}. {movie_file}")
                
                print("\nOptions:")
                print("1. Attempt to rename all files")
                print("2. Skip this movie")
                choice = input("Enter your choice (1/2): ").strip()
                
                if choice == "2":
                    logging.info(f"Skipping multiple movie files in: {folder_name}")
                    warnings.append(f"Skipped multiple files: {folder_name}")
                    stats['skipped'] += 1
                    continue

            # Process each movie file
            for movie_file in movie_files:
                # Detect quality
                quality = detect_quality(movie_file)
                if not quality:
                    print(f"\nCould not detect quality for movie: {movie_file}")
                    print("Options:")
                    print("1. Input quality manually")
                    print("2. Skip this file")
                    choice = input("Enter your choice (1/2): ").strip()
                    
                    if choice == "1":
                        quality = get_quality_from_user()
                    else:
                        logging.warning(f"Skipping file due to unknown quality: {movie_file}")
                        continue

                if quality:
                    # Rename movie file
                    _, ext = os.path.splitext(movie_file)
                    new_movie_name = f"{verified_name} ({year}) - {quality}{ext}"
                    try:
                        os.rename(
                            os.path.join(folder_path, movie_file),
                            os.path.join(folder_path, new_movie_name)
                        )
                        logging.info(f"Renamed movie file: {movie_file} -> {new_movie_name}")
                        
                        # Find and rename matching subtitle files
                        movie_name_without_ext = os.path.splitext(movie_file)[0]
                        matching_subtitles = [
                            sub for sub in subtitle_files
                            if os.path.splitext(sub)[0].startswith(movie_name_without_ext)
                        ]
                        
                        for subtitle in matching_subtitles:
                            _, sub_ext = os.path.splitext(subtitle)
                            new_sub_name = f"{verified_name} ({year}) - {quality}{sub_ext}"
                            os.rename(
                                os.path.join(folder_path, subtitle),
                                os.path.join(folder_path, new_sub_name)
                            )
                            logging.info(f"Renamed subtitle: {subtitle} -> {new_sub_name}")
                            subtitle_files.remove(subtitle)  # Remove processed subtitle

                    except Exception as e:
                        logging.error(f"Error processing file {movie_file}: {str(e)}")
                        warnings.append(f"File processing error: {movie_file}")
                        stats['errors'] += 1

            # Handle remaining files
            if other_files:
                print(f"\nThe following items in '{folder_name}' will be deleted:")
                for item in other_files:
                    print(f"- {item}")
                if input("Proceed with deletion? (y/n): ").strip().lower() == 'y':
                    for item in other_files:
                        item_path = os.path.join(folder_path, item)
                        try:
                            if os.path.isfile(item_path):
                                os.remove(item_path)
                            else:
                                import shutil
                                shutil.rmtree(item_path)
                        except Exception as e:
                            logging.error(f"Error deleting {item}: {str(e)}")
                    logging.info(f"Cleaned up {len(other_files)} items")

    return stats, skipped_items, warnings

def parse_media_folder(folder_name):
    """Extract name and year from folder name."""
    pattern = r"(.+)\s*\((\d{4})\)"
    match = re.match(pattern, folder_name)
    if match:
        return match.group(1).strip(), int(match.group(2))
    return None, None

def get_media_type() -> Optional[str]:
    """Get user's choice of media type."""
    while True:
        print("\nWhat would you like to do?")
        print("1. Rename Movies")
        print("2. TV Shows - Folders")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            logging.info("User selected: Movies")
            return "movies"
        elif choice == "2":
            logging.info("User selected: TV Shows")
            return "tv"
        elif choice == "3":
            logging.info("User chose to exit")
            return None
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

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
    print(f"Total items processed: {stats['processed']}")
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
    """Ask user if they want to return to main menu or exit."""
    while True:
        print("\nWhat would you like to do next?")
        print("1. Main Menu")
        print("2. Exit")
        choice = input("Enter your choice (1-2): ").strip()
        
        if choice == "1":
            logging.info("User chose to return to main menu")
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
            
            if media_type == "movies":
                # Process movies with combined workflow
                stats, skipped_items, warnings = rename_movies(media_path)
            else:
                # Process TV shows
                stats, skipped_items, warnings = rename_media_folders(
                    media_path,
                    "tv",
                    get_batch_size()
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
