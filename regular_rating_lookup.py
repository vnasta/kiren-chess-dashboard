#!/usr/bin/env python3
"""
Regular Rating Lookup Tool
Search and analyze opponents by their standard/classical ratings only
"""

import json
import argparse
from typing import Dict, List, Optional


def load_regular_rating_cache(filename: str = "data/regular_rating_cache.json") -> Dict:
    """Load the regular rating cache"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading regular rating cache: {e}")
        return {}


def search_by_regular_rating(cache_data: Dict, min_rating: int, max_rating: int) -> List[Dict]:
    """Search opponents by regular rating range"""
    if 'opponents' not in cache_data:
        return []

    matches = []
    for name, profile in cache_data['opponents'].items():
        rating = profile['avg_regular_rating']
        if min_rating <= rating <= max_rating:
            matches.append({
                'name': name,
                'profile': profile
            })

    matches.sort(key=lambda x: x['profile']['avg_regular_rating'], reverse=True)
    return matches


def get_strongest_regular_opponents(cache_data: Dict, limit: int = 10) -> List[Dict]:
    """Get strongest opponents by regular rating"""
    if 'opponents' not in cache_data:
        return []

    all_opponents = []
    for name, profile in cache_data['opponents'].items():
        all_opponents.append({
            'name': name,
            'profile': profile
        })

    all_opponents.sort(key=lambda x: x['profile']['avg_regular_rating'], reverse=True)
    return all_opponents[:limit]


def get_regular_rating_upsets(cache_data: Dict) -> List[Dict]:
    """Get all upset victories in regular time control"""
    if 'opponents' not in cache_data:
        return []

    upsets = []
    for name, profile in cache_data['opponents'].items():
        if profile['upset_wins'] > 0:
            upsets.append({
                'name': name,
                'profile': profile
            })

    upsets.sort(key=lambda x: x['profile']['avg_regular_rating'], reverse=True)
    return upsets


def search_regular_opponents(cache_data: Dict, query: str) -> List[Dict]:
    """Search opponents by name in regular games"""
    if 'opponents' not in cache_data:
        return []

    query_upper = query.upper()
    matches = []

    for name, profile in cache_data['opponents'].items():
        if query_upper in name.upper():
            matches.append({
                'name': name,
                'profile': profile
            })

    matches.sort(key=lambda x: x['profile']['avg_regular_rating'], reverse=True)
    return matches


def display_regular_opponent(name: str, profile: Dict, detailed: bool = False):
    """Display opponent profile with regular rating focus"""
    title_str = f" ({profile.get('title', 'Untitled')})" if profile.get('title') else ""

    print(f"\n👤 {name}{title_str}")

    # Regular rating info
    avg_rating = profile['avg_regular_rating']
    highest = profile['highest_regular_rating']
    lowest = profile['lowest_regular_rating']

    if highest == lowest:
        print(f"   Regular Rating: {avg_rating:.0f}")
    else:
        print(f"   Regular Rating: {avg_rating:.0f} (range: {lowest}-{highest})")

    # Game results
    games = profile['total_regular_games']
    wins = profile['kiren_wins']
    losses = profile['kiren_losses']
    draws = profile['kiren_draws']
    win_rate = profile['kiren_win_rate']

    print(f"   Regular Games vs Kiren: {wins}W-{losses}L-{draws}D ({games} total, {win_rate:.1f}% for Kiren)")

    # Upset info
    if profile['upset_wins'] > 0:
        print(f"   ⚡ Regular rating upsets by Kiren: {profile['upset_wins']}")

    if detailed:
        print(f"   First regular game: {profile['first_regular_game']}")
        print(f"   Last regular game: {profile['last_regular_game']}")

        tournaments = profile['regular_tournaments']
        if len(tournaments) <= 3:
            print(f"   Regular tournaments: {', '.join(tournaments)}")
        else:
            print(f"   Regular tournaments: {', '.join(tournaments[:3])} ... and {len(tournaments)-3} more")


def main():
    """Main CLI for regular rating lookup"""
    parser = argparse.ArgumentParser(description="Search opponents by regular/classical ratings")
    parser.add_argument('command', choices=[
        'stats', 'top', 'rating', 'upsets', 'search', 'profile', 'masters', 'experts'
    ], help='Command to execute')

    parser.add_argument('--query', '-q', type=str, help='Search query')
    parser.add_argument('--min-rating', type=int, default=0, help='Minimum regular rating')
    parser.add_argument('--max-rating', type=int, default=4000, help='Maximum regular rating')
    parser.add_argument('--limit', '-l', type=int, default=10, help='Limit results')
    parser.add_argument('--detailed', '-d', action='store_true', help='Show detailed profiles')

    args = parser.parse_args()

    # Load cache
    cache_data = load_regular_rating_cache()
    if not cache_data:
        print("❌ Could not load regular rating cache. Run regular_rating_cache.py first.")
        return

    print(f"📊 Regular Rating Cache: {cache_data.get('total_opponents', 0)} opponents")
    print(f"📅 Created: {cache_data.get('created', 'Unknown')[:19]}")
    print(f"🎯 Focus: {cache_data.get('focus', 'Unknown')}")

    if args.command == 'stats':
        print(f"\n📊 REGULAR RATING STATISTICS")
        print(f"="*50)

        if 'opponents' not in cache_data:
            return

        opponents = cache_data['opponents']
        total_opponents = len(opponents)
        total_games = sum(p['total_regular_games'] for p in opponents.values())
        total_wins = sum(p['kiren_wins'] for p in opponents.values())
        total_losses = sum(p['kiren_losses'] for p in opponents.values())
        total_draws = sum(p['kiren_draws'] for p in opponents.values())

        avg_rating = sum(p['avg_regular_rating'] for p in opponents.values()) / total_opponents
        win_rate = (total_wins / total_games * 100) if total_games > 0 else 0

        print(f"Total opponents: {total_opponents}")
        print(f"Total regular games: {total_games}")
        print(f"Kiren's record: {total_wins}W-{total_losses}L-{total_draws}D")
        print(f"Win rate: {win_rate:.1f}%")
        print(f"Average opponent regular rating: {avg_rating:.0f}")

        # Rating ranges
        ranges = {
            '2600+': len([p for p in opponents.values() if p['avg_regular_rating'] >= 2600]),
            '2400-2599': len([p for p in opponents.values() if 2400 <= p['avg_regular_rating'] < 2600]),
            '2200-2399': len([p for p in opponents.values() if 2200 <= p['avg_regular_rating'] < 2400]),
            '2000-2199': len([p for p in opponents.values() if 2000 <= p['avg_regular_rating'] < 2200]),
            '<2000': len([p for p in opponents.values() if p['avg_regular_rating'] < 2000])
        }

        print(f"\nRegular Rating Distribution:")
        for range_name, count in ranges.items():
            if count > 0:
                percentage = (count / total_opponents * 100)
                print(f"  {range_name}: {count} ({percentage:.1f}%)")

    elif args.command == 'top':
        print(f"\n🏆 Top {args.limit} by Regular Rating")
        matches = get_strongest_regular_opponents(cache_data, args.limit)

        for match in matches:
            display_regular_opponent(match['name'], match['profile'], args.detailed)

    elif args.command == 'rating':
        print(f"\n📈 Regular Rating Range: {args.min_rating}-{args.max_rating}")
        matches = search_by_regular_rating(cache_data, args.min_rating, args.max_rating)

        if not matches:
            print(f"No opponents found in regular rating range {args.min_rating}-{args.max_rating}")
            return

        for match in matches[:args.limit]:
            display_regular_opponent(match['name'], match['profile'], args.detailed)

    elif args.command == 'upsets':
        print(f"\n⚡ Regular Rating Upsets by Kiren")
        matches = get_regular_rating_upsets(cache_data)

        if not matches:
            print("No regular rating upsets found")
            return

        for match in matches[:args.limit]:
            display_regular_opponent(match['name'], match['profile'], args.detailed)

    elif args.command == 'search':
        if not args.query:
            print("❌ Please provide a search query with --query")
            return

        print(f"\n🔍 Searching regular opponents: '{args.query}'")
        matches = search_regular_opponents(cache_data, args.query)

        if not matches:
            print("No opponents found")
            return

        for match in matches[:args.limit]:
            display_regular_opponent(match['name'], match['profile'], args.detailed)

    elif args.command == 'profile':
        if not args.query:
            print("❌ Please provide an opponent name with --query")
            return

        matches = search_regular_opponents(cache_data, args.query)
        if matches:
            display_regular_opponent(matches[0]['name'], matches[0]['profile'], detailed=True)
        else:
            print(f"Regular opponent '{args.query}' not found")

    elif args.command == 'masters':
        print(f"\n🎖️ Master Level Opponents (2200+ regular rating)")
        matches = search_by_regular_rating(cache_data, 2200, 4000)

        if not matches:
            print("No master-level opponents found")
            return

        for match in matches[:args.limit]:
            display_regular_opponent(match['name'], match['profile'], args.detailed)

    elif args.command == 'experts':
        print(f"\n🎖️ Expert Level Opponents (2000-2199 regular rating)")
        matches = search_by_regular_rating(cache_data, 2000, 2199)

        if not matches:
            print("No expert-level opponents found")
            return

        for match in matches[:args.limit]:
            display_regular_opponent(match['name'], match['profile'], args.detailed)


if __name__ == "__main__":
    main()