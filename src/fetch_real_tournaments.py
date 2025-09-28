#!/usr/bin/env python3
"""
Fetch real tournament data for Kiren Nasta from USCF
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json

class USCFTournamentFetcher:
    def __init__(self, uscf_id="15255524"):
        self.uscf_id = uscf_id
        self.base_url = "http://www.uschess.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_tournament_history(self):
        """Get tournament history from USCF website"""
        print(f"Fetching tournament history for USCF ID: {self.uscf_id}")

        # Try multiple URLs for tournament history
        urls = [
            f"{self.base_url}/msa/MbrDtlTnmtHst.php?{self.uscf_id}",
            f"{self.base_url}/msa/MbrDtlMain.php?{self.uscf_id}",
            f"{self.base_url}/msa/MbrDtlTnmtHst.php?{self.uscf_id}.0"
        ]

        for url in urls:
            print(f"Trying URL: {url}")
            try:
                response = self.session.get(url)
                print(f"Response status: {response.status_code}")

                if response.status_code == 200:
                    tournaments = self.parse_tournament_history(response.text)
                    if tournaments:
                        print(f"Found {len(tournaments)} tournaments")
                        return tournaments
                    else:
                        print("No tournaments found in this page")
                        # Print first 1000 chars to debug
                        print("Page content preview:")
                        print(response.text[:1000])
                        print("...")

            except Exception as e:
                print(f"Error with {url}: {e}")

        return []

    def parse_tournament_history(self, html_content):
        """Parse tournament history from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        tournaments = []

        print("Parsing tournament data...")

        # Look for tables containing tournament data
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables")

        for i, table in enumerate(tables):
            print(f"Analyzing table {i+1}")
            rows = table.find_all('tr')

            if len(rows) < 2:
                continue

            # Check if this looks like a tournament table
            header_row = rows[0]
            headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
            print(f"Table {i+1} headers: {headers}")

            # Look for tournament-related headers
            tournament_indicators = ['event', 'tournament', 'date', 'rating', 'section', 'score', 'pair']

            if any(indicator in ' '.join(headers) for indicator in tournament_indicators):
                print(f"Table {i+1} appears to contain tournament data")

                for j, row in enumerate(rows[1:]):  # Skip header row
                    cells = row.find_all(['td', 'th'])

                    if len(cells) >= 3:
                        tournament = self.extract_tournament_from_row(cells, j+1)
                        if tournament:
                            tournaments.append(tournament)
                            print(f"Extracted tournament: {tournament.get('name', 'Unknown')}")

        return tournaments

    def extract_tournament_from_row(self, cells, row_num):
        """Extract tournament data from a table row"""
        tournament = {
            'name': '',
            'date': '',
            'section': '',
            'rating_before': 0,
            'rating_after': 0,
            'score': '',
            'event_id': '',
            'opponents': []
        }

        cell_texts = [cell.get_text(strip=True) for cell in cells]
        print(f"Row {row_num} data: {cell_texts}")

        for i, cell in enumerate(cells):
            text = cell.get_text(strip=True)

            # Look for event name/link
            link = cell.find('a')
            if link and 'href' in link.attrs:
                href = link['href']
                # Extract event ID from link
                event_match = re.search(r'(\d{12})', href)
                if event_match:
                    tournament['event_id'] = event_match.group(1)
                    tournament['name'] = text or f"Event {tournament['event_id']}"

            # Parse dates (various formats)
            date_patterns = [
                r'(\d{1,2})/(\d{1,2})/(\d{4})',
                r'(\d{1,2})-(\d{1,2})-(\d{4})',
                r'(\d{4})-(\d{1,2})-(\d{1,2})'
            ]

            for pattern in date_patterns:
                date_match = re.search(pattern, text)
                if date_match:
                    if pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD
                        year, month, day = date_match.groups()
                    else:  # MM/DD/YYYY or MM-DD-YYYY
                        month, day, year = date_match.groups()
                    tournament['date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    break

            # Parse ratings
            if re.match(r'^\d{3,4}$', text):
                rating = int(text)
                if not tournament['rating_before']:
                    tournament['rating_before'] = rating
                else:
                    tournament['rating_after'] = rating

            # Parse scores
            score_match = re.search(r'(\d+(?:\.\d+)?)[/\-](\d+(?:\.\d+)?)', text)
            if score_match:
                tournament['score'] = f"{score_match.group(1)}/{score_match.group(2)}"

            # Look for section information
            if len(text) > 2 and any(keyword in text.lower() for keyword in ['open', 'section', 'u1800', 'u2000', 'reserve']):
                tournament['section'] = text

        # Only return if we have essential data
        if tournament['name'] or tournament['event_id']:
            return tournament
        return None

    def get_tournament_details(self, event_id):
        """Get detailed tournament information including opponents"""
        if not event_id:
            return None

        print(f"Fetching details for event {event_id}")

        # Try different URLs for tournament details
        detail_urls = [
            f"{self.base_url}/msa/XtblMain.php?{event_id}",
            f"{self.base_url}/msa/XtblMain.php?{event_id}.0",
            f"{self.base_url}/msa/XtblPlrs.php?{event_id}"
        ]

        for url in detail_urls:
            try:
                print(f"Trying detail URL: {url}")
                response = self.session.get(url)

                if response.status_code == 200:
                    opponents = self.parse_tournament_details(response.text, event_id)
                    if opponents:
                        print(f"Found {len(opponents)} opponents")
                        return opponents

            except Exception as e:
                print(f"Error getting tournament details: {e}")

        return []

    def parse_tournament_details(self, html_content, event_id):
        """Parse tournament crosstable for opponent information"""
        soup = BeautifulSoup(html_content, 'html.parser')
        opponents = []

        print(f"Parsing tournament details for event {event_id}")

        # Look for crosstable or results table
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all(['td', 'th'])

                # Look for player data (name, rating, results)
                if len(cells) >= 4:
                    opponent_data = self.extract_opponent_data(cells)
                    if opponent_data:
                        opponents.append(opponent_data)

        return opponents

    def extract_opponent_data(self, cells):
        """Extract opponent information from table cells"""
        opponent = {
            'name': '',
            'rating': 0,
            'result': '',
            'round': 0
        }

        for cell in cells:
            text = cell.get_text(strip=True)

            # Look for names (usually longer text with comma)
            if ',' in text and len(text) > 5:
                opponent['name'] = text

            # Look for ratings
            if re.match(r'^\d{3,4}$', text):
                opponent['rating'] = int(text)

            # Look for results (W, L, D, etc.)
            if re.match(r'^[WLD]$', text.upper()):
                opponent['result'] = text.upper()

            # Look for round numbers
            if re.match(r'^\d{1,2}$', text) and int(text) <= 15:
                opponent['round'] = int(text)

        return opponent if opponent['name'] else None

    def fetch_all_data(self):
        """Fetch complete tournament data with opponents"""
        print("Starting comprehensive data fetch...")

        tournaments = self.get_tournament_history()

        # Get detailed opponent data for each tournament
        for tournament in tournaments:
            if tournament.get('event_id'):
                opponents = self.get_tournament_details(tournament['event_id'])
                tournament['opponents'] = opponents
            else:
                tournament['opponents'] = []

        return tournaments

    def save_to_json(self, tournaments, filename='kiren_tournaments.json'):
        """Save tournament data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(tournaments, f, indent=2)
        print(f"Data saved to {filename}")

def main():
    fetcher = USCFTournamentFetcher()

    print("Fetching real tournament data for Kiren Nasta...")
    tournaments = fetcher.fetch_all_data()

    if tournaments:
        print(f"\nFound {len(tournaments)} tournaments:")
        for i, tournament in enumerate(tournaments, 1):
            print(f"\n{i}. {tournament.get('name', 'Unknown Event')}")
            print(f"   Date: {tournament.get('date', 'Unknown')}")
            print(f"   Section: {tournament.get('section', 'Unknown')}")
            print(f"   Score: {tournament.get('score', 'Unknown')}")
            print(f"   Rating: {tournament.get('rating_before', '?')} → {tournament.get('rating_after', '?')}")
            print(f"   Opponents: {len(tournament.get('opponents', []))}")

            # Show first few opponents
            for j, opp in enumerate(tournament.get('opponents', [])[:3]):
                print(f"     R{opp.get('round', '?')}: {opp.get('name', 'Unknown')} ({opp.get('rating', '?')}) - {opp.get('result', '?')}")

        # Save to file
        fetcher.save_to_json(tournaments)

    else:
        print("No tournament data found. This could be due to:")
        print("1. Different website structure than expected")
        print("2. Authentication requirements")
        print("3. Player has no tournament history on record")
        print("4. Website access restrictions")

if __name__ == "__main__":
    main()