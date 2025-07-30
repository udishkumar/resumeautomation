#!/usr/bin/env python3
"""
Helper script to encrypt your Claude API key for config.ini
Run this to generate the encrypted key to put in your config file
"""

import base64
import configparser
import os
import getpass

def encrypt_api_key(api_key):
    """Encrypt API key using base64"""
    return base64.b64encode(api_key.encode()).decode('utf-8')

def create_config_file(encrypted_key):
    """Create or update config.ini with encrypted API key"""
    config = configparser.ConfigParser()
    
    # Read existing config if it exists
    if os.path.exists('config.ini'):
        config.read('config.ini')
        print("Updating existing config.ini...")
    else:
        print("Creating new config.ini...")
    
    # Set the encrypted key
    if 'API' not in config:
        config['API'] = {}
    
    config['API']['key'] = encrypted_key
    
    # Write to file
    with open('config.ini', 'w') as f:
        config.write(f)
    
    print("✓ config.ini has been created/updated successfully!")

def main():
    print("=" * 50)
    print("Claude API Key Encryption Tool")
    print("=" * 50)
    print()
    print("This tool will encrypt your API key and save it to config.ini")
    print("Your actual API key will not be stored in plain text.")
    print()
    
    # Get API key securely (hidden input)
    api_key = getpass.getpass("Enter your Claude API key (input hidden): ").strip()
    
    if not api_key:
        print("Error: No API key provided")
        return
    
    # Validate key format (basic check)
    if not api_key.startswith('sk-'):
        print("Warning: API key should start with 'sk-'")
        confirm = input("Continue anyway? (y/n): ").lower()
        if confirm != 'y':
            return
    
    # Encrypt the key
    encrypted_key = encrypt_api_key(api_key)
    
    print()
    print("Encrypted key (base64):")
    print("-" * 50)
    print(encrypted_key)
    print("-" * 50)
    
    # Ask if user wants to create config file
    print()
    create_file = input("Create/update config.ini with this encrypted key? (y/n): ").lower()
    
    if create_file == 'y':
        create_config_file(encrypted_key)
        print()
        print("You can now run the resume automation tool without entering your API key!")
    else:
        print()
        print("To manually add to config.ini, create a file with:")
        print("[API]")
        print(f"key = {encrypted_key}")

if __name__ == "__main__":
    main()