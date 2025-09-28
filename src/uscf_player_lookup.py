#!/usr/bin/env python3
"""
USCF Player Data Lookup Tool

This script searches for and retrieves player data from the US Chess Federation website.
It can find player information including ratings, membership status, and tournament history.
"""

import requests
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin, quote
import time
from bs4 import BeautifulSoup


@dataclass
class PlayerInfo:
    """Data class to hold player information from USCF"""
    name: str
    uscf_id: Optional[str] = None
    current_rating: Optional[int] = None
    peak_rating: Optional[int] = None
    state: Optional[str] = None
    expiration_date: Optional[str] = None
    membership_status: Optional[str] = None
    tournament_history: Optional[List[Dict]] = None
    rating_history: Optional[List[Dict]] = None


class USCFPlayerLookup:
    """
    A class to search for and retrieve player data from the USCF website
    """

    def __init__(self):
        self.base_url = "http://www.uschess.org"
        self.search_url = "http://www.uschess.org/datapage/player-search.php"
        self.player_detail_url = "http://www.uschess.org/msa/MbrDtlMain.php"
        self.session = requests.Session()
        # Set a reasonable user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def search_player_by_name(self, first_name: str, last_name: str, state: str = None) -> List[PlayerInfo]:
        """
        Search for players by first and last name

        Args:
            first_name: Player's first name
            last_name: Player's last name
            state: Optional state filter (e.g., 'CA', 'NY')

        Returns:
            List of PlayerInfo objects matching the search
        """
        try:
            # Format name for USCF search (they prefer "Last, First" format)
            name_query = f"{last_name}, {first_name}"

            # Prepare search parameters for legacy USCF system
            params = {
                'name': name_query
            }

            if state:
                params['state'] = state

            response = self.session.get(self.search_url, params=params)
            response.raise_for_status()

            # Parse the response and extract player data
            return self._parse_search_results(response.text)

        except requests.RequestException as e:
            print(f"Error searching for player: {e}")
            return []

    def search_player_by_id(self, uscf_id: str) -> Optional[PlayerInfo]:
        """
        Search for a player by their USCF ID

        Args:
            uscf_id: The player's USCF ID number

        Returns:
            PlayerInfo object if found, None otherwise
        """
        try:
            # Use the legacy USCF member detail page
            url = f"{self.player_detail_url}?{uscf_id}"

            response = self.session.get(url)
            response.raise_for_status()

            return self._parse_player_details(response.text, uscf_id)

        except requests.RequestException as e:
            print(f"Error looking up player by ID: {e}")
            return None

    def get_player_rating_history(self, uscf_id: str) -> List[Dict]:
        """
        Get rating history for a player

        Args:
            uscf_id: The player's USCF ID

        Returns:
            List of rating history entries
        """
        try:
            rating_url = f"{self.base_url}/player/{uscf_id}/ratings"
            response = self.session.get(rating_url)

            if response.status_code == 200:
                return self._parse_rating_history(response.text)
            return []

        except requests.RequestException as e:
            print(f"Error getting rating history: {e}")
            return []

    def get_player_tournament_history(self, uscf_id: str) -> List[Dict]:
        """
        Get tournament history for a player

        Args:
            uscf_id: The player's USCF ID

        Returns:
            List of tournament entries
        """
        try:
            tournament_url = f"{self.base_url}/player/{uscf_id}/tournaments"
            response = self.session.get(tournament_url)

            if response.status_code == 200:
                return self._parse_tournament_history(response.text)
            return []

        except requests.RequestException as e:
            print(f"Error getting tournament history: {e}")
            return []

    def _parse_search_results(self, html_content: str) -> List[PlayerInfo]:
        """Parse HTML search results and extract player information"""
        players = []
        soup = BeautifulSoup(html_content, 'html.parser')

        # Look for the results table in USCF search results
        # The search results are typically in a table with specific structure

        # Find all tables and look for the one containing player data
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            # Skip header row, look for data rows
            for row in rows[1:]:  # Skip header
                cells = row.find_all(['td', 'th'])

                if len(cells) >= 4:  # Ensure we have enough data
                    try:
                        # USCF search results typically have: ID, Name, Rating, State, etc.
                        player_data = {}

                        for i, cell in enumerate(cells):
                            cell_text = cell.get_text(strip=True)

                            # Parse USCF ID (usually first column or a link)
                            if i == 0 or cell.find('a'):
                                # Look for USCF ID number
                                id_match = re.search(r'\d{8,}', cell_text)
                                if id_match:
                                    player_data['uscf_id'] = id_match.group()

                                # If there's a link, extract href for ID
                                link = cell.find('a')
                                if link and 'href' in link.attrs:
                                    href = link['href']
                                    id_in_href = re.search(r'(\d{8,})', href)
                                    if id_in_href:
                                        player_data['uscf_id'] = id_in_href.group(1)

                            # Look for name (usually contains comma or capitalized words)
                            if ',' in cell_text or (cell_text and cell_text[0].isupper()):
                                if len(cell_text) > 3 and not cell_text.isdigit():
                                    player_data['name'] = cell_text

                            # Look for regular rating (3-4 digit number)
                            # Skip if this is in a quick/blitz column
                            if re.match(r'^\d{3,4}$', cell_text):
                                # Check context to prefer regular rating
                                context = ""
                                if i > 0:
                                    context += cells[i-1].get_text(strip=True).lower()
                                if i < len(cells) - 1:
                                    context += cells[i+1].get_text(strip=True).lower()

                                # Prefer regular rating over quick/blitz
                                if 'regular' in context or ('quick' not in context and 'blitz' not in context):
                                    if 'rating' not in player_data or 'regular' in context:
                                        player_data['rating'] = int(cell_text)

                            # Look for state (2 letter code)
                            if re.match(r'^[A-Z]{2}$', cell_text):
                                player_data['state'] = cell_text

                            # Look for expiration date
                            if re.match(r'\d{2}/\d{2}/\d{4}', cell_text):
                                player_data['expiration'] = cell_text

                        # Create player object if we have at least a name and it's valid
                        if 'name' in player_data and player_data['name'] not in ['Name', 'MSA Home Page']:
                            player = PlayerInfo(
                                name=player_data['name'],
                                uscf_id=player_data.get('uscf_id'),
                                current_rating=player_data.get('rating'),
                                state=player_data.get('state'),
                                expiration_date=player_data.get('expiration')
                            )
                            players.append(player)

                    except (ValueError, IndexError):
                        continue

        # Remove duplicates based on USCF ID
        seen_ids = set()
        unique_players = []
        for player in players:
            if player.uscf_id and player.uscf_id not in seen_ids:
                unique_players.append(player)
                seen_ids.add(player.uscf_id)
            elif not player.uscf_id:
                unique_players.append(player)

        return unique_players

    def _parse_player_details(self, html_content: str, uscf_id: str) -> Optional[PlayerInfo]:
        """Parse detailed player page and extract all available information"""
        soup = BeautifulSoup(html_content, 'html.parser')

        player_info = PlayerInfo(name="", uscf_id=uscf_id)

        # Look for player name in various locations
        # Try title first
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            # Extract name from title like "John Smith - USCF"
            name_match = re.search(r'^([^-]+)', title_text.strip())
            if name_match:
                player_info.name = name_match.group(1).strip()

        # Look for name in table cells or divs
        if not player_info.name:
            # Look for patterns like "Name: John Smith"
            for text in soup.stripped_strings:
                if 'name' in text.lower() and ':' in text:
                    name_part = text.split(':')[-1].strip()
                    if len(name_part) > 2:
                        player_info.name = name_part
                        break

        # Look for ratings in tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)

                    # Look for ratings (3-4 digit numbers)
                    if re.match(r'^\d{3,4}$', text):
                        # Check if this is likely a rating (previous or next cell mentions rating)
                        context = ""
                        if i > 0:
                            context += cells[i-1].get_text(strip=True).lower()
                        if i < len(cells) - 1:
                            context += cells[i+1].get_text(strip=True).lower()

                        if 'rating' in context or 'regular' in context or not player_info.current_rating:
                            player_info.current_rating = int(text)

                    # Look for state (2 letter abbreviation)
                    elif re.match(r'^[A-Z]{2}$', text):
                        player_info.state = text

                    # Look for expiration date
                    elif re.match(r'\d{1,2}/\d{1,2}/\d{4}', text):
                        player_info.expiration_date = text

        # If still no name, try to find it in the page content
        if not player_info.name:
            # Look for header tags
            for header in soup.find_all(['h1', 'h2', 'h3']):
                header_text = header.get_text(strip=True)
                if len(header_text) > 3 and not header_text.isdigit():
                    player_info.name = header_text
                    break

        return player_info if player_info.name else None

    def _parse_html_player_data(self, html_content: str) -> List[PlayerInfo]:
        """Parse HTML content to extract player data from tables or structured elements"""
        players = []

        # Look for table rows containing player data
        table_row_pattern = r'<tr[^>]*>(.*?)</tr>'
        rows = re.findall(table_row_pattern, html_content, re.DOTALL | re.IGNORECASE)

        for row in rows:
            # Extract data from table cells
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)

            if len(cells) >= 2:  # At least name and some other info
                player = PlayerInfo(name=self._clean_html(cells[0]))

                # Try to extract additional info from other cells
                for cell in cells[1:]:
                    cell_text = self._clean_html(cell)

                    # Check if it's a rating
                    if re.match(r'^\d{3,4}$', cell_text):
                        player.current_rating = int(cell_text)

                    # Check if it's a state
                    elif re.match(r'^[A-Z]{2}$', cell_text):
                        player.state = cell_text

                    # Check if it's a USCF ID
                    elif re.match(r'^\d{8,}$', cell_text):
                        player.uscf_id = cell_text

                if player.name:
                    players.append(player)

        return players

    def _parse_rating_history(self, html_content: str) -> List[Dict]:
        """Parse rating history from HTML content"""
        history = []

        # Look for rating history data in JSON or structured HTML
        json_pattern = r'ratingHistory\s*[:=]\s*(\[.*?\])'
        json_match = re.search(json_pattern, html_content, re.DOTALL)

        if json_match:
            try:
                history = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        return history

    def _parse_tournament_history(self, html_content: str) -> List[Dict]:
        """Parse tournament history from HTML content"""
        history = []

        # Look for tournament data
        json_pattern = r'tournaments\s*[:=]\s*(\[.*?\])'
        json_match = re.search(json_pattern, html_content, re.DOTALL)

        if json_match:
            try:
                history = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        return history

    def _create_player_info_from_dict(self, data: Dict) -> PlayerInfo:
        """Create a PlayerInfo object from a dictionary of data"""
        return PlayerInfo(
            name=data.get('name', ''),
            uscf_id=str(data.get('id', '')),
            current_rating=data.get('rating'),
            state=data.get('state'),
            expiration_date=data.get('expiration'),
            membership_status=data.get('status')
        )

    def _clean_html(self, html_text: str) -> str:
        """Remove HTML tags and clean up text"""
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', html_text)
        # Clean up whitespace
        clean_text = ' '.join(clean_text.split())
        return clean_text.strip()


