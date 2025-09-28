#!/usr/bin/env python3
"""
Interactive USCF Player Search Tool
"""

import sys
from uscf_player_lookup import USCFPlayerLookup

def search_player(first_name, last_name, state=None):
    """Search for a specific player"""

    lookup = USCFPlayerLookup()

    print(f"Looking up {first_name} {last_name}...")
    if state:
        print(f"Filtering by state: {state}")
    print("=" * 50)

    # Primary search
    players = lookup.search_player_by_name(first_name, last_name, state)

    if players:
        print(f"\nFound {len(players)} player(s):")
        for i, player in enumerate(players, 1):
            print(f"\n{i}. {player.name}")
            if player.uscf_id:
                print(f"   USCF ID: {player.uscf_id}")
            if player.current_rating:
                print(f"   Current Rating: {player.current_rating}")
            if player.peak_rating:
                print(f"   Peak Rating: {player.peak_rating}")
            if player.state:
                print(f"   State: {player.state}")
            if player.membership_status:
                print(f"   Membership Status: {player.membership_status}")
            if player.expiration_date:
                print(f"   Expiration Date: {player.expiration_date}")

            # Get additional data if we have USCF ID
            if player.uscf_id:
                try:
                    rating_history = lookup.get_player_rating_history(player.uscf_id)
                    if rating_history:
                        print(f"   Rating History: {len(rating_history)} entries available")

                    tournament_history = lookup.get_player_tournament_history(player.uscf_id)
                    if tournament_history:
                        print(f"   Tournament History: {len(tournament_history)} entries available")
                except:
                    pass
    else:
        print(f"No players found with the name '{first_name} {last_name}'")

        # Try some common variations
        variations = []

        # Common nickname expansions
        nickname_map = {
            'mike': 'michael',
            'bob': 'robert',
            'bill': 'william',
            'jim': 'james',
            'tom': 'thomas',
            'rick': 'richard',
            'dave': 'david',
            'steve': 'stephen',
            'chris': 'christopher',
            'nick': 'nicholas'
        }

        # Try expanded first name
        first_lower = first_name.lower()
        if first_lower in nickname_map:
            variations.append((nickname_map[first_lower].title(), last_name))

        # Try nickname if given full name
        for nick, full in nickname_map.items():
            if first_lower == full:
                variations.append((nick.title(), last_name))

        # Try different capitalizations
        variations.append((first_name.upper(), last_name.upper()))
        variations.append((first_name.lower(), last_name.lower()))

        # Try common misspellings for Kiren
        if first_name.lower() == 'kiren':
            variations.extend([
                ('Kiran', last_name),
                ('Kieran', last_name),
                ('Kyren', last_name),
                ('Karen', last_name)
            ])

        if variations:
            print(f"\nTrying variations...")
            for alt_first, alt_last in variations:
                if alt_first.lower() == first_name.lower() and alt_last.lower() == last_name.lower():
                    continue  # Skip if same as original

                print(f"Searching for '{alt_first} {alt_last}'...")
                alt_players = lookup.search_player_by_name(alt_first, alt_last, state)

                if alt_players:
                    print(f"Found {len(alt_players)} player(s) with '{alt_first} {alt_last}':")
                    for player in alt_players:
                        print(f"  - {player.name}")
                        if player.current_rating:
                            print(f"    Rating: {player.current_rating}")
                        if player.state:
                            print(f"    State: {player.state}")
                        if player.uscf_id:
                            print(f"    USCF ID: {player.uscf_id}")
                    break
            else:
                print("No matches found with variations either.")

def main():
    """Main function to handle command line arguments"""

    if len(sys.argv) < 3:
        print("Usage: python3 search_player.py <first_name> <last_name> [state]")
        print("Example: python3 search_player.py Kiren Nasta")
        print("Example: python3 search_player.py John Smith CA")
        return

    first_name = sys.argv[1]
    last_name = sys.argv[2]
    state = sys.argv[3] if len(sys.argv) > 3 else None

    search_player(first_name, last_name, state)

if __name__ == "__main__":
    main()