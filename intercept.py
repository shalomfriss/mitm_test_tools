from mitmproxy import http
import json
import re
import hashlib
from pathlib import Path
import sys
import subprocess
import atexit

##############################################
# PROXY SETUP
##############################################
def set_proxy(host, port):
    subprocess.run(['networksetup', '-setwebproxy', 'Wi-Fi', host, port])
    subprocess.run(['networksetup', '-setsecurewebproxy', 'Wi-Fi', host, port])
    print(f"Proxy set to {host}:{port}")

def unset_proxy():
    subprocess.run(['networksetup', '-setwebproxystate', 'Wi-Fi', 'off'])
    subprocess.run(['networksetup', '-setsecurewebproxystate', 'Wi-Fi', 'off'])
    print("Proxy settings removed")

# Set proxy on startup
set_proxy('127.0.0.1', '8080')

# Register function to be called on script exit
def cleanup():
    unset_proxy()

atexit.register(cleanup)

##############################################
# FILE CACHE
##############################################
saved_file_dir = '__files'
domain_file_name = 'domains.txt'

def response(flow: http.HTTPFlow) -> None:

    # Read domains from file
    with open(domain_file_name, 'r') as f:
        domains = [line.strip() for line in f]
    
    # Create a pattern to match any of the domains in domains.txt
    domain_pattern = r'^(?:[\w-]+\.)*(?:' + '|'.join(re.escape(domain) for domain in domains) + ')$'
    
    if re.match(domain_pattern, flow.request.host, re.IGNORECASE):

        # Generate a filename based on the whole domain and path
        full_url = f"{flow.request.host}{flow.request.path}"
        safe_filename = "".join([c if c.isalnum() else "_" for c in full_url]).rstrip("_")
        
        # Hash the full URL to create a deterministic filename
        hashed_filename = hashlib.sha256(full_url.encode()).hexdigest()
        safe_filename = hashed_filename[:32]  # Use first 32 characters of the hash
        filename = f"{saved_file_dir}/{safe_filename}.txt"
        
        # Check if the file already exists
        file_path = Path(filename)
        if file_path.exists():
            # Read the existing file contents
            with open(file_path, "r", encoding="utf-8") as existing_file:
                existing_content = existing_file.read()
            
            # Set the response content to the existing file contents
            flow.response.text = existing_content
            flow.response.headers["Content-Type"] = "text/plain"
            # print(f"File {filename} already exists. Skipping save.")
            return
        
        # Save the response content to the file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(flow.response.text)
            # print(f"Saved response to: {filename}")
        
