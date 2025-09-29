#!/usr/bin/env python3
"""
Comprehensive Opponent Cache - All Opponents from Last 10 Tournaments
Creates detailed profiles for every single opponent faced
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class DetailedOpponentProfile:
    """Comprehensive opponent profile with all encounter details"""
    name: str
    uscf_id: Optional[str]
    title: Optional[str]  # GM, IM, FM, etc.

    # Rating information
    ratings_faced: List[int]
    avg_rating: float
    highest_rating: int
    lowest_rating: int

    # Game results
    total_encounters: int
    wins_against_kiren: int
    losses_against_kiren: int
    draws_against_kiren: int
    kiren_win_rate: float

    # Encounter details
    tournaments_met: List[str]
    dates_faced: List[str]
    rounds_played: List[int]
    results_history: List[str]

    # Performance analysis
    kiren_rating_when_faced: List[int]
    rating_difference_avg: float
    upset_victories: int  # wins against higher-rated
    expected_losses: int  # losses to higher-rated

    # Additional info
    first_encounter: str
    last_encounter: str
    encounter_span_days: int
    colors_played: List[str]  # if available
    opening_patterns: List[str]  # if available


def extract_title_from_name(name: str) -> tuple[str, Optional[str]]:
    """Extract chess title from opponent name"""
    titles = ['GM', 'IM', 'FM', 'WGM', 'WIM', 'WFM', 'EXPERT', 'MASTER', 'CLASS A']

    for title in titles:
        if name.upper().startswith(title + ' '):
            clean_name = name[len(title):].strip()
            return clean_name, title

    return name, None


def clean_opponent_name(name: str) -> str:
    """Enhanced name cleaning"""
    if not name:
        return ""

    # Remove HTML artifacts
    invalid_patterns = [
        "Click on a Section Name", "The ratings shown on this page",
        "Section(s),", "Players", "not official published ratings",
        "may change from time to time", "Using them for pairing purposes",
        "should only be done if this has been advertised",
        "advance publicity and is announced"
    ]

    for pattern in invalid_patterns:
        if pattern.lower() in name.lower():
            return ""

    import re
    name = re.sub(r'\s+', ' ', name).strip()

    if len(name) < 3 or len(name) > 60:
        return ""

    if not re.search(r'[A-Za-z]', name):
        return ""

    name = name.strip('.,;:*')
    return name


def load_tournament_data() -> List[Dict]:
    """Load all tournament data"""
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


def get_recent_tournaments(tournaments: List[Dict], count: int = 10) -> List[Dict]:
    """Get most recent tournaments"""
    sorted_tournaments = sorted(
        tournaments,
        key=lambda x: x.get('date', ''),
        reverse=True
    )

    recent = sorted_tournaments[:count]
    print(f"\n📅 Selected {len(recent)} most recent tournaments:")
    for i, t in enumerate(recent, 1):
        opponent_count = len(t.get('opponents', []))
        print(f"  {i:2d}. {t.get('name', 'Unknown'):<45} ({t.get('date', 'No date')}) - {opponent_count} opponents")

    return recent


def create_comprehensive_opponent_profiles(tournaments: List[Dict]) -> Dict[str, DetailedOpponentProfile]:
    """Create detailed profiles for ALL opponents"""
    opponent_profiles = {}

    print(f"\n🔍 Creating comprehensive profiles for ALL opponents...")

    total_games = 0
    unique_opponents = set()

    for tournament in tournaments:
        tournament_name = tournament.get('name', 'Unknown Tournament')
        tournament_date = tournament.get('date', '')
        kiren_rating_before = tournament.get('rating_before', 0)

        print(f"\n📊 Processing: {tournament_name}")

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
            round_num = opponent_data.get('round', 0)

            unique_opponents.add(clean_name)
            total_games += 1

            # Create or update opponent profile
            if clean_name not in opponent_profiles:
                opponent_profiles[clean_name] = DetailedOpponentProfile(
                    name=clean_name,
                    uscf_id=None,
                    title=title,
                    ratings_faced=[],
                    avg_rating=0.0,
                    highest_rating=0,
                    lowest_rating=9999,
                    total_encounters=0,
                    wins_against_kiren=0,
                    losses_against_kiren=0,
                    draws_against_kiren=0,
                    kiren_win_rate=0.0,
                    tournaments_met=[],
                    dates_faced=[],
                    rounds_played=[],
                    results_history=[],
                    kiren_rating_when_faced=[],
                    rating_difference_avg=0.0,
                    upset_victories=0,
                    expected_losses=0,
                    first_encounter='',
                    last_encounter='',
                    encounter_span_days=0,
                    colors_played=[],
                    opening_patterns=[]
                )

            profile = opponent_profiles[clean_name]

            # Update profile data
            profile.ratings_faced.append(rating)
            profile.tournaments_met.append(tournament_name)
            profile.dates_faced.append(tournament_date)
            profile.rounds_played.append(round_num)
            profile.results_history.append(result)
            profile.kiren_rating_when_faced.append(kiren_rating_before)

            # Update encounter counts
            profile.total_encounters += 1
            if result == 'W':  # Kiren won
                profile.losses_against_kiren += 1
            elif result == 'L':  # Kiren lost
                profile.wins_against_kiren += 1
            elif result == 'D':  # Draw
                profile.draws_against_kiren += 1

            # Update first/last encounter
            if not profile.first_encounter or tournament_date < profile.first_encounter:
                profile.first_encounter = tournament_date
            if not profile.last_encounter or tournament_date > profile.last_encounter:
                profile.last_encounter = tournament_date

            # Update title if we found a better one
            if title and (not profile.title or len(title) > len(profile.title or '')):
                profile.title = title

    # Calculate derived statistics
    print(f"\n🧮 Calculating comprehensive statistics...")

    for name, profile in opponent_profiles.items():
        if profile.ratings_faced:
            profile.avg_rating = sum(profile.ratings_faced) / len(profile.ratings_faced)
            profile.highest_rating = max(profile.ratings_faced)
            profile.lowest_rating = min(profile.ratings_faced)

        # Calculate Kiren's win rate against this opponent
        total_games_vs_opponent = profile.total_encounters
        if total_games_vs_opponent > 0:
            profile.kiren_win_rate = (profile.losses_against_kiren / total_games_vs_opponent) * 100

        # Calculate average rating difference
        if profile.kiren_rating_when_faced and profile.ratings_faced:
            rating_diffs = [k_rating - opp_rating for k_rating, opp_rating in
                           zip(profile.kiren_rating_when_faced, profile.ratings_faced)]
            profile.rating_difference_avg = sum(rating_diffs) / len(rating_diffs)

        # Count upsets and expected results
        for i, result in enumerate(profile.results_history):
            if i < len(profile.kiren_rating_when_faced) and i < len(profile.ratings_faced):
                kiren_rating = profile.kiren_rating_when_faced[i]
                opp_rating = profile.ratings_faced[i]

                if result == 'W' and kiren_rating < opp_rating:  # Kiren won vs higher rated
                    profile.upset_victories += 1
                elif result == 'L' and kiren_rating > opp_rating:  # Kiren lost to lower rated
                    profile.expected_losses += 1

        # Calculate encounter span
        if profile.first_encounter and profile.last_encounter:
            try:
                from datetime import datetime
                first_date = datetime.strptime(profile.first_encounter, '%Y-%m-%d')
                last_date = datetime.strptime(profile.last_encounter, '%Y-%m-%d')
                profile.encounter_span_days = (last_date - first_date).days
            except:
                profile.encounter_span_days = 0

    print(f"✅ Created profiles for {len(opponent_profiles)} unique opponents")
    print(f"📊 Total games analyzed: {total_games}")

    return opponent_profiles


def save_comprehensive_cache(profiles: Dict[str, DetailedOpponentProfile],
                           filename: str = "data/comprehensive_opponents_cache.json"):
    """Save comprehensive opponent cache"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        cache_data = {
            'created': datetime.now().isoformat(),
            'source': 'comprehensive_last_10_tournaments',
            'total_opponents': len(profiles),
            'total_games': sum(p.total_encounters for p in profiles.values()),
            'opponents': {name: asdict(profile) for name, profile in profiles.items()}
        }

        with open(filename, 'w') as f:
            json.dump(cache_data, f, indent=2)

        print(f"💾 Saved comprehensive cache to {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to save cache: {e}")
        return False


