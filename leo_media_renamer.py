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
        print("1. Process Movies")
        print("2. Process TV Shows")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            logging.info("User selected: Movies")
            return "movie"
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
            
            # Get batch size
            batch_size = get_batch_size()
            logging.info(f"Batch size set to: {batch_size}")
            
            # Process the media folders
            stats, skipped_items, warnings = rename_media_folders(media_path, media_type, batch_size)
            
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
