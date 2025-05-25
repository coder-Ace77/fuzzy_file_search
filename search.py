# textual_file_search/search.py
from pathlib import Path
import os
from typing import List, Tuple
import math

# Define a set of directory names that should *always* be excluded.
# This list now implicitly covers hidden directories that are commonly
# undesirable in a search, such as .git, .venv, .cache, etc.
ALWAYS_EXCLUDED_DIR_NAMES = {
    '.git', '.vscode', '.idea', '.venv', 'venv', '.env', 'node_modules', '__pycache__',
    '.npm', '.thunderbird', '.ssh', '.gnupg', '.docker', '.gradle', '.m2', '.pki',
    '.ansible', '.aws', '.kube', '.terraform', '.terraform.d', '.history', '.Trash',
    '.trash', '.thumbnails', '.dbus', '.gvfs', '.compose-cache', '.bundle', '.condarc',
    '.cpan', '.nuget', '.rustup', '.stack', '.texlive', '.vim', '.vscode-oss', '.android',
    '.atom', '.bazel', '.cargo', '.composer', '.cypress', '.dart', '.fvm', '.go',
    '.ipython', '.java', '.jupyter', '.nvm', '.platformio', '.pub-cache',
    '.python_history', '.rbenv', '.sbt', '.sdkman', '.tooling', '.yarn',
    '.local', '.config', '.cache', '.mozilla', # Common hidden user config/data directories
    'Library', # macOS
    'AppData', # Windows
    '$RECYCLE.BIN', # Windows
    'System Volume Information', # Windows
    'Program Files', 'Program Files (x86)', 'ProgramData', # Windows
    'bin', 'sbin', 'lib', 'usr', 'opt', 'dev', 'sys', 'proc', 'run', 'mnt', 'srv', # Linux/Unix system directories
    'var', 'tmp', 'boot', 'etc', 'media'
}

# Define a set of specific file names that should *always* be excluded.
ALWAYS_EXCLUDED_FILE_NAMES = {
    '.bash_history', '.zsh_history', '.profile', '.bashrc', '.zshrc', '.vimrc',
    '.gitconfig', '.tmux.conf', '.selected_editor', '.lesshst', '.wget-hsts',
    '.Xauthority', '.ICEauthority', '.rnd', '.sqlite_history', '.mysql_history',
    '.psql_history', '.rediscli_history', '.mongosh_history', '.Xresources',
    '.bash_profile', '.bash_logout', '.inputrc', '.DS_Store', # macOS metadata
    'thumbs.db' # Windows thumbnails
}

def get_home_directory_files(include_hidden: bool = False) -> List[Path]:
    """
    Recursively gets all files and directories within the user's home directory.
    This version **always excludes** hidden folders and files (those starting with '.')
    and other specific system/library folders.
    The `include_hidden` parameter is effectively ignored in this version,
    as all hidden items are permanently excluded.

    Returns:
        List[Path]: A list of Path objects representing files and directories.
    """
    home_dir = Path.home()
    all_paths: List[Path] = []
    
    # Add home_dir itself if it's not in the ALWAYS_EXCLUDED_DIR_NAMES
    if home_dir.name not in ALWAYS_EXCLUDED_DIR_NAMES:
        all_paths.append(home_dir)

    for root, dirs, files in os.walk(home_dir, followlinks=False):
        current_path = Path(root)

        # Skip adding the current root if it's an always excluded directory (and not home_dir itself)
        if current_path != home_dir and current_path.name in ALWAYS_EXCLUDED_DIR_NAMES:
            continue
        
        # Filter 'dirs' in-place for os.walk to avoid traversing unwanted subdirectories.
        # This is the most efficient way to exclude large trees.
        # Directories starting with '.' are now explicitly excluded here.
        dirs[:] = [
            d_name for d_name in dirs
            if d_name not in ALWAYS_EXCLUDED_DIR_NAMES and not d_name.startswith('.')
        ]

        # Process files and directories in the current `root` (after `dirs` has been filtered)
        for entry_name in files + dirs: # Iterate over both files and the now filtered directories
            entry_path = current_path / entry_name

            # Apply general exclusion rules: always exclude names in predefined sets
            if entry_path.name in ALWAYS_EXCLUDED_DIR_NAMES or \
               entry_path.name in ALWAYS_EXCLUDED_FILE_NAMES:
                continue
            
            # Now, explicitly exclude any file or directory whose name starts with '.'
            # (unless it's the home directory itself, which might be named something like `~/.config`)
            if entry_path.name.startswith('.') and entry_path != home_dir:
                continue
            
            # Add to list if it exists and is a file or a directory
            if entry_path.exists():
                all_paths.append(entry_path)
            
    return all_paths


def fuzzy_match_score(query: str, text: str) -> float:
    """
    Calculates a basic fuzzy match score between a query and a text.
    Scores higher for:
    - Exact matches
    - Substring matches
    - Characters in order
    - Matches at the beginning of words/path components
    """
    query = query.lower()
    text = text.lower()

    if not query:
        return 1.0 # Empty query matches everything perfectly

    # Exact match bonus
    if query == text:
        return 2.0

    # Substring match bonus
    if query in text:
        # Give a bonus proportional to the length of the matched substring
        # relative to the text length. Longer substrings in smaller texts are better.
        return 1.5 + (len(query) / len(text)) 

    score = 0.0
    query_index = 0
    last_match_index = -1
    
    # Character matching in order (not necessarily contiguous)
    for i, char_text in enumerate(text):
        if query_index < len(query) and char_text == query[query_index]:
            score += 1.0 # Base score for matching character
            
            # Bonus for consecutive matches
            if last_match_index != -1 and i == last_match_index + 1:
                score += 0.5 
            
            # Bonus for matching at the start of a path component (after / or \)
            if i == 0 or text[i-1] in ('/', '\\'):
                score += 0.75

            query_index += 1
            last_match_index = i

    # Penalize if not all query characters were found
    if query_index < len(query):
        score -= (len(query) - query_index) * 0.5

    # Normalize score by length of query and text to favor shorter, more precise matches
    # Add a small epsilon to prevent division by zero for extremely short texts.
    score = score / (len(query) + len(text) * 0.1 + 1e-6)

    return max(0.0, score) # Ensure score is not negative

def fuzzy_search(query: str, items: List[Path], limit: int = 10) -> List[Path]:
    """
    Performs a fuzzy search on a list of Path objects and returns the top N matches.
    """
    if not query:
        # If query is empty, return an empty list.
        return [] 

    scored_results: List[Tuple[float, Path]] = []
    
    for item_path in items:
        # Use the string representation of the path for scoring
        score = fuzzy_match_score(query, str(item_path))
        if score > 0: # Only add if there's any match
            scored_results.append((score, item_path))

    # Sort by score in descending order
    scored_results.sort(key=lambda x: x[0], reverse=True)

    # Return only the Path objects, limited to the top N
    return [path for score, path in scored_results[:limit]]