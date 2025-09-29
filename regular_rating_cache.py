#!/usr/bin/env python3
"""
Regular Rating Cache System
Focus on standard/classical time control ratings for all opponents
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class RegularRatedOpponent:
    """Opponent profile focused on regular/classical ratings"""
    name: str
    title: Optional[str]

    # Regular rating info (standard time control)
    regular_ratings: List[int]  # All regular ratings faced
    avg_regular_rating: float
    highest_regular_rating: int
    lowest_regular_rating: int

    # Game results in regular time control games
    total_regular_games: int
    kiren_wins: int
    kiren_losses: int
    kiren_draws: int
    kiren_win_rate: float

    # Tournament details for regular games only
    regular_tournaments: List[str]
    regular_dates: List[str]
    regular_results: List[str]

    # Performance analysis
    rating_performance: float  # Expected vs actual performance
    upset_wins: int  # Wins against higher regular-rated
    expected_draws: int  # Draws vs similar rated

    # Timeline
    first_regular_game: str
    last_regular_game: str


def extract_title_from_name(name: str) -> tuple[str, Optional[str]]:
    """Extract chess title from opponent name"""
    titles = ['GM', 'IM', 'FM', 'WGM', 'WIM', 'WFM', 'EXPERT', 'MASTER']

    name_upper = name.upper()
    for title in titles:
        if name_upper.startswith(title + ' '):
            clean_name = name[len(title):].strip()
            return clean_name, title

    return name, None


def clean_opponent_name(name: str) -> str:
    """Clean opponent names"""
    if not name or len(name) < 3:
        return ""

    # Remove HTML artifacts
    invalid_patterns = [
        "Click on a Section Name", "The ratings shown on this page",
        "Section(s),", "Players", "not official published ratings"
    ]

    for pattern in invalid_patterns:
        if pattern.lower() in name.lower():
            return ""

    import re
    name = re.sub(r'\s+', ' ', name).strip()

    if len(name) > 60 or not re.search(r'[A-Za-z]', name):
        return ""

    return name.strip('.,;:*')


def is_regular_time_control(tournament_name: str, section: str = "") -> bool:
    """Determine if tournament uses regular/classical time control"""
    tournament_lower = tournament_name.lower()
    section_lower = section.lower()

    # Indicators of NON-regular time controls
    fast_indicators = [
        'blitz', 'rapid', 'quick', 'speed', 'action', 'bullet',
        'lightning', 'fast', '15+', '30+', 'g/15', 'g/30', 'g/60'
    ]

    # Check if it's a fast time control tournament
    for indicator in fast_indicators:
        if indicator in tournament_lower or indicator in section_lower:
            return False

    # Indicators of regular time controls
    regular_indicators = [
        'classical', 'standard', 'regular', 'open', 'championship',
        'invitational', 'masters', 'international', 'national'
    ]

    # If explicitly regular, return True
    for indicator in regular_indicators:
        if indicator in tournament_lower:
            return True

    # Default assumption: if no fast indicators, likely regular
    return True


def load_tournament_data() -> List[Dict]:
    """Load clean tournament data"""
    files = [
        "data/real_kiren_tournaments.json",
        "data/kiren_real_multiyear.json"
    ]

    all_tournaments = []
    for file_path in files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    tournaments = json.load(f)
                    if isinstance(tournaments, list):
                        all_tournaments.extend(tournaments)
                        print(f"📁 Loaded {len(tournaments)} tournaments from {file_path}")
            except Exception as e:
                print(f"❌ Error loading {file_path}: {e}")

    return all_tournaments


def filter_regular_tournaments(tournaments: List[Dict], limit: int = 10) -> List[Dict]:
    """Filter to only regular time control tournaments"""
    regular_tournaments = []

    print(f"\n🔍 Filtering for regular time control tournaments...")

    for tournament in tournaments:
        name = tournament.get('name', '')
        section = tournament.get('section', '')

        if is_regular_time_control(name, section):
            regular_tournaments.append(tournament)
            print(f"✅ Regular: {name}")
        else:
            print(f"❌ Fast TC: {name}")

    # Sort by date and take most recent
    regular_tournaments.sort(key=lambda x: x.get('date', ''), reverse=True)

    if limit:
        regular_tournaments = regular_tournaments[:limit]

    print(f"\n📊 Selected {len(regular_tournaments)} regular tournaments:")
    for i, t in enumerate(regular_tournaments, 1):
        opponent_count = len(t.get('opponents', []))
        print(f"  {i:2d}. {t.get('name', 'Unknown'):<45} ({t.get('date', 'No date')}) - {opponent_count} opponents")

    return regular_tournaments


def create_regular_rating_profiles(tournaments: List[Dict]) -> Dict[str, RegularRatedOpponent]:
    """Create profiles focusing on regular ratings only"""
    opponent_profiles = {}

    print(f"\n🎯 Creating regular rating profiles...")

    total_regular_games = 0

    for tournament in tournaments:
        tournament_name = tournament.get('name', 'Unknown Tournament')
        tournament_date = tournament.get('date', '')

        print(f"\n📊 Processing regular tournament: {tournament_name}")

        for opponent_data in tournament.get('opponents', []):
            raw_name = opponent_data.get('name', '').strip()
            if not raw_name:
                continue

            clean_name = clean_opponent_name(raw_name)
            if not clean_name:
                continue

            # Extract title and clean name
            clean_name, title = extract_title_from_name(clean_name)

            rating = opponent_data.get('rating', 0)
            result = opponent_data.get('result', '').upper()

            if rating == 0:  # Skip if no rating available
                continue

            total_regular_games += 1

            # Create or update opponent profile
            if clean_name not in opponent_profiles:
                opponent_profiles[clean_name] = RegularRatedOpponent(
                    name=clean_name,
                    title=title,
                    regular_ratings=[],
                    avg_regular_rating=0.0,
                    highest_regular_rating=0,
                    lowest_regular_rating=9999,
                    total_regular_games=0,
                    kiren_wins=0,
                    kiren_losses=0,
                    kiren_draws=0,
                    kiren_win_rate=0.0,
                    regular_tournaments=[],
                    regular_dates=[],
                    regular_results=[],
                    rating_performance=0.0,
                    upset_wins=0,
                    expected_draws=0,
                    first_regular_game='',
                    last_regular_game=''
                )

            profile = opponent_profiles[clean_name]

            # Update profile with regular rating data
            profile.regular_ratings.append(rating)
            profile.regular_tournaments.append(tournament_name)
            profile.regular_dates.append(tournament_date)
            profile.regular_results.append(result)

            # Update game counts
            profile.total_regular_games += 1
            if result == 'W':  # Kiren won
                profile.kiren_wins += 1
            elif result == 'L':  # Kiren lost
                profile.kiren_losses += 1
            elif result == 'D':  # Draw
                profile.kiren_draws += 1

            # Update timeline
            if not profile.first_regular_game or tournament_date < profile.first_regular_game:
                profile.first_regular_game = tournament_date
            if not profile.last_regular_game or tournament_date > profile.last_regular_game:
                profile.last_regular_game = tournament_date

            # Update title if we found a better one
            if title and (not profile.title or len(title) > len(profile.title or '')):
                profile.title = title

    # Calculate derived statistics
    print(f"\n🧮 Calculating regular rating statistics...")

    for name, profile in opponent_profiles.items():
        if profile.regular_ratings:
            profile.avg_regular_rating = sum(profile.regular_ratings) / len(profile.regular_ratings)
            profile.highest_regular_rating = max(profile.regular_ratings)
            profile.lowest_regular_rating = min(profile.regular_ratings)

        # Calculate win rate
        if profile.total_regular_games > 0:
            profile.kiren_win_rate = (profile.kiren_wins / profile.total_regular_games) * 100

        # Count upsets (simplified - assume Kiren ~2200 regular rating)
        kiren_estimated_regular = 2200
        for i, result in enumerate(profile.regular_results):
            if i < len(profile.regular_ratings):
                opp_rating = profile.regular_ratings[i]
                if result == 'W' and kiren_estimated_regular < opp_rating:
                    profile.upset_wins += 1
                elif result == 'D' and abs(kiren_estimated_regular - opp_rating) <= 100:
                    profile.expected_draws += 1

    print(f"✅ Created {len(opponent_profiles)} regular rating profiles")
    print(f"📊 Total regular games: {total_regular_games}")

    return opponent_profiles


def save_regular_rating_cache(profiles: Dict[str, RegularRatedOpponent],
                             filename: str = "data/regular_rating_cache.json"):
    """Save regular rating cache"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        cache_data = {
            'created': datetime.now().isoformat(),
            'source': 'regular_time_control_games_only',
            'total_opponents': len(profiles),
            'total_regular_games': sum(p.total_regular_games for p in profiles.values()),
            'focus': 'standard_classical_ratings',
            'opponents': {name: asdict(profile) for name, profile in profiles.items()}
        }

        with open(filename, 'w') as f:
            json.dump(cache_data, f, indent=2)

        print(f"💾 Saved regular rating cache to {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to save cache: {e}")
        return False


