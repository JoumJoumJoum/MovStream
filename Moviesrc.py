
#!/usr/bin/env python3
import requests
import sys
import time
import threading
import json
import os
import webbrowser
from datetime import datetime
import platform
import socket

API_KEY = '15eb0bb0'

# ANSI color codes
COLOR_BLUE = '\033[34m'
COLOR_GREEN = '\033[32m'
COLOR_CYAN = '\033[36m'
COLOR_RED = '\033[31m'
COLOR_YELLOW = '\033[33m'
COLOR_RESET = '\033[0m'



print("\033[33m" +r'''
      
      
                          $$\               $$\                                   
                         $$  |             $$  |                                  
      $$\  $$$$$$\      $$  /$$$$$$\      $$  /$$$$$$\$$$$\   $$$$$$\ $$\    $$\  
      \__|$$  __$$\    $$  /$$  __$$\    $$  / $$  _$$  _$$\ $$  __$$\\$$\  $$  | 
      $$\ $$ /  $$ |  $$  / $$ /  $$ |  $$  /  $$ / $$ / $$ |$$ /  $$ |\$$\$$  /  
      $$ |$$ |  $$ | $$  /  $$ |  $$ | $$  /   $$ | $$ | $$ |$$ |  $$ | \$$$  /   
      $$ |\$$$$$$  |$$  /   \$$$$$$  |$$  /    $$ | $$ | $$ |\$$$$$$  |  \$  /$$\ 
      $$ | \______/ \__/     \______/ \__/     \__| \__| \__| \______/    \_/ \__|
$$\   $$ |                                                                        
\$$$$$$  |                                                                        
 \______/
      

'''+'\033[0m')

original_getaddrinfo = socket.getaddrinfo
def force_ipv4_getaddrinfo(*args, **kwargs):
    """Filter getaddrinfo results to return only IPv4 addresses."""
    results = original_getaddrinfo(*args, **kwargs)
    return [r for r in results if r[0] == socket.AF_INET]
socket.getaddrinfo = force_ipv4_getaddrinfo


def loading_animation(stop_event, message="Loading"):
    """Display a simple spinner animation until stop_event is set."""
    spinner = ['[-]', '[\\]', '[|]', '[/]']
    while not stop_event.is_set():
        for symbol in spinner:
            print(f'\r{message} {symbol}', end='', flush=True)
            time.sleep(0.2)
    print(f'\r{" " * (len(message) + 5)}', end='', flush=True)  # Clear the line

def load_history():
    """Load the last 5 watched items from history.json."""
    history_file = os.path.join(os.path.dirname(__file__), 'history.json')
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_history(entry):
    """Save a new entry to history, keeping only the last 5."""
    history_file = os.path.join(os.path.dirname(__file__), 'history.json')
    history = load_history()
    history.append(entry)
    history = history[-5:]  # Keep only the last 5 entries
    try:
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    except IOError:
        print(f"{COLOR_RED}Error: Could not save history.{COLOR_RESET}")

def display_history():
    """Display the watch history."""
    history = load_history()
    if history:
        print(f"\n{COLOR_BLUE}=========================== Watch History ==========================={COLOR_RESET}")
        for i, entry in enumerate(history, 1):
            title = entry['title']
            if entry['type'] == 'series' and 'season' in entry and 'episode' in entry:
                try:
                    season = int(entry['season'])
                    episode = int(entry['episode'])
                    title += f" S{season:02d}E{episode:02d} - {entry.get('episode_title', '')}"
                except (ValueError, TypeError):
                    title += " (Invalid season/episode)"
            if 'ds_lang' in entry:
                title += f" (lang: {entry['ds_lang']})"
            print(f"{COLOR_GREEN}H{i}. {title} ({entry['type']}) - {entry['timestamp']}{COLOR_RESET}")
        print()

def open_stream_link(url, title):
    """Open the streaming link with the default application and return the URL."""
    print(f"\n{COLOR_GREEN}Stream link for '{title}': {url}{COLOR_RESET}")
    try:
        webbrowser.open(url)
        print(f"{COLOR_CYAN}Opening '{title}' in your default application...{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}Error opening link: {e}. Please open the URL manually.{COLOR_RESET}")
    return url

