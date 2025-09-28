#!/usr/bin/env python3
"""
Opponent Cache Manager for Kiren Nasta Chess Dashboard
Efficiently caches and manages all of Kiren's opponents across tournaments
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict


@dataclass
class OpponentInfo:
    """Information about a chess opponent"""
    name: str
    ratings_faced: List[int]  # All ratings this opponent had when faced
    results_against: List[str]  # All results (W/L/D) against this opponent
    tournaments_met: List[str]  # Tournament names where they met
    rounds_played: List[int]  # Round numbers where they played
    last_faced: str  # Date of last encounter
    total_games: int
    wins_against: int
    losses_against: int
    draws_against: int
    avg_rating: float


class OpponentCacheManager:
    """Manages caching and retrieval of all opponent data"""

    def __init__(self, cache_file: str = "data/opponents_cache.json"):
        self.cache_file = cache_file
        self.opponents_cache: Dict[str, OpponentInfo] = {}
        self.last_updated = None
        self.source_files = [
            "data/kiren_real_multiyear.json",
            "data/real_kiren_tournaments.json",
            "data/kiren_multiyear_tournaments.json",
            "data/kiren_tournaments.json"
        ]
        self.load_cache()

    def load_cache(self) -> bool:
        """Load opponents cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)

                self.last_updated = cache_data.get('last_updated')
                opponents_data = cache_data.get('opponents', {})

                # Convert back to OpponentInfo objects
                for name, data in opponents_data.items():
                    self.opponents_cache[name] = OpponentInfo(**data)

                print(f"Loaded {len(self.opponents_cache)} opponents from cache")
                return True
        except Exception as e:
            print(f"Could not load cache: {e}")

        return False

    def save_cache(self) -> bool:
        """Save opponents cache to file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

            cache_data = {
                'last_updated': datetime.now().isoformat(),
                'opponents': {name: asdict(info) for name, info in self.opponents_cache.items()}
            }

            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

            self.last_updated = cache_data['last_updated']
            print(f"Saved {len(self.opponents_cache)} opponents to cache")
            return True
        except Exception as e:
            print(f"Could not save cache: {e}")
            return False

    def needs_refresh(self) -> bool:
        """Check if cache needs to be refreshed based on source file modifications"""
        if not self.last_updated:
            return True

        cache_time = datetime.fromisoformat(self.last_updated)

        for source_file in self.source_files:
            if os.path.exists(source_file):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(source_file))
                if file_mtime > cache_time:
                    print(f"Source file {source_file} is newer than cache")
                    return True

        return False

    def clean_opponent_name(self, name: str) -> str:
        """Clean up opponent names to remove HTML artifacts and invalid entries"""
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

    def extract_opponents_from_tournaments(self, tournaments: List[Dict]) -> None:
        """Extract and cache all opponents from tournament data"""
        print(f"Processing {len(tournaments)} tournaments for opponents...")

        for tournament in tournaments:
            tournament_name = tournament.get('name', 'Unknown Tournament')
            tournament_date = tournament.get('date', '')

            for opponent_data in tournament.get('opponents', []):
                name = opponent_data.get('name', '').strip()
                if not name:
                    continue

                # Clean up opponent name - remove HTML artifacts and invalid entries
                name = self.clean_opponent_name(name)
                if not name:
                    continue

                rating = opponent_data.get('rating', 0)
                result = opponent_data.get('result', '').upper()
                round_num = opponent_data.get('round', 0)

                if name not in self.opponents_cache:
                    self.opponents_cache[name] = OpponentInfo(
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

                opponent_info = self.opponents_cache[name]

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

    def refresh_cache(self) -> bool:
        """Refresh the opponents cache from all source files"""
        print("Refreshing opponents cache...")
        self.opponents_cache.clear()

        all_tournaments = []

        for source_file in self.source_files:
            if os.path.exists(source_file):
                try:
                    with open(source_file, 'r') as f:
                        tournaments = json.load(f)
                        if isinstance(tournaments, list):
                            all_tournaments.extend(tournaments)
                            print(f"Loaded {len(tournaments)} tournaments from {source_file}")
                except Exception as e:
                    print(f"Error loading {source_file}: {e}")

        if all_tournaments:
            self.extract_opponents_from_tournaments(all_tournaments)
            return self.save_cache()

        return False

    def get_all_opponents(self) -> Dict[str, OpponentInfo]:
        """Get all cached opponents"""
        if self.needs_refresh():
            self.refresh_cache()
        return self.opponents_cache.copy()

    def get_opponent(self, name: str) -> Optional[OpponentInfo]:
        """Get specific opponent information"""
        if self.needs_refresh():
            self.refresh_cache()
        return self.opponents_cache.get(name)

    def get_opponents_by_rating_range(self, min_rating: int, max_rating: int) -> Dict[str, OpponentInfo]:
        """Get opponents within a specific rating range"""
        if self.needs_refresh():
            self.refresh_cache()

        result = {}
        for name, info in self.opponents_cache.items():
            if min_rating <= info.avg_rating <= max_rating:
                result[name] = info
        return result

    def get_frequent_opponents(self, min_games: int = 2) -> Dict[str, OpponentInfo]:
        """Get opponents played multiple times"""
        if self.needs_refresh():
            self.refresh_cache()

        return {name: info for name, info in self.opponents_cache.items()
                if info.total_games >= min_games}

    def get_top_opponents_by_rating(self, limit: int = 20) -> List[OpponentInfo]:
        """Get top opponents by rating"""
        if self.needs_refresh():
            self.refresh_cache()

        return sorted(self.opponents_cache.values(),
                     key=lambda x: x.avg_rating, reverse=True)[:limit]

    def get_statistics(self) -> Dict:
        """Get overall statistics about opponents"""
        if self.needs_refresh():
            self.refresh_cache()

        if not self.opponents_cache:
            return {}

        total_opponents = len(self.opponents_cache)
        total_games = sum(info.total_games for info in self.opponents_cache.values())
        total_wins = sum(info.wins_against for info in self.opponents_cache.values())
        total_losses = sum(info.losses_against for info in self.opponents_cache.values())
        total_draws = sum(info.draws_against for info in self.opponents_cache.values())

        avg_opponent_rating = sum(info.avg_rating for info in self.opponents_cache.values()) / total_opponents

        rating_ranges = {
            '2400+': len([info for info in self.opponents_cache.values() if info.avg_rating >= 2400]),
            '2200-2399': len([info for info in self.opponents_cache.values() if 2200 <= info.avg_rating < 2400]),
            '2000-2199': len([info for info in self.opponents_cache.values() if 2000 <= info.avg_rating < 2200]),
            '1800-1999': len([info for info in self.opponents_cache.values() if 1800 <= info.avg_rating < 2000]),
            '<1800': len([info for info in self.opponents_cache.values() if info.avg_rating < 1800])
        }

        return {
            'total_opponents': total_opponents,
            'total_games': total_games,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'total_draws': total_draws,
            'win_percentage': (total_wins / total_games * 100) if total_games > 0 else 0,
            'avg_opponent_rating': avg_opponent_rating,
            'rating_distribution': rating_ranges,
            'last_updated': self.last_updated
        }

    def search_opponents(self, search_term: str) -> List[OpponentInfo]:
        """Search opponents by name"""
        if self.needs_refresh():
            self.refresh_cache()

        search_term = search_term.upper()
        results = []

        for info in self.opponents_cache.values():
            if search_term in info.name.upper():
                results.append(info)

        return sorted(results, key=lambda x: x.avg_rating, reverse=True)

    def force_refresh(self) -> bool:
        """Force a cache refresh regardless of file dates"""
        print("Force refreshing opponents cache...")
        return self.refresh_cache()


def main():
    """Test the opponent cache manager"""
    cache = OpponentCacheManager()

    # Force refresh to test
    cache.force_refresh()

    # Get statistics
    stats = cache.get_statistics()
    print("\n=== OPPONENT CACHE STATISTICS ===")
    print(f"Total opponents: {stats.get('total_opponents', 0)}")
    print(f"Total games: {stats.get('total_games', 0)}")
    print(f"Win percentage: {stats.get('win_percentage', 0):.1f}%")
    print(f"Average opponent rating: {stats.get('avg_opponent_rating', 0):.0f}")

    print("\nRating distribution:")
    for rating_range, count in stats.get('rating_distribution', {}).items():
        print(f"  {rating_range}: {count} opponents")

    # Show top opponents
    print("\n=== TOP 10 OPPONENTS BY RATING ===")
    top_opponents = cache.get_top_opponents_by_rating(10)
    for i, opp in enumerate(top_opponents, 1):
        print(f"{i:2d}. {opp.name} (avg: {opp.avg_rating:.0f}, games: {opp.total_games})")

    # Show frequent opponents
    print("\n=== FREQUENT OPPONENTS (2+ games) ===")
    frequent = cache.get_frequent_opponents(2)
    for name, info in sorted(frequent.items(), key=lambda x: x[1].total_games, reverse=True)[:10]:
        win_rate = (info.wins_against / info.total_games * 100) if info.total_games > 0 else 0
        print(f"{info.name}: {info.total_games} games, {win_rate:.1f}% win rate")


if __name__ == "__main__":
    main()