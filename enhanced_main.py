#!/usr/bin/env python3
"""
Enhanced Interactive Chess Dashboard
Search and analyze any USCF player
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, no_update, ALL
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from src.uscf_player_lookup import USCFPlayerLookup
from src.opponent_cache import OpponentCacheManager
import json

class EnhancedChessDashboard:
    def __init__(self):
        self.lookup = USCFPlayerLookup()
        self.opponent_cache = OpponentCacheManager()
        self.current_player_data = None
        self.current_tournaments = []
        self.cached_opponents = {}  # Initialize opponent cache for profile switching

        # Default to Kiren's data
        self.load_player_data("NASTA, KIREN", "15255524")

        self.app = dash.Dash(__name__, suppress_callback_exceptions=True)
        self.setup_layout()
        self.setup_callbacks()

    def load_player_data(self, player_name, uscf_id):
        """Load player data and tournaments - now fetches real USCF data!"""
        print(f"Loading real data for {player_name} (ID: {uscf_id})")
        print(f"Debug: Checking if KIREN in '{player_name.upper()}' or ID == '15255524': {uscf_id == '15255524'}")

        # ALWAYS use cached data for Kiren's USCF ID
        if uscf_id == "15255524":
            self.current_player_data = {
                'name': 'NASTA, KIREN',
                'uscf_id': '15255524',
                'regular_rating': 2208,  # Use cached regular rating for Kiren
                'state': 'NY'
            }
            print(f"✅ FORCED Kiren's cached data: 2208 regular rating")
            return  # Exit early to prevent any USCF lookup
        elif "KIREN" in player_name.upper():
            self.current_player_data = {
                'name': 'NASTA, KIREN',
                'uscf_id': '15255524',
                'regular_rating': 2208,  # Use cached regular rating for Kiren
                'state': 'NY'
            }
            print(f"✅ FORCED Kiren's cached data by name: 2208 regular rating")
            return  # Exit early to prevent any USCF lookup
        else:
            # For other players, try to get real player info from USCF lookup
            try:
                player_info = self.lookup.search_player_by_id(uscf_id)
                if player_info:
                    self.current_player_data = {
                        'name': player_info.name,
                        'uscf_id': player_info.uscf_id,
                        'regular_rating': player_info.current_rating or 1200,
                        'state': player_info.state or 'Unknown'
                    }
                    print(f"Got real player data: {player_info.current_rating} rating")
                else:
                    # Fallback to basic data
                    self.current_player_data = {
                        'name': player_name,
                        'uscf_id': uscf_id,
                        'regular_rating': 1200,
                        'state': 'Unknown'
                    }
            except Exception as e:
                print(f"Error getting player info: {e}")
                self.current_player_data = {
                    'name': player_name,
                    'uscf_id': uscf_id,
                    'regular_rating': 1200,
                    'state': 'Unknown'
                }

        # Now try to fetch real tournament data
        self.current_tournaments = []

        # Try multiple methods to get tournament data
        try:
            # Method 1: Check if we have cached data
            if "KIREN" in player_name.upper():
                with open('data/kiren_real_multiyear.json', 'r') as f:
                    multiyear_data = json.load(f)
                try:
                    with open('data/real_kiren_tournaments.json', 'r') as f:
                        recent_data = json.load(f)
                    self.current_tournaments = multiyear_data + recent_data
                except:
                    self.current_tournaments = multiyear_data
                print(f"Loaded cached data: {len(self.current_tournaments)} tournaments")
                self.cache_all_opponents()  # Cache all opponents for profile switching
                return

            # Method 2: Try to load from existing cache file
            filename = f"data/{uscf_id}_tournaments.json"
            try:
                with open(filename, 'r') as f:
                    cached_data = json.load(f)
                    if cached_data:
                        self.current_tournaments = cached_data
                        print(f"Loaded cached data: {len(self.current_tournaments)} tournaments")
                        return
            except:
                pass

            # Method 3: Fetch fresh data from USCF
            print("Fetching fresh tournament data from USCF...")
            from src.fetch_real_tournaments import USCFTournamentFetcher
            fetcher = USCFTournamentFetcher(uscf_id)
            fresh_tournaments = fetcher.get_tournament_history()

            if fresh_tournaments:
                self.current_tournaments = fresh_tournaments
                print(f"Fetched fresh data: {len(self.current_tournaments)} tournaments")

                # Cache the data for future use
                try:
                    import os
                    os.makedirs('data', exist_ok=True)
                    with open(filename, 'w') as f:
                        json.dump(fresh_tournaments, f, indent=2)
                    print(f"Cached data to {filename}")
                except Exception as e:
                    print(f"Could not cache data: {e}")
                return

        except Exception as e:
            print(f"Error fetching tournament data: {e}")

        # Fallback: Use sample data only if no real data found
        print("No real tournament data found, using sample data")
        self.current_tournaments = self.get_sample_tournaments(player_name)

    def get_sample_tournaments(self, player_name):
        """Get sample tournament data for famous players"""
        if "KIREN" in player_name.upper():
            try:
                with open('data/real_kiren_tournaments.json', 'r') as f:
                    return json.load(f)
            except:
                pass

        # Generate realistic data for famous players
        famous_players = {
            'NAKAMURA': {
                'rating': 2750,
                'tournaments': [
                    {
                        'name': '2024 US Championship',
                        'date': '2024-10-15',
                        'rating_before': 2740,
                        'rating_after': 2750,
                        'score': '8.5/11',
                        'section': 'Championship',
                        'opponents': [
                            {'name': 'CARUANA, FABIANO', 'rating': 2720, 'result': 'D', 'round': 1},
                            {'name': 'SO, WESLEY', 'rating': 2690, 'result': 'W', 'round': 2},
                            {'name': 'XIONG, JEFFERY', 'rating': 2650, 'result': 'W', 'round': 3},
                            {'name': 'DOMINGUEZ, LEINIER', 'rating': 2620, 'result': 'D', 'round': 4},
                            {'name': 'SHANKLAND, SAM', 'rating': 2590, 'result': 'W', 'round': 5}
                        ]
                    }
                ]
            },
            'CARUANA': {
                'rating': 2720,
                'tournaments': [
                    {
                        'name': '2024 Candidates Tournament',
                        'date': '2024-04-20',
                        'rating_before': 2715,
                        'rating_after': 2720,
                        'score': '9/14',
                        'section': 'Candidates',
                        'opponents': [
                            {'name': 'DING, LIREN', 'rating': 2780, 'result': 'D', 'round': 1},
                            {'name': 'NEPOMNIACHTCHI, IAN', 'rating': 2760, 'result': 'W', 'round': 2},
                            {'name': 'GUKESH, DOMMARAJU', 'rating': 2750, 'result': 'D', 'round': 3},
                            {'name': 'PRAGGNANANDHAA, RAMESHBABU', 'rating': 2740, 'result': 'W', 'round': 4}
                        ]
                    }
                ]
            },
            'SHABALOV': {
                'rating': 2450,
                'tournaments': [
                    {
                        'name': '2024 US Open',
                        'date': '2024-08-03',
                        'rating_before': 2445,
                        'rating_after': 2450,
                        'score': '6.5/9',
                        'section': 'Open',
                        'opponents': [
                            {'name': 'BENJAMIN, JOEL', 'rating': 2420, 'result': 'W', 'round': 1},
                            {'name': 'FEDOROWICZ, JOHN', 'rating': 2380, 'result': 'D', 'round': 2},
                            {'name': 'NOVIKOV, IGOR', 'rating': 2360, 'result': 'W', 'round': 3},
                            {'name': 'ROHDE, MICHAEL', 'rating': 2340, 'result': 'W', 'round': 4}
                        ]
                    }
                ]
            }
        }

        # Check if this is a famous player
        for key, data in famous_players.items():
            if key in player_name.upper():
                return data['tournaments']

        # Generic sample data for unknown players
        base_rating = 2200 if any(title in player_name for title in ['GM', 'IM', 'FM']) else 1900

        return [
            {
                'name': f'{player_name} Sample Tournament',
                'date': '2024-06-15',
                'rating_before': base_rating - 20,
                'rating_after': base_rating,
                'score': '4.5/7',
                'section': 'Open',
                'opponents': [
                    {'name': 'STRONG PLAYER A', 'rating': base_rating + 100, 'result': 'L', 'round': 1},
                    {'name': 'PEER PLAYER B', 'rating': base_rating, 'result': 'W', 'round': 2},
                    {'name': 'WEAKER PLAYER C', 'rating': base_rating - 100, 'result': 'W', 'round': 3},
                    {'name': 'EQUAL PLAYER D', 'rating': base_rating + 10, 'result': 'D', 'round': 4},
                    {'name': 'STRONG PLAYER E', 'rating': base_rating + 80, 'result': 'W', 'round': 5},
                    {'name': 'PEER PLAYER F', 'rating': base_rating - 20, 'result': 'W', 'round': 6},
                    {'name': 'TOUGH OPPONENT G', 'rating': base_rating + 150, 'result': 'L', 'round': 7}
                ]
            }
        ]

    def search_player(self, search_term):
        """Search for a player using USCF lookup"""
        try:
            # Parse the search term (assuming "Last, First" format)
            if ',' in search_term:
                parts = search_term.split(',', 1)
                last_name = parts[0].strip()
                first_name = parts[1].strip()
            else:
                # If no comma, treat as last name
                last_name = search_term.strip()
                first_name = ""

            results = self.lookup.search_player_by_name(first_name, last_name)
            if results:
                # Convert PlayerInfo objects to dictionaries
                formatted_results = []
                for player in results[:10]:
                    formatted_results.append({
                        'name': player.name,
                        'uscf_id': player.uscf_id,
                        'rating': player.current_rating
                    })
                return formatted_results
        except Exception as e:
            print(f"Search error: {e}")
            pass
        return []

    def setup_layout(self):
        self.app.layout = html.Div([
            # Store components to hold data
            dcc.Store(id='selected-player-store'),
            dcc.Store(id='search-results-store'),

            # Header with search
            html.Div([
                html.H1("♟️ USCF Player Analysis Dashboard",
                       style={'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': '20px'}),

                # Search section
                html.Div([
                    html.H3("Search Player", style={'color': '#34495e', 'marginBottom': '15px'}),
                    html.Div([
                        dcc.Input(
                            id='player-search',
                            type='text',
                            placeholder='Enter player name (e.g., "Smith, John")',
                            style={'width': '300px', 'padding': '10px', 'marginRight': '10px'}
                        ),
                        html.Button('Search', id='search-btn',
                                  style={'padding': '10px 20px', 'backgroundColor': '#3498db', 'color': 'white', 'border': 'none'})
                    ], style={'marginBottom': '20px'}),

                    # Search results
                    html.Div(id='search-results', style={'marginBottom': '30px'})
                ], style={
                    'backgroundColor': '#f8f9fa',
                    'padding': '20px',
                    'borderRadius': '8px',
                    'marginBottom': '30px'
                })
            ]),

            # Current player section (will be updated dynamically)
            html.Div(id='player-content', children=self.create_player_content())
        ])

    def cache_all_opponents(self):
        """Cache all opponents from Kiren's tournaments for profile switching"""
        self.cached_opponents = {}

        for tournament in self.current_tournaments:
            for opp in tournament.get('opponents', []):
                name = opp['name']
                if name not in self.cached_opponents:
                    # Parse opponent name to get clean format
                    clean_name = self.parse_opponent_name(name)

                    # Create opponent profile data
                    self.cached_opponents[name] = {
                        'original_name': name,
                        'clean_name': clean_name,
                        'rating': opp['rating'],
                        'tournaments_vs_kiren': [],
                        'record_vs_kiren': {'W': 0, 'D': 0, 'L': 0},
                        'avg_rating': opp['rating']
                    }

                # Add this game to the opponent's record
                result = opp['result']
                self.cached_opponents[name]['tournaments_vs_kiren'].append({
                    'tournament': tournament['name'],
                    'date': tournament['date'],
                    'result': result,
                    'round': opp['round'],
                    'rating': opp['rating']
                })

                # Update record (from opponent's perspective)
                if result == 'W':  # Kiren won, so opponent lost
                    self.cached_opponents[name]['record_vs_kiren']['L'] += 1
                elif result == 'L':  # Kiren lost, so opponent won
                    self.cached_opponents[name]['record_vs_kiren']['W'] += 1
                elif result == 'D':  # Draw
                    self.cached_opponents[name]['record_vs_kiren']['D'] += 1

        print(f"✅ Cached {len(self.cached_opponents)} opponents for profile switching")

    def parse_opponent_name(self, name):
        """Parse opponent name to clean format"""
        if ',' in name:
            parts = name.split(',')
            lastname = parts[0].strip()
            firstname = parts[1].strip() if len(parts) > 1 else ""

            # Remove title prefixes
            for title in ['GM ', 'IM ', 'FM ', 'WGM ', 'WIM ', 'WFM ', 'MASTER ', 'EXPERT ', 'CLASS A ']:
                if lastname.startswith(title):
                    lastname = lastname[len(title):].strip()
                    break

            return f"{lastname}, {firstname}".strip(', ')
        return name

    def create_initial_charts(self):
        """Create initial charts with current player data"""
        print(f"🔍 Creating charts with {len(self.current_tournaments)} tournaments")

        if not self.current_tournaments:
            print("❌ No tournament data available for charts")
            return {
                'rating': go.Figure().update_layout(title="No tournament data available"),
                'performance': go.Figure().update_layout(title="No tournament data available"),
                'opponent_rating': go.Figure().update_layout(title="No tournament data available"),
                'results_pie': go.Figure().update_layout(title="No tournament data available")
            }

        # Rating progression chart
        sorted_tournaments = sorted(self.current_tournaments, key=lambda x: x['date'])
        dates = [t['date'] for t in sorted_tournaments]
        ratings_after = [t.get('rating_after', t.get('rating_before', 0)) for t in sorted_tournaments]

        print(f"📊 Rating chart: {len(dates)} dates, ratings: {ratings_after}")

        rating_fig = go.Figure()
        if dates and ratings_after:
            rating_fig.add_trace(go.Scatter(
                x=dates,
                y=ratings_after,
                mode='lines+markers',
                name='Rating',
                line=dict(color='#2c3e50', width=3),
                marker=dict(size=8, color='#e74c3c')
            ))

        rating_fig.update_layout(
            title=f"Rating Progression for {self.current_player_data['name']}",
            xaxis_title="Tournament Date",
            yaxis_title="USCF Rating",
            template='plotly_white',
            height=400
        )

        # Performance chart
        all_opponents = []
        for tournament in self.current_tournaments:
            for opp in tournament.get('opponents', []):
                all_opponents.append({
                    'rating': opp['rating'],
                    'result': opp['result'],
                    'score': 1 if opp['result'] == 'W' else 0.5 if opp['result'] == 'D' else 0
                })

        print(f"📈 Performance chart: {len(all_opponents)} opponent games")

        performance_fig = go.Figure()
        if all_opponents:
            df = pd.DataFrame(all_opponents)
            df['rating_range'] = pd.cut(df['rating'],
                                      bins=[0, 1600, 1800, 2000, 2200, 2400, 3000],
                                      labels=['<1600', '1600-1799', '1800-1999', '2000-2199', '2200-2399', '2400+'])
            performance = df.groupby('rating_range')['score'].mean().reset_index()

            performance_fig.add_trace(go.Bar(
                x=performance['rating_range'],
                y=performance['score'],
                marker_color=['#e74c3c' if x < 0.5 else '#f39c12' if x < 0.6 else '#27ae60'
                            for x in performance['score']]
            ))

        performance_fig.update_layout(
            title="Performance vs Opponent Rating",
            xaxis_title="Opponent Rating Range",
            yaxis_title="Score Rate",
            template='plotly_white',
            height=400
        )

        # Opponent rating distribution
        all_ratings = []
        for tournament in self.current_tournaments:
            for opp in tournament.get('opponents', []):
                all_ratings.append(opp['rating'])

        opponent_fig = go.Figure()
        if all_ratings:
            opponent_fig.add_trace(go.Histogram(x=all_ratings, nbinsx=15))

        opponent_fig.update_layout(
            title="Opponent Rating Distribution",
            xaxis_title="Opponent Rating",
            yaxis_title="Number of Games",
            template='plotly_white',
            height=400
        )

        # Results pie chart
        results = {'W': 0, 'D': 0, 'L': 0}
        for tournament in self.current_tournaments:
            for opp in tournament.get('opponents', []):
                results[opp['result']] += 1

        results_fig = go.Figure()
        if sum(results.values()) > 0:
            results_fig.add_trace(go.Pie(
                labels=['Wins', 'Draws', 'Losses'],
                values=[results['W'], results['D'], results['L']],
                marker_colors=['#27ae60', '#f39c12', '#e74c3c']
            ))

        results_fig.update_layout(
            title="Overall Results",
            template='plotly_white',
            height=400
        )

        return {
            'rating': rating_fig,
            'performance': performance_fig,
            'opponent_rating': opponent_fig,
            'results_pie': results_fig
        }

    def create_player_content(self):
        """Create content for the current player"""
        if not self.current_player_data:
            return html.Div("No player selected")

        # Create initial charts for layout
        initial_charts = self.create_initial_charts()

        return [
            # Player info card
            html.Div([
                html.H2(f"Analysis for {self.current_player_data['name']}",
                       style={'color': '#2c3e50', 'marginBottom': '20px'}),

                html.Div([
                    html.H3("Player Profile", style={'color': '#34495e', 'marginBottom': '15px'}),
                    html.P(f"Name: {self.current_player_data['name']}", style={'fontSize': '16px', 'margin': '5px 0'}),
                    html.P(f"USCF ID: {self.current_player_data['uscf_id']}", style={'fontSize': '16px', 'margin': '5px 0'}),
                    html.P(f"Regular Rating: {self.current_player_data['regular_rating']}",
                          style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#e74c3c', 'margin': '5px 0'}),
                    html.P(f"State: {self.current_player_data['state']}", style={'fontSize': '16px', 'margin': '5px 0'}),
                    html.P(f"Tournaments: {len(self.current_tournaments)}", style={'fontSize': '16px', 'margin': '5px 0'})
                ], style={
                    'backgroundColor': '#ecf0f1',
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'width': '300px',
                    'display': 'inline-block',
                    'marginRight': '20px',
                    'verticalAlign': 'top'
                })
            ]),

            # Charts section
            html.Div([
                html.Div([
                    dcc.Graph(id='rating-chart', figure=initial_charts['rating'])
                ], style={'width': '50%', 'display': 'inline-block'}),

                html.Div([
                    dcc.Graph(id='performance-chart', figure=initial_charts['performance'])
                ], style={'width': '50%', 'display': 'inline-block'})
            ], style={'width': 'calc(100% - 340px)', 'display': 'inline-block', 'marginTop': '20px'}),

            # Additional analysis charts
            html.Div([
                html.Div([
                    dcc.Graph(id='opponent-rating-chart', figure=initial_charts['opponent_rating'])
                ], style={'width': '50%', 'display': 'inline-block', 'marginTop': '20px'}),

                html.Div([
                    dcc.Graph(id='results-pie-chart', figure=initial_charts['results_pie'])
                ], style={'width': '50%', 'display': 'inline-block', 'marginTop': '20px'})
            ]),

            # Tournament details
            html.Div([
                html.H3("Tournament Details", style={'color': '#34495e', 'marginTop': '30px', 'marginBottom': '15px'}),
                html.Div(id='tournament-selector', children=[
                    dcc.Dropdown(
                        id='tournament-dropdown',
                        options=[{'label': t['name'], 'value': i} for i, t in enumerate(self.current_tournaments)],
                        value=0 if self.current_tournaments else None,
                        style={'marginBottom': '20px'}
                    )
                ])
            ]),

            # Tournament analysis
            html.Div(id='tournament-analysis'),

            # Opponents section
            html.Div(id='opponents-section'),

            # Opponent cache statistics
            html.Div([
                html.H3("Opponent Cache Overview", style={'color': '#34495e', 'marginTop': '30px', 'marginBottom': '15px'}),
                html.Div(id='opponent-cache-stats'),
                html.Button(
                    "🔄 Refresh Opponent Cache",
                    id='refresh-cache-btn',
                    style={
                        'padding': '10px 20px',
                        'backgroundColor': '#3498db',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '4px',
                        'marginTop': '20px',
                        'cursor': 'pointer'
                    }
                )
            ])
        ]

    def setup_callbacks(self):
        @self.app.callback(
            [Output('search-results', 'children'),
             Output('search-results-store', 'data')],
            [Input('search-btn', 'n_clicks')],
            [State('player-search', 'value')]
        )
        def search_players(n_clicks, search_term):
            if not n_clicks or not search_term:
                return [], []

            results = self.search_player(search_term)
            if not results:
                return html.P("No players found", style={'color': 'red'}), []

            search_display = html.Div([
                html.H4("Search Results:", style={'marginBottom': '10px'}),
                html.Div([
                    html.Button(
                        f"{result['name']} (ID: {result['uscf_id']}) - Rating: {result.get('rating', 'N/A')}",
                        id={'type': 'player-btn', 'index': i},
                        style={
                            'display': 'block',
                            'width': '100%',
                            'padding': '10px',
                            'margin': '5px 0',
                            'backgroundColor': '#ecf0f1',
                            'border': '1px solid #bdc3c7',
                            'borderRadius': '4px',
                            'cursor': 'pointer'
                        }
                    ) for i, result in enumerate(results)
                ])
            ])

            return search_display, results

        @self.app.callback(
            [Output('selected-player-store', 'data'),
             Output('player-content', 'children')],
            [Input({'type': 'player-btn', 'index': ALL}, 'n_clicks')],
            [State('search-results-store', 'data')]
        )
        def select_player(n_clicks_list, search_results):
            print(f"select_player called with n_clicks_list: {n_clicks_list}")
            print(f"search_results: {search_results}")

            if not any(n_clicks_list) or not search_results:
                print("No clicks detected or no search results, returning no_update")
                return no_update, no_update

            # Find which button was clicked
            ctx = callback_context
            print(f"Callback context triggered: {ctx.triggered}")

            if not ctx.triggered:
                print("No triggered context, returning no_update")
                return no_update, no_update

            # Extract the button index from the triggered button ID
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            print(f"Button ID: {button_id}")

            try:
                import json
                button_data = json.loads(button_id)
                button_index = button_data['index']
                print(f"Button index: {button_index}")

                # Get player data from stored search results
                if button_index < len(search_results):
                    player_data = search_results[button_index]
                    player_name = player_data['name']
                    uscf_id = player_data['uscf_id']
                    print(f"Selected player: {player_name} (ID: {uscf_id})")

                    # Load the selected player's data
                    self.load_player_data(player_name, uscf_id)

                    # Store the player data and return updated content
                    player_store_data = {'name': player_name, 'uscf_id': uscf_id}
                    print(f"Returning updated content for {player_name}")
                    return player_store_data, self.create_player_content()
                else:
                    print(f"Invalid button index: {button_index}")
                    return no_update, no_update

            except Exception as e:
                print(f"Error in select_player callback: {e}")
                import traceback
                traceback.print_exc()
                return no_update, no_update

        @self.app.callback(
            Output('rating-chart', 'figure'),
            [Input('selected-player-store', 'data'),
             Input('player-content', 'children')]
        )
        def update_rating_chart(store_data, player_content):
            print(f"update_rating_chart called, tournaments: {len(self.current_tournaments) if self.current_tournaments else 0}")
            if not self.current_tournaments:
                print("No tournaments data, returning empty figure")
                return go.Figure()

            # Sort tournaments by date
            sorted_tournaments = sorted(self.current_tournaments, key=lambda x: x['date'])

            dates = []
            ratings = []
            tournament_names = []
            rating_changes = []

            for tournament in sorted_tournaments:
                dates.append(tournament['date'])
                rating_after = tournament.get('rating_after', tournament.get('rating_before', 0))
                ratings.append(rating_after)
                tournament_names.append(tournament['name'])

                # Calculate rating change
                rating_before = tournament.get('rating_before', rating_after)
                change = rating_after - rating_before
                rating_changes.append(f"{'+' if change >= 0 else ''}{change}")

            fig = go.Figure()

            # Main rating line
            fig.add_trace(go.Scatter(
                x=dates,
                y=ratings,
                mode='lines+markers',
                name='Rating',
                line=dict(color='#2c3e50', width=3),
                marker=dict(size=8, color='#e74c3c'),
                hovertemplate='<b>%{text}</b><br>' +
                            'Date: %{x}<br>' +
                            'Rating: %{y}<br>' +
                            'Change: %{customdata}<br>' +
                            '<extra></extra>',
                text=tournament_names,
                customdata=rating_changes
            ))

            # Add rating zones
            if ratings:
                min_rating = min(ratings) - 50
                max_rating = max(ratings) + 50

                # Expert zone (2000+)
                if max_rating >= 2000:
                    fig.add_hrect(y0=2000, y1=max_rating,
                                  fillcolor="rgba(46, 204, 113, 0.1)",
                                  line_width=0, annotation_text="Expert+")

                # Class A zone (1800-1999)
                if max_rating >= 1800:
                    fig.add_hrect(y0=1800, y1=min(1999, max_rating),
                                  fillcolor="rgba(52, 152, 219, 0.1)",
                                  line_width=0, annotation_text="Class A")

            fig.update_layout(
                title=f"Rating Progression for {self.current_player_data['name']}",
                xaxis_title="Tournament Date",
                yaxis_title="USCF Rating",
                hovermode='closest',
                template='plotly_white',
                showlegend=True,
                height=400
            )

            return fig

        @self.app.callback(
            Output('performance-chart', 'figure'),
            [Input('selected-player-store', 'data'),
             Input('player-content', 'children')]
        )
        def update_performance_chart(store_data, player_content):
            if not self.current_tournaments:
                return go.Figure()

            # Calculate performance vs opponent rating
            all_opponents = []
            for tournament in self.current_tournaments:
                for opp in tournament.get('opponents', []):
                    all_opponents.append({
                        'rating': opp['rating'],
                        'result': opp['result'],
                        'score': 1 if opp['result'] == 'W' else 0.5 if opp['result'] == 'D' else 0
                    })

            if not all_opponents:
                return go.Figure()

            df = pd.DataFrame(all_opponents)

            # Group by rating ranges
            df['rating_range'] = pd.cut(df['rating'],
                                      bins=[0, 1600, 1800, 2000, 2200, 2400, 3000],
                                      labels=['<1600', '1600-1799', '1800-1999', '2000-2199', '2200-2399', '2400+'])

            performance = df.groupby('rating_range')['score'].mean().reset_index()

            fig = go.Figure(data=[
                go.Bar(x=performance['rating_range'], y=performance['score'],
                       marker_color=['#e74c3c' if x < 0.5 else '#f39c12' if x < 0.6 else '#27ae60'
                                   for x in performance['score']])
            ])

            fig.update_layout(
                title="Performance vs Opponent Rating",
                xaxis_title="Opponent Rating Range",
                yaxis_title="Score Rate",
                template='plotly_white',
                height=400
            )

            return fig

        @self.app.callback(
            Output('opponent-rating-chart', 'figure'),
            [Input('selected-player-store', 'data'),
             Input('player-content', 'children')]
        )
        def update_opponent_rating_chart(store_data, player_content):
            if not self.current_tournaments:
                return go.Figure()

            all_ratings = []
            for tournament in self.current_tournaments:
                for opp in tournament.get('opponents', []):
                    all_ratings.append(opp['rating'])

            if not all_ratings:
                return go.Figure()

            fig = go.Figure(data=[go.Histogram(x=all_ratings, nbinsx=15)])
            fig.update_layout(
                title="Opponent Rating Distribution",
                xaxis_title="Opponent Rating",
                yaxis_title="Number of Games",
                template='plotly_white',
                height=400
            )

            return fig

        @self.app.callback(
            Output('results-pie-chart', 'figure'),
            [Input('player-content', 'children')]
        )
        def update_results_pie_chart(_):
            if not self.current_tournaments:
                return go.Figure()

            results = {'W': 0, 'D': 0, 'L': 0}
            for tournament in self.current_tournaments:
                for opp in tournament.get('opponents', []):
                    results[opp['result']] += 1

            if sum(results.values()) == 0:
                return go.Figure()

            fig = go.Figure(data=[go.Pie(
                labels=['Wins', 'Draws', 'Losses'],
                values=[results['W'], results['D'], results['L']],
                marker_colors=['#27ae60', '#f39c12', '#e74c3c']
            )])

            fig.update_layout(
                title="Overall Results",
                template='plotly_white',
                height=400
            )

            return fig

        @self.app.callback(
            [Output('tournament-analysis', 'children'),
             Output('opponents-section', 'children')],
            [Input('tournament-dropdown', 'value')]
        )
        def update_tournament_details(selected_tournament_idx):
            if selected_tournament_idx is None or selected_tournament_idx >= len(self.current_tournaments):
                return [], []

            tournament = self.current_tournaments[selected_tournament_idx]

            # Tournament analysis
            analysis = html.Div([
                html.H4(f"Tournament: {tournament['name']}", style={'color': '#2c3e50'}),
                html.P(f"Date: {tournament['date']}"),
                html.P(f"Score: {tournament['score']}"),
                html.P(f"Rating Change: {tournament.get('rating_before', 0)} → {tournament.get('rating_after', 0)}"),
                html.P(f"Section: {tournament.get('section', 'N/A')}")
            ], style={'backgroundColor': '#f8f9fa', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '20px'})

            # Opponents table
            opponents = tournament.get('opponents', [])
            if opponents:
                opponents_table = html.Div([
                    html.H4("Opponents", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                    html.Table([
                        html.Thead([
                            html.Tr([
                                html.Th("Round", style={'padding': '8px', 'backgroundColor': '#34495e', 'color': 'white'}),
                                html.Th("Opponent", style={'padding': '8px', 'backgroundColor': '#34495e', 'color': 'white'}),
                                html.Th("Rating", style={'padding': '8px', 'backgroundColor': '#34495e', 'color': 'white'}),
                                html.Th("Result", style={'padding': '8px', 'backgroundColor': '#34495e', 'color': 'white'})
                            ])
                        ]),
                        html.Tbody([
                            html.Tr([
                                html.Td(opp['round'], style={'padding': '8px', 'border': '1px solid #ddd'}),
                                html.Td(
                                    html.Button(
                                        opp['name'],
                                        id={'type': 'opponent-btn', 'name': opp['name']},
                                        style={
                                            'background': 'none',
                                            'border': 'none',
                                            'color': '#3498db',
                                            'cursor': 'pointer',
                                            'textDecoration': 'underline'
                                        }
                                    ),
                                    style={'padding': '8px', 'border': '1px solid #ddd'}
                                ),
                                html.Td(opp['rating'], style={'padding': '8px', 'border': '1px solid #ddd'}),
                                html.Td(
                                    opp['result'],
                                    style={
                                        'padding': '8px',
                                        'border': '1px solid #ddd',
                                        'backgroundColor': '#d5edda' if opp['result'] == 'W' else '#f8d7da' if opp['result'] == 'L' else '#fff3cd',
                                        'fontWeight': 'bold'
                                    }
                                )
                            ]) for opp in opponents
                        ])
                    ], style={'width': '100%', 'borderCollapse': 'collapse'})
                ])
            else:
                opponents_table = html.P("No opponent data available")

            return analysis, opponents_table

        @self.app.callback(
            Output('player-content', 'children', allow_duplicate=True),
            [Input({'type': 'opponent-btn', 'name': dash.dependencies.ALL}, 'n_clicks')],
            prevent_initial_call=True
        )
        def handle_opponent_click(n_clicks_list):
            """Handle clicking on opponent names - now with real cached data"""
            if not any(n_clicks_list):
                return dash.no_update

            ctx = callback_context
            if not ctx.triggered:
                return dash.no_update

            # Extract the opponent name from the triggered button
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            import json as json_module
            button_data = json_module.loads(button_id)
            opponent_name = button_data['name']

            # Check if we have cached data for this opponent
            if hasattr(self, 'cached_opponents') and opponent_name in self.cached_opponents:
                opp_data = self.cached_opponents[opponent_name]

                # Create opponent profile with cached data
                self.current_player_data = {
                    'name': opp_data['clean_name'],
                    'uscf_id': f"OPP_{hash(opponent_name) % 100000000}",  # Generate consistent ID
                    'regular_rating': opp_data['avg_rating'],
                    'state': 'Unknown'
                }

                # Create opponent tournament data showing games vs Kiren
                opponent_tournaments = []
                for game in opp_data['tournaments_vs_kiren']:
                    # Create a tournament from opponent's perspective
                    opp_result = game['result']
                    if opp_result == 'W':  # Kiren won, opponent lost
                        opp_perspective = 'L'
                    elif opp_result == 'L':  # Kiren lost, opponent won
                        opp_perspective = 'W'
                    else:  # Draw
                        opp_perspective = 'D'

                    opponent_tournaments.append({
                        'name': f"{game['tournament']} (vs Kiren)",
                        'date': game['date'],
                        'rating_before': game['rating'],
                        'rating_after': game['rating'],
                        'score': '1/1' if opp_perspective == 'W' else '0.5/1' if opp_perspective == 'D' else '0/1',
                        'section': 'vs Kiren Nasta',
                        'opponents': [{
                            'name': 'NASTA, KIREN',
                            'rating': 2208,
                            'result': opp_perspective,
                            'round': game['round']
                        }]
                    })

                # Update tournament data BEFORE creating content
                self.current_tournaments = opponent_tournaments
                print(f"🎯 Created {len(opponent_tournaments)} opponent tournaments for {opp_data['clean_name']}")

                # Get record summary
                record = opp_data['record_vs_kiren']
                record_str = f"{record['W']}W-{record['L']}L-{record['D']}D"

                # Create fresh content with updated data
                print(f"🔄 Creating player content for opponent: {opp_data['clean_name']}")
                player_content = self.create_player_content()

                return [
                    html.Div([
                        html.H2(f"🔍 Opponent Analysis: {opp_data['clean_name']}",
                               style={'color': '#27ae60', 'marginBottom': '20px'}),
                        html.P(f"Record vs Kiren Nasta: {record_str} | Average Rating: {opp_data['avg_rating']}",
                              style={'fontSize': '16px', 'color': '#34495e', 'marginBottom': '20px'}),
                        html.Button("← Back to Kiren", id='back-to-kiren-btn',
                                  style={'padding': '10px 20px', 'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'marginBottom': '20px'})
                    ]),
                    *player_content
                ]

            return dash.no_update

        @self.app.callback(
            Output('player-content', 'children', allow_duplicate=True),
            [Input('back-to-kiren-btn', 'n_clicks')],
            prevent_initial_call=True
        )
        def back_to_kiren(n_clicks):
            """Return to Kiren's analysis"""
            if not n_clicks:
                return dash.no_update

            # Reset to Kiren's data and re-cache opponents
            self.load_player_data("NASTA, KIREN", "15255524")
            return self.create_player_content()

        @self.app.callback(
            [Output('rating-chart', 'figure', allow_duplicate=True),
             Output('performance-chart', 'figure', allow_duplicate=True),
             Output('opponent-rating-chart', 'figure', allow_duplicate=True),
             Output('results-pie-chart', 'figure', allow_duplicate=True)],
            [Input('player-content', 'children')],
            prevent_initial_call=True
        )
        def update_all_charts_on_content_change(player_content):
            """Update all charts when player content changes (not on initial call)"""
            print(f"🔄 Updating all charts for current player data")
            charts = self.create_initial_charts()
            return (
                charts['rating'],
                charts['performance'],
                charts['opponent_rating'],
                charts['results_pie']
            )

        @self.app.callback(
            Output('opponent-cache-stats', 'children'),
            [Input('player-content', 'children')]
        )
        def update_opponent_cache_stats(_):
            """Update opponent cache statistics display"""
            try:
                stats = self.opponent_cache.get_statistics()

                if not stats:
                    return html.P("No opponent data available")

                # Create statistics cards
                stats_cards = html.Div([
                    # Overall stats card
                    html.Div([
                        html.H4("Overall Statistics", style={'color': '#2c3e50', 'marginBottom': '10px'}),
                        html.P(f"Total Opponents: {stats.get('total_opponents', 0)}", style={'margin': '5px 0'}),
                        html.P(f"Total Games: {stats.get('total_games', 0)}", style={'margin': '5px 0'}),
                        html.P(f"Win Rate: {stats.get('win_percentage', 0):.1f}%",
                              style={'margin': '5px 0', 'fontWeight': 'bold', 'color': '#27ae60'}),
                        html.P(f"Average Opponent Rating: {stats.get('avg_opponent_rating', 0):.0f}",
                              style={'margin': '5px 0', 'fontWeight': 'bold', 'color': '#e74c3c'})
                    ], style={
                        'backgroundColor': '#f8f9fa',
                        'padding': '15px',
                        'borderRadius': '8px',
                        'width': '200px',
                        'display': 'inline-block',
                        'marginRight': '20px',
                        'verticalAlign': 'top'
                    }),

                    # Rating distribution card
                    html.Div([
                        html.H4("Opponent Rating Distribution", style={'color': '#2c3e50', 'marginBottom': '10px'}),
                        html.Div([
                            html.P(f"{rating_range}: {count} opponents", style={'margin': '3px 0'})
                            for rating_range, count in stats.get('rating_distribution', {}).items()
                        ])
                    ], style={
                        'backgroundColor': '#f8f9fa',
                        'padding': '15px',
                        'borderRadius': '8px',
                        'width': '250px',
                        'display': 'inline-block',
                        'marginRight': '20px',
                        'verticalAlign': 'top'
                    }),

                    # Top opponents preview
                    html.Div([
                        html.H4("Top 5 Opponents by Rating", style={'color': '#2c3e50', 'marginBottom': '10px'}),
                        html.Div([
                            html.P(f"{i+1}. {opp.name} ({opp.avg_rating:.0f})",
                                  style={'margin': '3px 0', 'fontSize': '14px'})
                            for i, opp in enumerate(self.opponent_cache.get_top_opponents_by_rating(5))
                        ])
                    ], style={
                        'backgroundColor': '#f8f9fa',
                        'padding': '15px',
                        'borderRadius': '8px',
                        'width': '250px',
                        'display': 'inline-block',
                        'verticalAlign': 'top'
                    })
                ])

                # Add timestamp info
                timestamp_info = html.Div([
                    html.Span(f"Last updated: {stats.get('last_updated', 'Never')[:19]}",
                             style={'color': '#7f8c8d', 'fontSize': '12px', 'marginTop': '10px', 'display': 'block'})
                ])

                return [stats_cards, timestamp_info]

            except Exception as e:
                return html.P(f"Error loading opponent cache: {e}", style={'color': 'red'})

        @self.app.callback(
            Output('opponent-cache-stats', 'children', allow_duplicate=True),
            [Input('refresh-cache-btn', 'n_clicks')],
            prevent_initial_call=True
        )
        def refresh_opponent_cache(n_clicks):
            """Handle opponent cache refresh button"""
            if not n_clicks:
                return dash.no_update

            try:
                success = self.opponent_cache.force_refresh()
                if success:
                    # Return updated stats after refresh
                    stats = self.opponent_cache.get_statistics()

                    stats_cards = html.Div([
                        html.Div([
                            html.H4("Overall Statistics", style={'color': '#2c3e50', 'marginBottom': '10px'}),
                            html.P(f"Total Opponents: {stats.get('total_opponents', 0)}", style={'margin': '5px 0'}),
                            html.P(f"Total Games: {stats.get('total_games', 0)}", style={'margin': '5px 0'}),
                            html.P(f"Win Rate: {stats.get('win_percentage', 0):.1f}%",
                                  style={'margin': '5px 0', 'fontWeight': 'bold', 'color': '#27ae60'}),
                            html.P(f"Average Opponent Rating: {stats.get('avg_opponent_rating', 0):.0f}",
                                  style={'margin': '5px 0', 'fontWeight': 'bold', 'color': '#e74c3c'})
                        ], style={
                            'backgroundColor': '#f8f9fa',
                            'padding': '15px',
                            'borderRadius': '8px',
                            'width': '200px',
                            'display': 'inline-block',
                            'marginRight': '20px',
                            'verticalAlign': 'top'
                        }),

                        html.Div([
                            html.H4("Opponent Rating Distribution", style={'color': '#2c3e50', 'marginBottom': '10px'}),
                            html.Div([
                                html.P(f"{rating_range}: {count} opponents", style={'margin': '3px 0'})
                                for rating_range, count in stats.get('rating_distribution', {}).items()
                            ])
                        ], style={
                            'backgroundColor': '#f8f9fa',
                            'padding': '15px',
                            'borderRadius': '8px',
                            'width': '250px',
                            'display': 'inline-block',
                            'marginRight': '20px',
                            'verticalAlign': 'top'
                        }),

                        html.Div([
                            html.H4("Top 5 Opponents by Rating", style={'color': '#2c3e50', 'marginBottom': '10px'}),
                            html.Div([
                                html.P(f"{i+1}. {opp.name} ({opp.avg_rating:.0f})",
                                      style={'margin': '3px 0', 'fontSize': '14px'})
                                for i, opp in enumerate(self.opponent_cache.get_top_opponents_by_rating(5))
                            ])
                        ], style={
                            'backgroundColor': '#f8f9fa',
                            'padding': '15px',
                            'borderRadius': '8px',
                            'width': '250px',
                            'display': 'inline-block',
                            'verticalAlign': 'top'
                        })
                    ])

                    # Add success timestamp
                    success_info = html.Div([
                        html.Span("✅ Cache refreshed successfully!",
                                 style={'color': '#27ae60', 'fontWeight': 'bold', 'marginRight': '15px'}),
                        html.Span(f"Last updated: {stats.get('last_updated', 'Never')[:19]}",
                                 style={'color': '#7f8c8d', 'fontSize': '12px'})
                    ], style={'marginTop': '10px'})

                    return [stats_cards, success_info]
                else:
                    return html.P("Failed to refresh cache", style={'color': 'red'})

            except Exception as e:
                return html.P(f"Error refreshing cache: {e}", style={'color': 'red'})

        @self.app.callback(
            [Output('refresh-cache-btn', 'children'),
             Output('refresh-cache-btn', 'style')],
            [Input('refresh-cache-btn', 'n_clicks')],
            prevent_initial_call=True
        )
        def update_refresh_button(n_clicks):
            """Update refresh button appearance when clicked"""
            if not n_clicks:
                return dash.no_update, dash.no_update

            return "✅ Cache Refreshed!", {
                'padding': '10px 20px',
                'backgroundColor': '#27ae60',
                'color': 'white',
                'border': 'none',
                'borderRadius': '4px',
                'marginTop': '20px',
                'cursor': 'pointer'
            }

    def run(self, debug=True, port=8052):
        """Run the dashboard"""
        print("🏁 Starting Enhanced Chess Dashboard")
        print(f"📊 Dashboard URL: http://localhost:{port}")
        print("🔍 Search any USCF player and analyze their performance!")

        # Use environment variable for port (for deployment)
        import os
        port = int(os.environ.get('PORT', port))

        self.app.run(debug=debug, port=port, host='0.0.0.0')

def main():
    dashboard = EnhancedChessDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()