def generate_detailed_report(profiles: Dict[str, DetailedOpponentProfile]):
    """Generate comprehensive analysis report"""
    if not profiles:
        print("❌ No opponent profiles to analyze")
        return

    total_opponents = len(profiles)
    total_games = sum(p.total_encounters for p in profiles.values())
    total_wins = sum(p.losses_against_kiren for p in profiles.values())  # Kiren's wins
    total_losses = sum(p.wins_against_kiren for p in profiles.values())  # Kiren's losses
    total_draws = sum(p.draws_against_kiren for p in profiles.values())

    overall_win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
    avg_opponent_rating = sum(p.avg_rating for p in profiles.values()) / total_opponents

    print(f"\n" + "="*80)
    print(f"🏆 COMPREHENSIVE OPPONENT ANALYSIS - LAST 10 TOURNAMENTS")
    print(f"="*80)

    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total unique opponents: {total_opponents}")
    print(f"  Total games played: {total_games}")
    print(f"  Kiren's record: {total_wins}W-{total_losses}L-{total_draws}D")
    print(f"  Win percentage: {overall_win_rate:.1f}%")
    print(f"  Average opponent rating: {avg_opponent_rating:.0f}")

    # Title distribution
    title_counts = defaultdict(int)
    for profile in profiles.values():
        title = profile.title or 'Untitled'
        title_counts[title] += 1

    print(f"\n🎖️ OPPONENT TITLES:")
    for title, count in sorted(title_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {title}: {count} opponents")

    # Rating distribution
    rating_ranges = {
        '2600+': len([p for p in profiles.values() if p.avg_rating >= 2600]),
        '2400-2599': len([p for p in profiles.values() if 2400 <= p.avg_rating < 2600]),
        '2200-2399': len([p for p in profiles.values() if 2200 <= p.avg_rating < 2400]),
        '2000-2199': len([p for p in profiles.values() if 2000 <= p.avg_rating < 2200]),
        '<2000': len([p for p in profiles.values() if p.avg_rating < 2000])
    }

    print(f"\n📈 RATING DISTRIBUTION:")
    for range_name, count in rating_ranges.items():
        percentage = (count / total_opponents * 100) if total_opponents > 0 else 0
        print(f"  {range_name}: {count} opponents ({percentage:.1f}%)")

    # Top opponents by rating
    print(f"\n🏆 TOP 15 STRONGEST OPPONENTS:")
    top_opponents = sorted(profiles.values(), key=lambda x: x.avg_rating, reverse=True)[:15]

    for i, opp in enumerate(top_opponents, 1):
        win_rate = opp.kiren_win_rate
        encounters = opp.total_encounters
        title_str = f" ({opp.title})" if opp.title else ""

        result_summary = f"{opp.losses_against_kiren}W-{opp.wins_against_kiren}L-{opp.draws_against_kiren}D"

        print(f"  {i:2d}. {opp.name:<35}{title_str:<6} {opp.avg_rating:.0f} | "
              f"{encounters} games: {result_summary} ({win_rate:.1f}% for Kiren)")

    # Multiple encounters
    multiple_encounters = [p for p in profiles.values() if p.total_encounters > 1]
    if multiple_encounters:
        print(f"\n🔄 OPPONENTS FACED MULTIPLE TIMES:")
        multiple_encounters.sort(key=lambda x: x.total_encounters, reverse=True)

        for opp in multiple_encounters[:10]:
            result_summary = f"{opp.losses_against_kiren}W-{opp.wins_against_kiren}L-{opp.draws_against_kiren}D"
            print(f"  {opp.name:<35} {opp.total_encounters} times: {result_summary} "
                  f"({opp.kiren_win_rate:.1f}% for Kiren)")

    # Upset victories
    upset_wins = sum(p.upset_victories for p in profiles.values())
    total_upsets_possible = sum(1 for p in profiles.values() for i, result in enumerate(p.results_history)
                               if i < len(p.kiren_rating_when_faced) and i < len(p.ratings_faced)
                               and p.kiren_rating_when_faced[i] < p.ratings_faced[i])

    print(f"\n⚡ UPSET STATISTICS:")
    print(f"  Upset victories: {upset_wins}")
    print(f"  Games vs higher-rated: {total_upsets_possible}")
    if total_upsets_possible > 0:
        upset_rate = (upset_wins / total_upsets_possible * 100)
        print(f"  Upset rate: {upset_rate:.1f}%")


def main():
    """Main function for comprehensive opponent caching"""
    print("🎯 COMPREHENSIVE OPPONENT CACHING - LAST 10 TOURNAMENTS")
    print("="*65)

    # Load tournament data
    all_tournaments = load_tournament_data()
    if not all_tournaments:
        print("❌ No tournament data found!")
        return

    # Get recent tournaments
    recent_tournaments = get_recent_tournaments(all_tournaments, 10)
    if not recent_tournaments:
        print("❌ No recent tournaments found!")
        return

    # Create comprehensive profiles
    opponent_profiles = create_comprehensive_opponent_profiles(recent_tournaments)
    if not opponent_profiles:
        print("❌ No opponent profiles created!")
        return

    # Save cache
    save_comprehensive_cache(opponent_profiles)

    # Generate detailed report
    generate_detailed_report(opponent_profiles)

    print(f"\n✅ Comprehensive opponent caching complete!")
    print(f"📁 Cache saved to: data/comprehensive_opponents_cache.json")


if __name__ == "__main__":
    main()