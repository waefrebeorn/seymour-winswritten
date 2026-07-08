#!/usr/bin/env python3
"""
write_large_file — Write large files without tool timeout.
Usage: python3 write_large_file.py <path> < content.txt
       python3 write_large_file.py <path> "content string"
       echo "content" | python3 write_large_file.py <path> -
"""
import sys
import os

def write_file(path, content):
    """Write content to file, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    print(f"[write] {path} ({len(content)} bytes)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 write_large_file.py <path> <content|->")
        sys.exit(1)
    
    path = sys.argv[1]
    source = sys.argv[2]
    
    if source == "-":
        content = sys.stdin.read()
    else:
        content = source
    
    write_file(path, content)
