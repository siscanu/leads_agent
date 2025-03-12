import json
from typing import Any
from colorama import Fore, Style, init # type: ignore

# Initialize colorama
init()

def log_json(data: Any, title: str = None):
    """Simple JSON logger with basic formatting using colorama"""
    if title:
        print(f"{Style.BRIGHT}{Fore.BLUE}{title}{Style.RESET_ALL}")
    
    if isinstance(data, bytes):
        try:
            data = json.loads(data.decode('utf-8'))
        except:
            print(data)
            return
            
    try:
        formatted = json.dumps(data, indent=2)
        print(f"{Fore.GREEN}{formatted}{Style.RESET_ALL}")
    except:
        print(data)
