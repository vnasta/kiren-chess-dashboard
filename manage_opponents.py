#!/usr/bin/env python3
"""
CLI tool to manage Kiren's opponent cache
"""

import argparse
from src.opponent_cache import OpponentCacheManager

def main():
    parser = argparse.ArgumentParser(description="Manage Kiren's opponent cache")
    parser.add_argument('command', choices=['refresh', 'stats', 'search', 'top', 'frequent'],
                       help='Command to execute')
    parser.add_argument('--query', '-q', type=str, help='Search query for opponent names')
    parser.add_argument('--limit', '-l', type=int, default=10, help='Limit results (default: 10)')
    parser.add_argument('--min-games', '-m', type=int, default=2, help='Minimum games for frequent opponents')

    args = parser.parse_args()

    cache = OpponentCacheManager()

    if args.command == 'refresh':
        print("🔄 Refreshing opponent cache...")
        success = cache.force_refresh()
        if success:
            print("✅ Cache refreshed successfully!")
            stats = cache.get_statistics()
            print(f"Cached {stats['total_opponents']} opponents from {stats['total_games']} games")
        else:
            print("❌ Failed to refresh cache")

    elif args.command == 'stats':
        stats = cache.get_statistics()
        print("\n=== OPPONENT CACHE STATISTICS ===")
        print(f"Total opponents: {stats.get('total_opponents', 0)}")
        print(f"Total games: {stats.get('total_games', 0)}")
        print(f"Win percentage: {stats.get('win_percentage', 0):.1f}%")
        print(f"Average opponent rating: {stats.get('avg_opponent_rating', 0):.0f}")
        print(f"Last updated: {stats.get('last_updated', 'Never')}")

        print("\nRating distribution:")
        for rating_range, count in stats.get('rating_distribution', {}).items():
            print(f"  {rating_range}: {count} opponents")

    elif args.command == 'search':
        if not args.query:
            print("❌ Please provide a search query with --query")
            return

        results = cache.search_opponents(args.query)
        print(f"\n=== SEARCH RESULTS FOR '{args.query}' ===")

        if not results:
            print("No opponents found")
            return

        for i, opp in enumerate(results[:args.limit], 1):
            win_rate = (opp.wins_against / opp.total_games * 100) if opp.total_games > 0 else 0
            print(f"{i:2d}. {opp.name}")
            print(f"    Rating: {opp.avg_rating:.0f} | Games: {opp.total_games} | Win rate: {win_rate:.1f}%")
            print(f"    Last faced: {opp.last_faced}")

    elif args.command == 'top':
        top_opponents = cache.get_top_opponents_by_rating(args.limit)
        print(f"\n=== TOP {args.limit} OPPONENTS BY RATING ===")

        for i, opp in enumerate(top_opponents, 1):
            win_rate = (opp.wins_against / opp.total_games * 100) if opp.total_games > 0 else 0
            print(f"{i:2d}. {opp.name} ({opp.avg_rating:.0f})")
            print(f"    Games: {opp.total_games} | Win rate: {win_rate:.1f}% | Last faced: {opp.last_faced}")

    elif args.command == 'frequent':
        frequent = cache.get_frequent_opponents(args.min_games)
        print(f"\n=== FREQUENT OPPONENTS ({args.min_games}+ games) ===")

        sorted_frequent = sorted(frequent.items(), key=lambda x: x[1].total_games, reverse=True)
        for i, (name, info) in enumerate(sorted_frequent[:args.limit], 1):
            win_rate = (info.wins_against / info.total_games * 100) if info.total_games > 0 else 0
            print(f"{i:2d}. {info.name}")
            print(f"    Games: {info.total_games} | Win rate: {win_rate:.1f}% | Avg rating: {info.avg_rating:.0f}")
            print(f"    Last faced: {info.last_faced}")

if __name__ == "__main__":
    main()