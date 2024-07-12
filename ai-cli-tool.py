import argparse
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

import openai
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load configuration
config_path = Path.home() / '.aicli_config.json'
if config_path.exists():
    with open(config_path, 'r') as f:
        config = json.load(f)
else:
    config = {
        'api_key': '',
        'model': 'gpt-3.5-turbo',
        'max_tokens': 150,
        'temperature': 0.7
    }

# Set up OpenAI API
openai.api_key = config['api_key']

# Rich console for pretty output
console = Console()

# Custom prompt style
style = Style.from_dict({
    'prompt': '#ansibrightcyan bold',
})

# Command completer
command_completer = WordCompleter(['help', 'exit', 'settings', 'clear', 'save', 'load'])

def get_ai_response(prompt: str) -> str:
    """Get response from OpenAI API."""
    try:
        response = openai.ChatCompletion.create(
            model=config['model'],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=config['max_tokens'],
            temperature=config['temperature']
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error in AI response: {e}")
        return "Sorry, I encountered an error. Please try again."

def display_help():
    """Display help information."""
    help_text = """
    Available commands:
    - help: Display this help message
    - exit: Exit the program
    - settings: Modify tool settings
    - clear: Clear the screen
    - save <filename>: Save the conversation
    - load <filename>: Load a saved conversation
    
    For any other input, I'll try to assist you using AI!
    """
    console.print(Panel(Markdown(help_text), title="Help", expand=False))

def modify_settings():
    """Modify tool settings."""
    global config
    console.print("Current settings:")
    for key, value in config.items():
        console.print(f"{key}: {value}")
    
    key_to_modify = console.input("Enter the key to modify (or 'done' to finish): ")
    while key_to_modify != 'done':
        if key_to_modify in config:
            new_value = console.input(f"Enter new value for {key_to_modify}: ")
            config[key_to_modify] = new_value
        else:
            console.print(f"Invalid key: {key_to_modify}")
        key_to_modify = console.input("Enter the key to modify (or 'done' to finish): ")
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    console.print("Settings updated and saved.")

def save_conversation(filename: str, conversation: list):
    """Save the conversation to a file."""
    with open(filename, 'w') as f:
        json.dump(conversation, f, indent=2)
    console.print(f"Conversation saved to {filename}")

def load_conversation(filename: str) -> list:
    """Load a conversation from a file."""
    try:
        with open(filename, 'r') as f:
            conversation = json.load(f)
        console.print(f"Conversation loaded from {filename}")
        return conversation
    except FileNotFoundError:
        console.print(f"File {filename} not found.")
        return []

def main():
    parser = argparse.ArgumentParser(description="AI-powered CLI tool")
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    console.print(Panel("Welcome to the AI-powered CLI tool!", title="AI CLI", expand=False))
    console.print("Type 'help' for available commands or start chatting!")

    session = PromptSession(completer=command_completer, style=style)
    conversation = []

    while True:
        try:
            user_input = session.prompt("AI CLI > ", style=style)
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

        if user_input.lower() == 'exit':
            break
        elif user_input.lower() == 'help':
            display_help()
        elif user_input.lower() == 'settings':
            modify_settings()
        elif user_input.lower() == 'clear':
            os.system('cls' if os.name == 'nt' else 'clear')
        elif user_input.lower().startswith('save '):
            filename = user_input.split(maxsplit=1)[1]
            save_conversation(filename, conversation)
        elif user_input.lower().startswith('load '):
            filename = user_input.split(maxsplit=1)[1]
            conversation = load_conversation(filename)
        else:
            response = get_ai_response(user_input)
            conversation.append({"user": user_input, "ai": response})
            console.print(Syntax(response, "markdown", theme="monokai", line_numbers=True))

    console.print("Thank you for using the AI CLI tool. Goodbye!")

if __name__ == "__main__":
    main()
