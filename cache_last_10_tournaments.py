#!/usr/bin/env python3
"""
Cache opponents from Kiren's last 10 tournaments
Uses only clean tournament data with actual opponent information
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class OpponentInfo:
    """Information about a chess opponent"""
    name: str
    ratings_faced: List[int]
    results_against: List[str]
    tournaments_met: List[str]
    rounds_played: List[int]
    last_faced: str
    total_games: int
    wins_against: int
    losses_against: int
    draws_against: int
    avg_rating: float


def clean_opponent_name(name: str) -> str:
    """Clean up opponent names to remove artifacts"""
    if not name:
        return ""

    # Remove common HTML parsing artifacts
    invalid_patterns = [
        "Click on a Section Name",
        "The ratings shown on this page",
        "Section(s),",
        "Players",
        "not official published ratings",
        "may change from time to time",
        "Using them for pairing purposes",
        "should only be done if this has been advertised",
        "advance publicity and is announced"
    ]

    for pattern in invalid_patterns:
        if pattern.lower() in name.lower():
            return ""

    # Remove excessive whitespace and special characters
    import re
    name = re.sub(r'\s+', ' ', name).strip()

    # Must be a reasonable length for a name
    if len(name) < 3 or len(name) > 50:
        return ""

    # Should contain at least one letter
    if not re.search(r'[A-Za-z]', name):
        return ""

    # Remove leading/trailing punctuation
    name = name.strip('.,;:*')

    return name


def load_clean_tournaments() -> List[Dict]:
    """Load tournaments from clean data sources only"""
    clean_files = [
        "data/real_kiren_tournaments.json",
        "data/kiren_real_multiyear.json"
    ]

    all_tournaments = []
    for file_path in clean_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    tournaments = json.load(f)
                    if isinstance(tournaments, list):
                        all_tournaments.extend(tournaments)
                        print(f"Loaded {len(tournaments)} tournaments from {file_path}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

    return all_tournaments


def get_last_n_tournaments(tournaments: List[Dict], n: int = 10) -> List[Dict]:
    """Get the last N tournaments sorted by date"""
    # Sort by date (most recent first)
    sorted_tournaments = sorted(
        tournaments,
        key=lambda x: x.get('date', ''),
        reverse=True
    )

    recent = sorted_tournaments[:n]
    print(f"\n📅 Selected {len(recent)} most recent tournaments:")
    for i, t in enumerate(recent, 1):
        print(f"  {i:2d}. {t.get('name', 'Unknown'):<40} ({t.get('date', 'No date')})")

    return recent


def cache_opponents_from_tournaments(tournaments: List[Dict]) -> Dict[str, OpponentInfo]:
    """Extract and cache opponents from tournaments"""
    opponents_cache = {}

    print(f"\n🔍 Processing {len(tournaments)} tournaments for opponents...")

    for tournament in tournaments:
        tournament_name = tournament.get('name', 'Unknown Tournament')
        tournament_date = tournament.get('date', '')

        opponents_in_tournament = tournament.get('opponents', [])
        print(f"  {tournament_name}: {len(opponents_in_tournament)} opponents")

        for opponent_data in opponents_in_tournament:
            name = opponent_data.get('name', '').strip()
            if not name:
                continue

            # Clean up opponent name
            name = clean_opponent_name(name)
            if not name:
                continue

            rating = opponent_data.get('rating', 0)
            result = opponent_data.get('result', '').upper()
            round_num = opponent_data.get('round', 0)

            if name not in opponents_cache:
                opponents_cache[name] = OpponentInfo(
                    name=name,
                    ratings_faced=[],
                    results_against=[],
                    tournaments_met=[],
                    rounds_played=[],
                    last_faced='',
                    total_games=0,
                    wins_against=0,
                    losses_against=0,
                    draws_against=0,
                    avg_rating=0.0
                )

            opponent_info = opponents_cache[name]

            # Add this encounter
            opponent_info.ratings_faced.append(rating)
            opponent_info.results_against.append(result)
            opponent_info.tournaments_met.append(tournament_name)
            opponent_info.rounds_played.append(round_num)

            # Update last faced date
            if tournament_date > opponent_info.last_faced:
                opponent_info.last_faced = tournament_date

            # Update stats
            opponent_info.total_games += 1
            if result == 'W':
                opponent_info.wins_against += 1
            elif result == 'L':
                opponent_info.losses_against += 1
            elif result == 'D':
                opponent_info.draws_against += 1

            # Update average rating
            if opponent_info.ratings_faced:
                opponent_info.avg_rating = sum(opponent_info.ratings_faced) / len(opponent_info.ratings_faced)

    return opponents_cache


def save_cache(opponents_cache: Dict[str, OpponentInfo], filename: str = "data/last_10_tournaments_cache.json"):
    """Save the cache to file"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        cache_data = {
            'last_updated': datetime.now().isoformat(),
            'source': 'last_10_tournaments',
            'opponents': {name: asdict(info) for name, info in opponents_cache.items()}
        }

        with open(filename, 'w') as f:
            json.dump(cache_data, f, indent=2)

        print(f"💾 Saved {len(opponents_cache)} opponents to {filename}")
        return True
    except Exception as e:
        print(f"❌ Could not save cache: {e}")
        return False