def main():
    """Example usage of the USCF Player Lookup tool"""
    lookup = USCFPlayerLookup()

    print("USCF Player Lookup Tool")
    print("=======================\n")

    while True:
        print("Search options:")
        print("1. Search by name")
        print("2. Search by USCF ID")
        print("3. Exit")

        choice = input("\nEnter your choice (1-3): ").strip()

        if choice == '1':
            first_name = input("Enter first name: ").strip()
            last_name = input("Enter last name: ").strip()
            state = input("Enter state (optional, e.g., CA): ").strip() or None

            print(f"\nSearching for {first_name} {last_name}...")

            players = lookup.search_player_by_name(first_name, last_name, state)

            if players:
                print(f"\nFound {len(players)} player(s):")
                for i, player in enumerate(players, 1):
                    print(f"\n{i}. {player.name}")
                    if player.uscf_id:
                        print(f"   USCF ID: {player.uscf_id}")
                    if player.current_rating:
                        print(f"   Current Rating: {player.current_rating}")
                    if player.state:
                        print(f"   State: {player.state}")
                    if player.membership_status:
                        print(f"   Status: {player.membership_status}")
            else:
                print("No players found.")

        elif choice == '2':
            uscf_id = input("Enter USCF ID: ").strip()

            print(f"\nLooking up player with ID {uscf_id}...")

            player = lookup.search_player_by_id(uscf_id)

            if player:
                print(f"\nPlayer found:")
                print(f"Name: {player.name}")
                print(f"USCF ID: {player.uscf_id}")
                if player.current_rating:
                    print(f"Current Rating: {player.current_rating}")
                if player.state:
                    print(f"State: {player.state}")

                # Try to get additional data
                rating_history = lookup.get_player_rating_history(uscf_id)
                if rating_history:
                    print(f"Rating History: {len(rating_history)} entries found")

                tournament_history = lookup.get_player_tournament_history(uscf_id)
                if tournament_history:
                    print(f"Tournament History: {len(tournament_history)} entries found")
            else:
                print("Player not found.")

        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

        print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    main()