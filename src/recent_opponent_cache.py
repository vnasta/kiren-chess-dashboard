#!/usr/bin/env python3
"""
Recent Opponent Cache Manager - Focus on Last 10 Tournaments
Specialized caching for Kiren's most recent opponents
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.opponent_cache import OpponentCacheManager, OpponentInfo


class RecentOpponentCache(OpponentCacheManager):
    """Specialized cache manager for recent tournaments only"""

    def __init__(self, cache_file: str = "data/recent_opponents_cache.json", max_tournaments: int = 10):
        self.max_tournaments = max_tournaments
        super().__init__(cache_file)

        # Prioritize cleaner data sources first
        self.source_files = [
            "data/real_kiren_tournaments.json",
            "data/kiren_real_multiyear.json",
            "data/kiren_multiyear_tournaments.json",
            "data/kiren_tournaments.json"
        ]

    def get_recent_tournaments(self, all_tournaments: List[Dict]) -> List[Dict]:
        """Get the most recent N tournaments sorted by date"""
        # Sort tournaments by date (most recent first)
        sorted_tournaments = sorted(
            all_tournaments,
            key=lambda x: x.get('date', ''),
            reverse=True
        )

        # Return the most recent tournaments
        recent = sorted_tournaments[:self.max_tournaments]
        print(f"Selected {len(recent)} most recent tournaments:")
        for i, t in enumerate(recent, 1):
            print(f"  {i}. {t.get('name', 'Unknown')} ({t.get('date', 'No date')})")

        return recent

    def refresh_recent_cache(self) -> bool:
        """Refresh cache with only the most recent tournaments"""
        print(f"Refreshing recent opponent cache (last {self.max_tournaments} tournaments)...")
        self.opponents_cache.clear()

        all_tournaments = []

        # Load all tournaments from source files
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

        if not all_tournaments:
            print("No tournaments found!")
            return False

        # Get only recent tournaments
        recent_tournaments = self.get_recent_tournaments(all_tournaments)

        if recent_tournaments:
            self.extract_opponents_from_tournaments(recent_tournaments)
            return self.save_cache()

        return False

    def get_recent_statistics(self) -> Dict:
        """Get statistics specifically for recent tournaments"""
        if self.needs_refresh():
            self.refresh_recent_cache()

        stats = self.get_statistics()
        if stats:
            stats['tournaments_analyzed'] = self.max_tournaments
            stats['cache_type'] = 'recent_only'

        return stats

    def get_tournament_breakdown(self) -> List[Dict]:
        """Get a breakdown of opponents by tournament"""
        if self.needs_refresh():
            self.refresh_recent_cache()

        # Reload recent tournaments to get breakdown
        all_tournaments = []
        for source_file in self.source_files:
            if os.path.exists(source_file):
                try:
                    with open(source_file, 'r') as f:
                        tournaments = json.load(f)
                        if isinstance(tournaments, list):
                            all_tournaments.extend(tournaments)
                except:
                    continue

        recent_tournaments = self.get_recent_tournaments(all_tournaments)

        breakdown = []
        for tournament in recent_tournaments:
            opponents = tournament.get('opponents', [])
            clean_opponents = []

            for opp in opponents:
                name = self.clean_opponent_name(opp.get('name', ''))
                if name:
                    clean_opponents.append({
                        'name': name,
                        'rating': opp.get('rating', 0),
                        'result': opp.get('result', ''),
                        'round': opp.get('round', 0)
                    })

            breakdown.append({
                'tournament_name': tournament.get('name', 'Unknown'),
                'date': tournament.get('date', ''),
                'total_opponents': len(clean_opponents),
                'opponents': clean_opponents,
                'score': tournament.get('score', ''),
                'rating_change': tournament.get('rating_after', 0) - tournament.get('rating_before', 0)
            })

        return breakdown


def main():
    """Test the recent opponent cache manager"""
    print("🎯 RECENT OPPONENT CACHE MANAGER")
    print("=" * 50)

    # Test with last 10 tournaments
    recent_cache = RecentOpponentCache(max_tournaments=10)

    # Force refresh to get recent data
    print("\n🔄 Refreshing cache for last 10 tournaments...")
    success = recent_cache.refresh_recent_cache()

    if not success:
        print("❌ Failed to refresh cache")
        return

    # Get statistics
    stats = recent_cache.get_recent_statistics()
    print(f"\n📊 RECENT TOURNAMENTS STATISTICS")
    print(f"Tournaments analyzed: {stats.get('tournaments_analyzed', 0)}")
    print(f"Total opponents: {stats.get('total_opponents', 0)}")
    print(f"Total games: {stats.get('total_games', 0)}")
    print(f"Win percentage: {stats.get('win_percentage', 0):.1f}%")
    print(f"Average opponent rating: {stats.get('avg_opponent_rating', 0):.0f}")

    print(f"\nRating distribution:")
    for rating_range, count in stats.get('rating_distribution', {}).items():
        print(f"  {rating_range}: {count} opponents")

    # Show top opponents from recent tournaments
    print(f"\n🏆 TOP 10 RECENT OPPONENTS BY RATING")
    top_opponents = recent_cache.get_top_opponents_by_rating(10)
    for i, opp in enumerate(top_opponents, 1):
        win_rate = (opp.wins_against / opp.total_games * 100) if opp.total_games > 0 else 0
        print(f"{i:2d}. {opp.name}")
        print(f"    Rating: {opp.avg_rating:.0f} | Games: {opp.total_games} | Win rate: {win_rate:.1f}%")

    # Show tournament breakdown
    print(f"\n📋 TOURNAMENT BREAKDOWN")
    breakdown = recent_cache.get_tournament_breakdown()
    for i, tournament in enumerate(breakdown, 1):
        print(f"\n{i}. {tournament['tournament_name']} ({tournament['date']})")
        print(f"   Score: {tournament['score']} | Opponents: {tournament['total_opponents']} | Rating change: {tournament['rating_change']:+d}")

        # Show first few opponents
        for j, opp in enumerate(tournament['opponents'][:3], 1):
            result_color = "W" if opp['result'] == 'W' else "L" if opp['result'] == 'L' else "D"
            print(f"   R{opp['round']}: {opp['name']} ({opp['rating']}) - {result_color}")

        if len(tournament['opponents']) > 3:
            print(f"   ... and {len(tournament['opponents']) - 3} more opponents")


if __name__ == "__main__":
    main()