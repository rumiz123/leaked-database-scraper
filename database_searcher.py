import os
import time
import threading


def find_files(folder_path, extensions):
    """
    Find all files with specified extensions in folder and subfolders
    """
    matched_files = []
    total_size_bytes = 0

    print("Scanning for files...")

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext.lower()) for ext in extensions):
                full_path = os.path.join(root, file)
                matched_files.append(full_path)

                # Get file size for statistics
                try:
                    file_size = os.path.getsize(full_path)
                    total_size_bytes += file_size
                except:
                    pass

    return matched_files, total_size_bytes


def search_string_in_files(search_string, folder_path, file_extensions):
    """
    Search for a string in all specified files in folder and subfolders with progress tracking
    """
    # Find all matching files
    all_files, total_size_bytes = find_files(folder_path, file_extensions)
    total_files = len(all_files)

    if total_files == 0:
        print(f"No files found with extensions: {', '.join(file_extensions)}")
        return

    # Calculate total size in GB
    total_size_gb = total_size_bytes / (1024 ** 3)

    print(f"Found {total_files} files to search.")
    print(f"Searching for '{search_string}' in {total_files} files...")
    print(f"Total data to search: ~{total_size_gb:.2f} GB")
    print(f"File types: {', '.join(file_extensions)}")
    print("-" * 60)

    found_in_files = []
    processed_files = 0
    start_time = time.time()

    # Progress tracking thread
    def update_progress():
        while processed_files < total_files:
            elapsed = time.time() - start_time
            progress = (processed_files / total_files) * 100
            files_per_sec = processed_files / elapsed if elapsed > 0 else 0
            remaining_time = (total_files - processed_files) / files_per_sec if files_per_sec > 0 else 0

            print(f"\rProgress: {progress:.1f}% ({processed_files}/{total_files}) | "
                  f"Elapsed: {elapsed:.1f}s | "
                  f"Speed: {files_per_sec:.1f} files/s | "
                  f"ETA: {remaining_time:.1f}s", end="", flush=True)
            time.sleep(0.5)

    # Start progress thread
    progress_thread = threading.Thread(target=update_progress)
    progress_thread.daemon = True
    progress_thread.start()

    # Search through each file
    for file_path in all_files:
        try:
            # Get relative path for cleaner output
            rel_path = os.path.relpath(file_path, folder_path)

            # Read file line by line to handle large files
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                for line_num, line in enumerate(file, 1):
                    if search_string in line:
                        found_in_files.append({
                            'file': rel_path,
                            'full_path': file_path,
                            'line_number': line_num,
                            'preview': line.strip()[:100] + '...' if len(line.strip()) > 100 else line.strip()
                        })
                        break  # Stop searching this file after first match

        except Exception as e:
            print(f"\nError reading {file_path}: {str(e)}")

        processed_files += 1

    # Final progress update
    elapsed = time.time() - start_time
    print(f"\rProgress: 100.0% ({total_files}/{total_files}) | "
          f"Elapsed: {elapsed:.1f}s | "
          f"Speed: {total_files / elapsed:.1f} files/s")

    # Display results
    print("\n" + "=" * 60)
    print("SEARCH RESULTS:")
    print("=" * 60)

    if found_in_files:
        print(f"✓ Found '{search_string}' in {len(found_in_files)} files:")
        print("-" * 60)
        for result in found_in_files:
            print(f"  • File: {result['file']}")
            print(f"    Line: {result['line_number']}")
            print(f"    Preview: {result['preview']}")
            print()
    else:
        print(f"✗ String '{search_string}' not found in any files.")

    # Summary statistics
    print(f"\nSUMMARY:")
    print(f"• Files searched: {total_files}")
    print(f"• Total data: {total_size_gb:.2f} GB")
    print(f"• Files with matches: {len(found_in_files)}")
    print(f"• Search time: {elapsed:.2f} seconds")


def get_user_input():
    """Get search configuration from user"""
    print("=" * 50)
    print("      ADVANCED FILE SEARCH TOOL")
    print("=" * 50)

    # Get search string
    search_string = input("Enter the text you want to search for: ").strip()
    if not search_string:
        print("Error: Search string cannot be empty.")
        return None, None, None

    # Get folder path
    folder_path = input("Enter the folder path to search in: ").strip()
    if not folder_path:
        print("Error: Folder path cannot be empty.")
        return None, None, None

    # Get file extensions
    print("\nAvailable file types: .txt, .csv, .sql")
    extensions_input = input("Enter file extensions to search (comma-separated, or press Enter for all): ").strip()

    if extensions_input:
        # Parse user-specified extensions
        file_extensions = [ext.strip() for ext in extensions_input.split(',')]
        # Ensure extensions start with dot
        file_extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in file_extensions]
    else:
        # Default extensions
        file_extensions = ['.txt', '.csv', '.sql']

    # Remove quotes if user pasted a path with them
    folder_path = folder_path.strip('"\'')

    return search_string, folder_path, file_extensions


def main():
    # Get user input
    search_string, folder_path, file_extensions = get_user_input()

    if search_string and folder_path and file_extensions:
        print(f"\nStarting search...")
        print(f"Search for: '{search_string}'")
        print(f"Search location: '{folder_path}'")
        print(f"File types: {', '.join(file_extensions)}")
        print(f"Include subfolders: Yes")
        print()

        # Validate folder exists
        if not os.path.exists(folder_path):
            print(f"Error: The folder '{folder_path}' does not exist.")
            return

        search_string_in_files(search_string, folder_path, file_extensions)


if __name__ == "__main__":
    main()