def generate_regular_rating_report(profiles: Dict[str, RegularRatedOpponent]):
    """Generate report focused on regular ratings"""
    if not profiles:
        print("❌ No regular rating profiles to analyze")
        return

    total_opponents = len(profiles)
    total_games = sum(p.total_regular_games for p in profiles.values())
    total_wins = sum(p.kiren_wins for p in profiles.values())
    total_losses = sum(p.kiren_losses for p in profiles.values())
    total_draws = sum(p.kiren_draws for p in profiles.values())

    win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
    avg_opponent_rating = sum(p.avg_regular_rating for p in profiles.values()) / total_opponents

    print(f"\n" + "="*80)
    print(f"🏆 REGULAR TIME CONTROL RATING ANALYSIS")
    print(f"="*80)

    print(f"\n📊 OVERALL REGULAR RATING STATISTICS:")
    print(f"  Total opponents (regular games): {total_opponents}")
    print(f"  Total regular games: {total_games}")
    print(f"  Kiren's record: {total_wins}W-{total_losses}L-{total_draws}D")
    print(f"  Win percentage: {win_rate:.1f}%")
    print(f"  Average opponent regular rating: {avg_opponent_rating:.0f}")

    # Regular rating distribution
    rating_ranges = {
        '2400+': len([p for p in profiles.values() if p.avg_regular_rating >= 2400]),
        '2200-2399': len([p for p in profiles.values() if 2200 <= p.avg_regular_rating < 2400]),
        '2000-2199': len([p for p in profiles.values() if 2000 <= p.avg_regular_rating < 2200]),
        '1800-1999': len([p for p in profiles.values() if 1800 <= p.avg_regular_rating < 2000]),
        '<1800': len([p for p in profiles.values() if p.avg_regular_rating < 1800])
    }

    print(f"\n📈 REGULAR RATING DISTRIBUTION:")
    for range_name, count in rating_ranges.items():
        percentage = (count / total_opponents * 100) if total_opponents > 0 else 0
        print(f"  {range_name}: {count} opponents ({percentage:.1f}%)")

    # Top regular-rated opponents
    print(f"\n🏆 TOP 15 REGULAR-RATED OPPONENTS:")
    top_opponents = sorted(profiles.values(), key=lambda x: x.avg_regular_rating, reverse=True)[:15]

    for i, opp in enumerate(top_opponents, 1):
        title_str = f" ({opp.title})" if opp.title else ""
        result_summary = f"{opp.kiren_wins}W-{opp.kiren_losses}L-{opp.kiren_draws}D"

        print(f"  {i:2d}. {opp.name:<35}{title_str:<6} {opp.avg_regular_rating:.0f} | "
              f"{opp.total_regular_games} games: {result_summary} ({opp.kiren_win_rate:.1f}%)")

    # Upset analysis
    total_upsets = sum(p.upset_wins for p in profiles.values())
    print(f"\n⚡ REGULAR RATING UPSET ANALYSIS:")
    print(f"  Total upset wins: {total_upsets}")

    if total_upsets > 0:
        print(f"  Notable upsets:")
        upset_opponents = [p for p in profiles.values() if p.upset_wins > 0]
        upset_opponents.sort(key=lambda x: x.avg_regular_rating, reverse=True)

        for opp in upset_opponents[:10]:
            print(f"    Beat {opp.name} ({opp.avg_regular_rating:.0f}) - {opp.upset_wins} time(s)")


def main():
    """Main function for regular rating caching"""
    print("🎯 REGULAR TIME CONTROL RATING CACHE")
    print("="*50)

    # Load tournament data
    all_tournaments = load_tournament_data()
    if not all_tournaments:
        print("❌ No tournament data found!")
        return

    # Filter to regular time control tournaments only
    regular_tournaments = filter_regular_tournaments(all_tournaments, limit=None)  # No limit, get all regular

    if not regular_tournaments:
        print("❌ No regular time control tournaments found!")
        return

    # Create regular rating profiles
    regular_profiles = create_regular_rating_profiles(regular_tournaments)

    if not regular_profiles:
        print("❌ No regular rating profiles created!")
        return

    # Save cache
    save_regular_rating_cache(regular_profiles)

    # Generate report
    generate_regular_rating_report(regular_profiles)

    print(f"\n✅ Regular rating caching complete!")
    print(f"📁 Cache saved to: data/regular_rating_cache.json")


if __name__ == "__main__":
    main()