def print_statistics(opponents_cache: Dict[str, OpponentInfo]):
    """Print detailed statistics"""
    if not opponents_cache:
        print("❌ No opponents cached")
        return

    total_opponents = len(opponents_cache)
    total_games = sum(info.total_games for info in opponents_cache.values())
    total_wins = sum(info.wins_against for info in opponents_cache.values())
    total_losses = sum(info.losses_against for info in opponents_cache.values())
    total_draws = sum(info.draws_against for info in opponents_cache.values())

    avg_opponent_rating = sum(info.avg_rating for info in opponents_cache.values()) / total_opponents

    win_percentage = (total_wins / total_games * 100) if total_games > 0 else 0

    print(f"\n📊 LAST 10 TOURNAMENTS OPPONENT STATISTICS")
    print(f"="*50)
    print(f"Total opponents: {total_opponents}")
    print(f"Total games: {total_games}")
    print(f"Wins: {total_wins} | Losses: {total_losses} | Draws: {total_draws}")
    print(f"Win percentage: {win_percentage:.1f}%")
    print(f"Average opponent rating: {avg_opponent_rating:.0f}")

    # Rating distribution
    rating_ranges = {
        '2400+': len([info for info in opponents_cache.values() if info.avg_rating >= 2400]),
        '2200-2399': len([info for info in opponents_cache.values() if 2200 <= info.avg_rating < 2400]),
        '2000-2199': len([info for info in opponents_cache.values() if 2000 <= info.avg_rating < 2200]),
        '1800-1999': len([info for info in opponents_cache.values() if 1800 <= info.avg_rating < 2000]),
        '<1800': len([info for info in opponents_cache.values() if info.avg_rating < 1800])
    }

    print(f"\nRating distribution:")
    for rating_range, count in rating_ranges.items():
        print(f"  {rating_range}: {count} opponents")

    # Top opponents
    print(f"\n🏆 TOP 10 OPPONENTS BY RATING")
    top_opponents = sorted(opponents_cache.values(), key=lambda x: x.avg_rating, reverse=True)[:10]

    for i, opp in enumerate(top_opponents, 1):
        win_rate = (opp.wins_against / opp.total_games * 100) if opp.total_games > 0 else 0
        print(f"{i:2d}. {opp.name:<30} (avg: {opp.avg_rating:.0f}) - {opp.total_games} games, {win_rate:.1f}% win rate")


def main():
    """Main function to cache last 10 tournaments"""
    print("🎯 CACHING KIREN'S OPPONENTS FROM LAST 10 TOURNAMENTS")
    print("="*60)

    # Load clean tournament data
    all_tournaments = load_clean_tournaments()

    if not all_tournaments:
        print("❌ No tournament data found!")
        return

    # Get last 10 tournaments
    recent_tournaments = get_last_n_tournaments(all_tournaments, 10)

    if not recent_tournaments:
        print("❌ No recent tournaments found!")
        return

    # Cache opponents
    opponents_cache = cache_opponents_from_tournaments(recent_tournaments)

    if not opponents_cache:
        print("❌ No opponents found in recent tournaments!")
        return

    # Save cache
    save_cache(opponents_cache)

    # Print statistics
    print_statistics(opponents_cache)

    print(f"\n✅ Successfully cached opponents from last 10 tournaments!")


if __name__ == "__main__":
    main()