#!/usr/bin/env python3
"""
CLI tool to manage Kiren's recent opponent cache (last 10 tournaments)
"""

import argparse
from src.recent_opponent_cache import RecentOpponentCache

def main():
    parser = argparse.ArgumentParser(description="Manage Kiren's recent opponent cache (last 10 tournaments)")
    parser.add_argument('command', choices=['refresh', 'stats', 'breakdown', 'top', 'tournaments'],
                       help='Command to execute')
    parser.add_argument('--tournaments', '-t', type=int, default=10,
                       help='Number of recent tournaments to analyze (default: 10)')
    parser.add_argument('--limit', '-l', type=int, default=10, help='Limit results (default: 10)')

    args = parser.parse_args()

    cache = RecentOpponentCache(max_tournaments=args.tournaments)

    if args.command == 'refresh':
        print(f"🔄 Refreshing cache for last {args.tournaments} tournaments...")
        success = cache.refresh_recent_cache()
        if success:
            print("✅ Recent cache refreshed successfully!")
            stats = cache.get_recent_statistics()
            print(f"Cached {stats.get('total_opponents', 0)} opponents from {stats.get('total_games', 0)} games")
            print(f"Analyzed {stats.get('tournaments_analyzed', 0)} most recent tournaments")
        else:
            print("❌ Failed to refresh recent cache")

    elif args.command == 'stats':
        stats = cache.get_recent_statistics()
        print(f"\n=== RECENT OPPONENT CACHE STATISTICS (LAST {args.tournaments} TOURNAMENTS) ===")
        print(f"Tournaments analyzed: {stats.get('tournaments_analyzed', 0)}")
        print(f"Total opponents: {stats.get('total_opponents', 0)}")
        print(f"Total games: {stats.get('total_games', 0)}")
        print(f"Win percentage: {stats.get('win_percentage', 0):.1f}%")
        print(f"Average opponent rating: {stats.get('avg_opponent_rating', 0):.0f}")
        print(f"Last updated: {stats.get('last_updated', 'Never')}")

        print("\nRating distribution:")
        for rating_range, count in stats.get('rating_distribution', {}).items():
            print(f"  {rating_range}: {count} opponents")

    elif args.command == 'top':
        top_opponents = cache.get_top_opponents_by_rating(args.limit)
        print(f"\n=== TOP {args.limit} RECENT OPPONENTS BY RATING ===")

        for i, opp in enumerate(top_opponents, 1):
            win_rate = (opp.wins_against / opp.total_games * 100) if opp.total_games > 0 else 0
            print(f"{i:2d}. {opp.name} ({opp.avg_rating:.0f})")
            print(f"    Games: {opp.total_games} | Win rate: {win_rate:.1f}% | Last faced: {opp.last_faced}")

    elif args.command == 'breakdown':
        breakdown = cache.get_tournament_breakdown()
        print(f"\n=== TOURNAMENT BREAKDOWN (LAST {len(breakdown)} TOURNAMENTS) ===")

        for i, tournament in enumerate(breakdown, 1):
            print(f"\n{i}. {tournament['tournament_name']}")
            print(f"   Date: {tournament['date']}")
            print(f"   Score: {tournament['score']}")
            print(f"   Opponents: {tournament['total_opponents']}")
            print(f"   Rating change: {tournament['rating_change']:+d}")

            # Show top opponents from this tournament
            sorted_opponents = sorted(tournament['opponents'],
                                   key=lambda x: x['rating'], reverse=True)

            print(f"   Top opponents:")
            for j, opp in enumerate(sorted_opponents[:3], 1):
                result_emoji = "🏆" if opp['result'] == 'W' else "❌" if opp['result'] == 'L' else "🤝"
                print(f"     {j}. {opp['name']} ({opp['rating']}) - {opp['result']} {result_emoji}")

            if len(sorted_opponents) > 3:
                print(f"     ... and {len(sorted_opponents) - 3} more")

    elif args.command == 'tournaments':
        breakdown = cache.get_tournament_breakdown()
        print(f"\n=== RECENT TOURNAMENTS SUMMARY ===")

        total_opponents = 0
        total_wins = 0
        total_games = 0

        for i, tournament in enumerate(breakdown, 1):
            wins = sum(1 for opp in tournament['opponents'] if opp['result'] == 'W')
            games = len(tournament['opponents'])
            win_rate = (wins / games * 100) if games > 0 else 0

            total_opponents += games
            total_wins += wins
            total_games += games

            print(f"{i:2d}. {tournament['tournament_name'][:40]:<40} | {tournament['date']} | {wins}/{games} ({win_rate:.1f}%)")

        overall_win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
        print(f"\n📊 Overall: {total_wins}/{total_games} ({overall_win_rate:.1f}%) across {len(breakdown)} tournaments")


if __name__ == "__main__":
    main()