def fetch_search_results(query):
    if not query.strip():
        return {'Response': 'False', 'Error': 'Search query cannot be empty.'}
    url = f'http://www.omdbapi.com/?apikey={API_KEY}&s={query}'
    stop_event = threading.Event()
    loading_thread = threading.Thread(target=loading_animation, args=(stop_event, "Searching"))
    loading_thread.start()
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        stop_event.set()
        loading_thread.join()
        return response.json()
    except requests.exceptions.RequestException as e:
        stop_event.set()
        loading_thread.join()
        return {'Response': 'False', 'Error': f'API request failed: {e}'}

def fetch_description(imdb_id):
    url = f'http://www.omdbapi.com/?apikey={API_KEY}&i={imdb_id}&plot=full'
    stop_event = threading.Event()
    loading_thread = threading.Thread(target=loading_animation, args=(stop_event, "Fetching description"))
    loading_thread.start()
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        stop_event.set()
        loading_thread.join()
        return response.json()
    except requests.exceptions.RequestException as e:
        stop_event.set()
        loading_thread.join()
        return {'Response': 'False', 'Error': f'Failed to fetch description: {e}'}

def fetch_season_episodes(imdb_id, season):
    url = f'http://www.omdbapi.com/?apikey={API_KEY}&i={imdb_id}&Season={season}'
    stop_event = threading.Event()
    loading_thread = threading.Thread(target=loading_animation, args=(stop_event, "Fetching episodes"))
    loading_thread.start()
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        stop_event.set()
        loading_thread.join()
        return response.json()
    except requests.exceptions.RequestException as e:
        stop_event.set()
        loading_thread.join()
        return {'Response': 'False', 'Error': f'Failed to fetch season data: {e}'}

def display_help():
    print(f"\n{COLOR_CYAN}Available commands:{COLOR_RESET}")
    print(f"  {COLOR_CYAN}<number>{COLOR_RESET}         : Get stream link for a movie or show series URL (series starts at S1E1)")
    print(f"  {COLOR_CYAN}desc <number>{COLOR_RESET}    : Show description for the selected title")
    print(f"  {COLOR_CYAN}episodes <number>{COLOR_RESET}: Show episodes for the selected series")
    print(f"  {COLOR_CYAN}lang <number> <code>{COLOR_RESET}: Get stream link with subtitle language (e.g., en, de)")
    print(f"  {COLOR_CYAN}h <number>{COLOR_RESET}       : Select a title from watch history")
    print(f"  {COLOR_CYAN}help{COLOR_RESET}             : Show this help menu")
    print(f"  {COLOR_CYAN}exit{COLOR_RESET}             : Quit the program")

def is_valid_language_code(code):
    """Check if the language code is a valid 2-letter ISO 639-1 code."""
    return len(code) == 2 and code.isalpha()

