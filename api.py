import os
import time
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
DEFAULT_SEARCH_LOCATION = 'ADD LOCATION OF YOUR LEAKS FOLDER HERE'
DEFAULT_PORT = 8080


def find_files(folder_path, extensions):
    """
    Find all files with specified extensions in folder and subfolders
    """
    matched_files = []
    total_size_bytes = 0

    logger.info(f"Scanning for files in {folder_path} with extensions: {extensions}")

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
    Search for a string in all specified files in folder and subfolders
    Returns results as a dictionary for API response
    """
    # Find all matching files
    all_files, total_size_bytes = find_files(folder_path, file_extensions)
    total_files = len(all_files)

    if total_files == 0:
        return {
            "error": f"No files found with extensions: {', '.join(file_extensions)}",
            "files_searched": 0,
            "matches_found": 0
        }

    # Calculate total size in GB
    total_size_gb = total_size_bytes / (1024 ** 3)

    logger.info(f"Found {total_files} files to search.")
    logger.info(f"Searching for '{search_string}' in {total_files} files...")
    logger.info(f"Total data to search: ~{total_size_gb:.2f} GB")

    found_in_files = []
    processed_files = 0
    start_time = time.time()

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
                            'preview': line.strip()[:100] + '...' if len(line.strip()) > 100 else line.strip(),
                            'full_line': line.strip()
                        })
                        break  # Stop searching this file after first match

        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")

        processed_files += 1

    # Calculate final statistics
    elapsed = time.time() - start_time

    # Prepare response
    response = {
        "search_string": search_string,
        "search_location": folder_path,
        "file_extensions": file_extensions,
        "summary": {
            "files_searched": total_files,
            "total_data_gb": round(total_size_gb, 2),
            "matches_found": len(found_in_files),
            "search_time_seconds": round(elapsed, 2),
            "files_per_second": round(total_files / elapsed, 2) if elapsed > 0 else 0
        },
        "matches": found_in_files
    }

    return response


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "file_search_api",
        "search_location": DEFAULT_SEARCH_LOCATION,
        "timestamp": time.time()
    })


@app.route('/search', methods=['GET', 'POST'])
def search_files():
    """
    Search endpoint - accepts both GET and POST requests
    GET params or POST JSON: search_string, extensions (optional)
    """
    start_time = time.time()

    # Get parameters from request
    if request.method == 'GET':
        search_string = request.args.get('search_string', '').strip()
        extensions_input = request.args.get('extensions', '').strip()
    else:  # POST
        data = request.get_json(silent=True) or {}
        search_string = data.get('search_string', '').strip()
        extensions_input = data.get('extensions', '').strip()

    # Validate search string
    if not search_string:
        return jsonify({
            "error": "Search string is required",
            "usage": {
                "GET": "/search?search_string=your_text&extensions=txt,csv,sql",
                "POST": '{"search_string": "your_text", "extensions": "txt,csv,sql"}'
            }
        }), 400

    # Process file extensions
    if extensions_input:
        file_extensions = [ext.strip() for ext in extensions_input.split(',')]
        file_extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in file_extensions]
    else:
        # Default extensions
        file_extensions = ['.txt', '.csv', '.sql']

    # Validate search location exists
    if not os.path.exists(DEFAULT_SEARCH_LOCATION):
        return jsonify({
            "error": f"Search location '{DEFAULT_SEARCH_LOCATION}' does not exist",
            "search_string": search_string
        }), 500

    # Perform the search
    try:
        result = search_string_in_files(search_string, DEFAULT_SEARCH_LOCATION, file_extensions)

        # Add request metadata
        result["request"] = {
            "method": request.method,
            "processing_time": round(time.time() - start_time, 3)
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({
            "error": f"Search failed: {str(e)}",
            "search_string": search_string,
            "search_location": DEFAULT_SEARCH_LOCATION
        }), 500


@app.route('/search/status', methods=['GET'])
def search_status():
    """Get information about the search location"""
    try:
        if not os.path.exists(DEFAULT_SEARCH_LOCATION):
            return jsonify({
                "error": f"Search location '{DEFAULT_SEARCH_LOCATION}' does not exist"
            }), 404

        # Get basic stats about the search location
        total_files = 0
        total_size_bytes = 0
        file_types = {}

        for root, dirs, files in os.walk(DEFAULT_SEARCH_LOCATION):
            for file in files:
                total_files += 1
                file_ext = os.path.splitext(file)[1].lower()
                file_types[file_ext] = file_types.get(file_ext, 0) + 1

                try:
                    file_path = os.path.join(root, file)
                    total_size_bytes += os.path.getsize(file_path)
                except:
                    pass

        return jsonify({
            "search_location": DEFAULT_SEARCH_LOCATION,
            "exists": True,
            "statistics": {
                "total_files": total_files,
                "total_size_gb": round(total_size_bytes / (1024 ** 3), 2),
                "file_types": file_types
            },
            "supported_extensions": ['.txt', '.csv', '.sql']
        })

    except Exception as e:
        return jsonify({
            "error": f"Failed to get search location status: {str(e)}"
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "available_endpoints": [
        "/health",
        "/search",
        "/search/status"
    ]}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


def main():
    """
    Main function to start the API server
    """
    print("=" * 60)
    print("           FILE SEARCH API SERVER")
    print("=" * 60)
    print(f"Search location: {DEFAULT_SEARCH_LOCATION}")
    print(f"API URL: http://localhost:{DEFAULT_PORT}")
    print(f"Endpoints:")
    print(f"  GET  /health         - Health check")
    print(f"  GET  /search/status  - Search location status")
    print(f"  GET  /search?search_string=text&extensions=txt,csv")
    print(f"  POST /search         - JSON: {{'search_string': 'text', 'extensions': 'txt,csv'}}")
    print("=" * 60)

    # Check if search location exists
    if not os.path.exists(DEFAULT_SEARCH_LOCATION):
        print(f"⚠️  WARNING: Search location '{DEFAULT_SEARCH_LOCATION}' does not exist!")
        print("   Please create the directory or update DEFAULT_SEARCH_LOCATION in the script.")
        print("   The API will still start but searches will fail.")

    # Start Flask server
    app.run(host='0.0.0.0', port=DEFAULT_PORT, debug=False)


if __name__ == "__main__":
    main()