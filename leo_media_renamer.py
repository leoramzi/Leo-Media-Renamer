#!/usr/bin/env python3
"""
Leo Media Renamer - A Media Library IMDb Code Renamer

This script renames movie and TV show folders by adding IMDb codes to their names.
It processes folders formatted as "Name (Year)" and adds the IMDb code in the format
"Name (Year) {IMDb-ID}".

Author: Leo
GitHub: https://github.com/yourusername/Leo-Media-Renamer
"""

import os
import re
import logging
import sys
from imdb import Cinemagoer
from datetime import datetime

# ============= CONFIGURATION =============
# Logging configuration
LOG_DIR = "MediaRenamerLog"
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
    
    logging.info("=== Leo Media Renamer Session Started ===")
    return log_file

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

def rename_media_folders(directory, media_type='movie'):
    """Process all media folders in the given directory."""
    if not os.path.exists(directory):
        logging.error(f"Directory not found: {directory}")
        return

    logging.info(f"Starting to process {media_type} folders in: {directory}")
    
    # Count statistics
    stats = {
        'processed': 0,
        'renamed': 0,
        'skipped': 0,
        'errors': 0
    }

    for folder_name in os.listdir(directory):
        folder_path = os.path.join(directory, folder_name)
        stats['processed'] += 1
        
        # Skip if not a directory or already has IMDb ID
        if not os.path.isdir(folder_path):
            logging.debug(f"Skipping non-directory: {folder_name}")
            stats['skipped'] += 1
            continue
        
        if "{" in folder_name:
            logging.info(f"Skipping already tagged folder: {folder_name}")
            stats['skipped'] += 1
            continue

        # Parse name and year
        media_name, year = parse_media_folder(folder_name)
        if not media_name or not year:
            logging.warning(f"Skipping {folder_name} - Invalid format")
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
                # Log final statistics before stopping
                logging.info("\nOperation Statistics (Incomplete - User Stopped):")
                logging.info(f"Total folders processed: {stats['processed']}")
                logging.info(f"Successfully renamed: {stats['renamed']}")
                logging.info(f"Skipped: {stats['skipped']}")
                logging.info(f"Errors: {stats['errors']}")
                return
            
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
            stats['errors'] += 1

    # Log statistics
    logging.info("\nOperation Statistics:")
    logging.info(f"Total folders processed: {stats['processed']}")
    logging.info(f"Successfully renamed: {stats['renamed']}")
    logging.info(f"Skipped: {stats['skipped']}")
    logging.info(f"Errors: {stats['errors']}")

def get_media_type():
    """Get user's choice of media type."""
    while True:
        print("\nWhat type of media do you want to process?")
        print("1. Movies")
        print("2. TV Shows")
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == "1":
            logging.info("User selected: Movies")
            return "movie"
        elif choice == "2":
            logging.info("User selected: TV Shows")
            return "tv"
        else:
            print("Invalid choice. Please enter 1 or 2.")

def get_media_path():
    """Get media library path from user."""
    while True:
        path = input("\nEnter the path to your media library: ").strip()
        if os.path.exists(path):
            logging.info(f"Selected media library path: {path}")
            return path
        else:
            print("Invalid path. Please enter a valid directory path.")

if __name__ == "__main__":
    # Setup logging
    log_file = setup_logging()
    
    try:
        print("=== Leo Media Renamer ===")
        logging.info("Starting new renaming session")
        
        # Get media type choice from user
        media_type = get_media_type()
        
        # Get media library path
        media_path = get_media_path()
        
        # Process the media folders
        rename_media_folders(media_path, media_type)
        
        logging.info("Session completed successfully")
        print(f"\nOperation complete! Log file created at: {log_file}")
    
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        print(f"\nAn error occurred. Check the log file for details: {log_file}")