def main():
    # Display watch history at startup
    display_history()
    
    search_query = input(f"\n{COLOR_CYAN}What would you like to Watch? {COLOR_RESET}").strip()
    data = fetch_search_results(search_query)

    results = []
    if data.get('Response') == 'True':
        index = 1
        movies = []
        series = []
        others = []

        for item in data['Search']:
            entry = {
                'index': index,
                'title': item['Title'],
                'year': item['Year'],
                'imdbID': item['imdbID'],
                'type': item['Type']
            }
            results.append(entry)

            if item['Type'] == 'movie':
                movies.append(entry)
            elif item['Type'] == 'series':
                series.append(entry)
            else:
                others.append(entry)
            index += 1

        if movies:
            print(f"\n{COLOR_BLUE}=========================== Movies ==========================={COLOR_RESET}")
            for m in movies:
                print(f"{COLOR_GREEN}{m['index']}. {m['title']} ({m['year']}) - IMDb ID: {m['imdbID']}{COLOR_RESET}")

        if series:
            print(f"\n{COLOR_BLUE}=========================== Series ==========================={COLOR_RESET}")
            for s in series:
                print(f"{COLOR_GREEN}{s['index']}. {s['title']} ({s['year']}) - IMDb ID: {s['imdbID']}{COLOR_RESET}")

        if others:
            print(f"\n{COLOR_BLUE}=========================== Others ==========================={COLOR_RESET}")
            for o in others:
                print(f"{COLOR_GREEN}{o['index']}. {o['title']} ({o['year']}) - IMDb ID: {o['imdbID']}{COLOR_RESET}")

        while True:
            command = input(f"\n{COLOR_CYAN}Enter a number to get a stream link, 'desc [number]' for description, 'episodes [number]', 'lang [number] [code]', 'h [number]' for history, 'help', or 'exit': {COLOR_RESET}").strip().lower()

            if command == 'exit':
                print(f"{COLOR_CYAN}Exiting.{COLOR_RESET}")
                break

            elif command == 'help':
                display_help()

            elif command.startswith('h '):
                parts = command.split()
                if len(parts) == 2 and parts[1].isdigit():
                    num = int(parts[1])
                    history = load_history()
                    if 1 <= num <= len(history):
                        selected = history[num - 1]
                        title = selected['title'] + (f" S{int(selected.get('season', '1')):02d}E{int(selected.get('episode', '1')):02d} - {selected.get('episode_title', '')}" if selected['type'] == 'series' and 'season' in selected else "")
                        if 'ds_lang' in selected:
                            title += f" (lang: {selected['ds_lang']})"
                        if selected['type'] == 'series' and 'season' not in selected:
                            stream_url = selected['stream_url']
                            print(f"\n{COLOR_GREEN}Stream link for '{title}': {stream_url}{COLOR_RESET}")
                            print(f"Use 'episodes {num}' to select a specific season and episode.")
                        else:
                            open_stream_link(selected['stream_url'], title)
                    else:
                        print(f"{COLOR_RED}Invalid history number.{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Invalid command format. Use: h [number]{COLOR_RESET}")

            elif command.startswith('desc '):
                parts = command.split()
                if len(parts) == 2 and parts[1].isdigit():
                    num = int(parts[1])
                    selected = next((item for item in results if item['index'] == num), None)
                    if selected:
                        desc_data = fetch_description(selected['imdbID'])
                        if desc_data.get('Response') == 'True':
                            print(f"\n{COLOR_GREEN}Description for '{selected['title']}':{COLOR_RESET}\n{desc_data.get('Plot', 'No description available.')}")
                        else:
                            print(f"{COLOR_RED}Error: {desc_data.get('Error', 'Could not fetch description.')}{COLOR_RESET}")
                    else:
                        print(f"{COLOR_RED}Invalid number.{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Invalid command format. Use: desc [number]{COLOR_RESET}")

            elif command.startswith('lang '):
                parts = command.split()
                if len(parts) == 3 and parts[1].isdigit() and is_valid_language_code(parts[2]):
                    num = int(parts[1])
                    lang_code = parts[2].lower()
                    selected = next((item for item in results if item['index'] == num), None)
                    if selected:
                        if selected['type'] == 'movie':
                            stream_url = f"https://vidsrc.xyz/embed/movie/{selected['imdbID']}?ds_lang={lang_code}"
                            title = selected['title'] + f" (lang: {lang_code})"
                            open_stream_link(stream_url, title)
                            # Save to history
                            save_history({
                                'title': selected['title'],
                                'type': selected['type'],
                                'imdbID': selected['imdbID'],
                                'stream_url': stream_url,
                                'ds_lang': lang_code,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                        else:
                            stream_url = f"https://vidsrc.xyz/embed/tv/{selected['imdbID']}?ds_lang={lang_code}"
                            title = f"{selected['title']} (starts at S1E1, lang: {lang_code})"
                            print(f"\n{COLOR_GREEN}Stream link for '{title}': {stream_url}{COLOR_RESET}")
                            print(f"Use 'episodes {num}' to select a specific season and episode with language.")
                            # Save to history
                            save_history({
                                'title': selected['title'],
                                'type': selected['type'],
                                'imdbID': selected['imdbID'],
                                'stream_url': stream_url,
                                'ds_lang': lang_code,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                    else:
                        print(f"{COLOR_RED}Invalid number.{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Invalid command format. Use: lang [number] [code] (e.g., lang 1 en){COLOR_RESET}")

            elif command.startswith('episodes '):
                parts = command.split()
                if len(parts) == 2 and parts[1].isdigit():
                    num = int(parts[1])
                    selected = next((item for item in results if item['index'] == num), None)
                    if selected and selected['type'] == 'series':
                        series_data = fetch_description(selected['imdbID'])
                        if series_data.get('Response') == 'True':
                            total_seasons = int(series_data.get('totalSeasons', 0))
                            if total_seasons == 0:
                                print(f"{COLOR_RED}Error: Could not retrieve season information.{COLOR_RESET}")
                                continue
                            print(f"\n{COLOR_GREEN}'{selected['title']}' has {total_seasons} season(s).{COLOR_RESET}")
                            season_input = input(f"\n{COLOR_CYAN}Enter season number (1-{total_seasons}), or 'back' to return: {COLOR_RESET}").strip().lower()
                            if season_input == 'back':
                                continue
                            if season_input.isdigit() and 1 <= int(season_input) <= total_seasons:
                                season = int(season_input)
                                episode_data = fetch_season_episodes(selected['imdbID'], season)
                                if episode_data.get('Response') == 'True':
                                    episodes = episode_data.get('Episodes', [])
                                    if episodes:
                                        print(f"\n{COLOR_BLUE}=========================== Episodes for '{selected['title']}' Season {season} ==========================={COLOR_RESET}")
                                        for ep in episodes:
                                            print(f"{COLOR_GREEN}{ep['Episode']}. {ep['Title']} ({ep['Released']}) - IMDb ID: {ep['imdbID']}{COLOR_RESET}")
                                        ep_input = input(f"\n{COLOR_CYAN}Enter episode number to get stream link, or 'back' to return: {COLOR_RESET}").strip().lower()
                                        if ep_input == 'back':
                                            continue
                                        if ep_input.isdigit() and 1 <= int(ep_input) <= len(episodes):
                                            episode = episodes[int(ep_input) - 1]
                                            lang_input = input(f"\n{COLOR_CYAN}Enter subtitle language code (e.g., en, de) or press Enter for default: {COLOR_RESET}").strip().lower()
                                            stream_url = f"https://vidsrc.xyz/embed/tv/{selected['imdbID']}/{season}-{ep_input}"
                                            title = f"{selected['title']} S{season:02d}E{int(ep_input):02d} - {episode['Title']}"
                                            history_entry = {
                                                'title': selected['title'],
                                                'type': selected['type'],
                                                'imdbID': selected['imdbID'],
                                                'stream_url': stream_url,
                                                'season': int(season),  # Store as integer
                                                'episode': int(ep_input),  # Store as integer
                                                'episode_title': episode['Title'],
                                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            }
                                            if lang_input and is_valid_language_code(lang_input):
                                                stream_url += f"?ds_lang={lang_input}"
                                                title += f" (lang: {lang_input})"
                                                history_entry['ds_lang'] = lang_input
                                            open_stream_link(stream_url, title)
                                            # Save to history
                                            save_history(history_entry)
                                        else:
                                            print(f"{COLOR_RED}Invalid episode number.{COLOR_RESET}")
                                    else:
                                        print(f"{COLOR_RED}No episodes found for this season.{COLOR_RESET}")
                                else:
                                    print(f"{COLOR_RED}Error: {episode_data.get('Error', 'Could not fetch episodes.')}{COLOR_RESET}")
                            else:
                                print(f"{COLOR_RED}Invalid season number. Must be between 1 and {total_seasons}.{COLOR_RESET}")
                        else:
                            print(f"{COLOR_RED}Error: {series_data.get('Error', 'Could not fetch series details.')}{COLOR_RESET}")
                    else:
                        print(f"{COLOR_RED}Invalid number or not a series.{COLOR_RESET}")
                else:
                    print(f"{COLOR_RED}Invalid command format. Use: episodes [number]{COLOR_RESET}")

            elif command.isdigit():
                num = int(command)
                selected = next((item for item in results if item['index'] == num), None)
                if selected:
                    if selected['type'] == 'movie':
                        stream_url = f"https://vidsrc.xyz/embed/movie/{selected['imdbID']}"
                        open_stream_link(stream_url, selected['title'])
                        # Save to history
                        save_history({
                            'title': selected['title'],
                            'type': selected['type'],
                            'imdbID': selected['imdbID'],
                            'stream_url': stream_url,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                    else:
                        stream_url = f"https://vidsrc.xyz/embed/tv/{selected['imdbID']}"
                        print(f"\n{COLOR_GREEN}Stream link for '{selected['title']} (starts at S1E1)': {stream_url}{COLOR_RESET}")
                        print(f"Use 'episodes {num}' to select a specific season and episode.")
                        # Save to history
                        save_history({
                            'title': selected['title'],
                            'type': selected['type'],
                            'imdbID': selected['imdbID'],
                            'stream_url': stream_url,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                else:
                    print(f"{COLOR_RED}Invalid number.{COLOR_RESET}")
            else:
                print(f"{COLOR_RED}Unknown command. Type 'help' for available commands.{COLOR_RESET}")

    else:
        print(f"\n{COLOR_RED}Error: {data.get('Error', 'Unknown error occurred.')}{COLOR_RESET}")

if __name__ == "__main__":
    main()