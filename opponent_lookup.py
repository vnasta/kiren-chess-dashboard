#!/usr/bin/env python3
"""
Opponent Lookup and Search System
Query and analyze all cached opponents from Kiren's last 10 tournaments
"""

import json
import os
import argparse
from typing import Dict, List, Optional
from dataclasses import dataclass


def load_comprehensive_cache(filename: str = "data/comprehensive_opponents_cache.json") -> Dict:
    """Load the comprehensive opponent cache"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading cache: {e}")
        return {}


def search_opponents(cache_data: Dict, query: str, limit: int = 10) -> List[Dict]:
    """Search opponents by name"""
    if 'opponents' not in cache_data:
        return []

    query_upper = query.upper()
    matches = []

    for name, profile in cache_data['opponents'].items():
        if query_upper in name.upper():
            matches.append({
                'name': name,
                'profile': profile,
                'relevance': 1.0 if name.upper() == query_upper else 0.5
            })

    # Sort by relevance and rating
    matches.sort(key=lambda x: (x['relevance'], x['profile']['avg_rating']), reverse=True)
    return matches[:limit]


def get_opponents_by_title(cache_data: Dict, title: str) -> List[Dict]:
    """Get all opponents with a specific title"""
    if 'opponents' not in cache_data:
        return []

    title_upper = title.upper()
    matches = []

    for name, profile in cache_data['opponents'].items():
        profile_title = profile.get('title') or ''
        if profile_title.upper() == title_upper:
            matches.append({
                'name': name,
                'profile': profile
            })

    # Sort by rating
    matches.sort(key=lambda x: x['profile']['avg_rating'], reverse=True)
    return matches


def get_opponents_by_rating_range(cache_data: Dict, min_rating: int, max_rating: int) -> List[Dict]:
    """Get opponents within a rating range"""
    if 'opponents' not in cache_data:
        return []

    matches = []
    for name, profile in cache_data['opponents'].items():
        rating = profile['avg_rating']
        if min_rating <= rating <= max_rating:
            matches.append({
                'name': name,
                'profile': profile
            })

    matches.sort(key=lambda x: x['profile']['avg_rating'], reverse=True)
    return matches


def get_most_played_opponents(cache_data: Dict, limit: int = 10) -> List[Dict]:
    """Get opponents faced multiple times"""
    if 'opponents' not in cache_data:
        return []

    multiple_encounters = []
    for name, profile in cache_data['opponents'].items():
        if profile['total_encounters'] > 1:
            multiple_encounters.append({
                'name': name,
                'profile': profile
            })

    multiple_encounters.sort(key=lambda x: x['profile']['total_encounters'], reverse=True)
    return multiple_encounters[:limit]


def get_upset_victories(cache_data: Dict) -> List[Dict]:
    """Get all opponents Kiren beat despite being lower-rated"""
    if 'opponents' not in cache_data:
        return []

    upsets = []
    for name, profile in cache_data['opponents'].items():
        if profile['upset_victories'] > 0:
            upsets.append({
                'name': name,
                'profile': profile
            })

    upsets.sort(key=lambda x: x['profile']['avg_rating'], reverse=True)
    return upsets


def display_opponent_profile(name: str, profile: Dict, detailed: bool = False):
    """Display a formatted opponent profile"""
    title_str = f" ({profile.get('title', 'Untitled')})" if profile.get('title') else ""

    print(f"\n👤 {name}{title_str}")
    print(f"   Rating: {profile['avg_rating']:.0f} (range: {profile['lowest_rating']}-{profile['highest_rating']})")

    encounters = profile['total_encounters']
    wins = profile['losses_against_kiren']  # Kiren's wins
    losses = profile['wins_against_kiren']  # Kiren's losses
    draws = profile['draws_against_kiren']
    win_rate = profile['kiren_win_rate']

    print(f"   Record vs Kiren: {wins}W-{losses}L-{draws}D ({encounters} games, {win_rate:.1f}% for Kiren)")

    if profile['upset_victories'] > 0:
        print(f"   ⚡ Upset victories by Kiren: {profile['upset_victories']}")

    if detailed:
        print(f"   First encountered: {profile['first_encounter']}")
        print(f"   Last encountered: {profile['last_encounter']}")
        print(f"   Tournaments met: {', '.join(profile['tournaments_met'])}")

        if profile['encounter_span_days'] > 0:
            print(f"   Encounter span: {profile['encounter_span_days']} days")

        rating_diff = profile['rating_difference_avg']
        if rating_diff != 0:
            print(f"   Avg rating difference: {rating_diff:+.0f} (Kiren vs opponent)")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Search and analyze Kiren's opponents")
    parser.add_argument('command', choices=[
        'search', 'title', 'rating', 'multiple', 'upsets', 'stats', 'top', 'profile'
    ], help='Command to execute')

    parser.add_argument('--query', '-q', type=str, help='Search query')
    parser.add_argument('--title', '-t', type=str, help='Title to filter by (GM, IM, FM, etc.)')
    parser.add_argument('--min-rating', type=int, help='Minimum rating')
    parser.add_argument('--max-rating', type=int, help='Maximum rating')
    parser.add_argument('--limit', '-l', type=int, default=10, help='Limit results')
    parser.add_argument('--detailed', '-d', action='store_true', help='Show detailed profiles')

    args = parser.parse_args()

    # Load cache
    cache_data = load_comprehensive_cache()
    if not cache_data:
        print("❌ Could not load opponent cache. Run comprehensive_opponent_cache.py first.")
        return

    print(f"📊 Loaded cache with {cache_data.get('total_opponents', 0)} opponents")
    print(f"📅 Created: {cache_data.get('created', 'Unknown')[:19]}")

    if args.command == 'search':
        if not args.query:
            print("❌ Please provide a search query with --query")
            return

        print(f"\n🔍 Searching for: '{args.query}'")
        matches = search_opponents(cache_data, args.query, args.limit)

        if not matches:
            print("No opponents found matching your query")
            return

        for match in matches:
            display_opponent_profile(match['name'], match['profile'], args.detailed)

    elif args.command == 'title':
        if not args.title:
            print("❌ Please provide a title with --title (GM, IM, FM, etc.)")
            return

        print(f"\n🎖️ Opponents with title: {args.title}")
        matches = get_opponents_by_title(cache_data, args.title)

        if not matches:
            print(f"No opponents found with title '{args.title}'")
            return

        for match in matches:
            display_opponent_profile(match['name'], match['profile'], args.detailed)

    elif args.command == 'rating':
        min_rating = args.min_rating or 0
        max_rating = args.max_rating or 4000

        print(f"\n📈 Opponents rated {min_rating}-{max_rating}")
        matches = get_opponents_by_rating_range(cache_data, min_rating, max_rating)

        if not matches:
            print(f"No opponents found in rating range {min_rating}-{max_rating}")
            return

        for match in matches[:args.limit]:
            display_opponent_profile(match['name'], match['profile'], args.detailed)

    elif args.command == 'multiple':
        print(f"\n🔄 Opponents faced multiple times")
        matches = get_most_played_opponents(cache_data, args.limit)

        if not matches:
            print("No opponents faced multiple times")
            return

        for match in matches:
            display_opponent_profile(match['name'], match['profile'], args.detailed)

    elif args.command == 'upsets':
        print(f"\n⚡ Upset victories by Kiren")
        matches = get_upset_victories(cache_data)

        if not matches:
            print("No upset victories found")
            return

        for match in matches[:args.limit]:
            display_opponent_profile(match['name'], match['profile'], args.detailed)

    elif args.command == 'top':
        print(f"\n🏆 Top {args.limit} opponents by rating")
        if 'opponents' not in cache_data:
            return

        top_opponents = sorted(
            cache_data['opponents'].items(),
            key=lambda x: x[1]['avg_rating'],
            reverse=True
        )[:args.limit]

        for name, profile in top_opponents:
            display_opponent_profile(name, profile, args.detailed)

    elif args.command == 'stats':
        print(f"\n📊 COMPREHENSIVE STATISTICS")
        print(f"="*50)

        if 'opponents' not in cache_data:
            return

        opponents = cache_data['opponents']

        # Title distribution
        title_counts = {}
        for profile in opponents.values():
            title = profile.get('title') or 'Untitled'
            title_counts[title] = title_counts.get(title, 0) + 1

        print(f"\n🎖️ Title Distribution:")
        for title, count in sorted(title_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {title}: {count}")

        # Rating ranges
        ranges = {
            '2700+': 0, '2600-2699': 0, '2500-2599': 0, '2400-2499': 0,
            '2300-2399': 0, '2200-2299': 0, '2000-2199': 0, '<2000': 0
        }

        for profile in opponents.values():
            rating = profile['avg_rating']
            if rating >= 2700:
                ranges['2700+'] += 1
            elif rating >= 2600:
                ranges['2600-2699'] += 1
            elif rating >= 2500:
                ranges['2500-2599'] += 1
            elif rating >= 2400:
                ranges['2400-2499'] += 1
            elif rating >= 2300:
                ranges['2300-2399'] += 1
            elif rating >= 2200:
                ranges['2200-2299'] += 1
            elif rating >= 2000:
                ranges['2000-2199'] += 1
            else:
                ranges['<2000'] += 1

        print(f"\n📈 Rating Distribution:")
        for range_name, count in ranges.items():
            if count > 0:
                print(f"  {range_name}: {count}")

    elif args.command == 'profile':
        if not args.query:
            print("❌ Please provide an opponent name with --query")
            return

        matches = search_opponents(cache_data, args.query, 1)
        if matches:
            display_opponent_profile(matches[0]['name'], matches[0]['profile'], detailed=True)
        else:
            print(f"Opponent '{args.query}' not found")


if __name__ == "__main__":
    main()