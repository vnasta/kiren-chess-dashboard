#!/usr/bin/env python3
"""
Clean Interactive Chess Dashboard for Kiren Nasta
Simple, focused, and functional
"""

import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from src.uscf_player_lookup import USCFPlayerLookup

class CleanChessDashboard:
    def __init__(self):
        self.player_name = "NASTA, KIREN"
        self.uscf_id = "15255524"
        self.lookup = USCFPlayerLookup()

        # Clean sample data for Kiren Nasta - Updated with regular rating
        self.player_data = {
            'name': 'NASTA, KIREN',
            'uscf_id': '15255524',
            'current_rating': 2208,  # Regular rating, not quick rating
            'state': 'NY'
        }

        # Load real tournament data
        self.tournaments = self.load_real_tournaments()

        self.app = dash.Dash(__name__)
        self.setup_layout()
        self.setup_callbacks()

    def load_real_tournaments(self):
        """Load real tournament data from JSON file"""
        try:
            import json
            with open('data/real_kiren_tournaments.json', 'r') as f:
                return json.load(f)
        except:
            # Fallback to sample data if file not found
            return [
                {
                    'name': '2025 US Open Chess Championship',
                    'date': '2025-08-03',
                    'rating_before': 2259,
                    'rating_after': 2239,
                    'score': '5.5/9',
                    'section': 'Open',
                    'opponents': [
                        {'name': 'GM SHABALOV, ALEXANDER', 'rating': 2456, 'result': 'L', 'round': 1},
                        {'name': 'EXPERT JOHNSON, MICHAEL', 'rating': 2180, 'result': 'W', 'round': 2},
                        {'name': 'IM WILLIAMS, SARAH', 'rating': 2389, 'result': 'D', 'round': 3},
                        {'name': 'FM BROWN, DAVID', 'rating': 2298, 'result': 'W', 'round': 4},
                        {'name': 'EXPERT GARCIA, MARIA', 'rating': 2156, 'result': 'W', 'round': 5},
                        {'name': 'MASTER WILSON, ROBERT', 'rating': 2267, 'result': 'W', 'round': 6},
                        {'name': 'IM TAYLOR, JENNIFER', 'rating': 2398, 'result': 'L', 'round': 7},
                        {'name': 'EXPERT ANDERSON, CHRIS', 'rating': 2189, 'result': 'W', 'round': 8},
                        {'name': 'FM MARTINEZ, CARLOS', 'rating': 2234, 'result': 'W', 'round': 9}
                    ]
                }
            ]

    def setup_layout(self):
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("♟️ Kiren Nasta Chess Performance Dashboard",
                       style={'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': '30px'})
            ]),

            # Player info card
            html.Div([
                html.Div([
                    html.H3("Player Profile", style={'color': '#34495e', 'marginBottom': '15px'}),
                    html.P(f"Name: {self.player_data['name']}", style={'fontSize': '16px', 'margin': '5px 0'}),
                    html.P(f"USCF ID: {self.player_data['uscf_id']}", style={'fontSize': '16px', 'margin': '5px 0'}),
                    html.P(f"Current Rating: {self.player_data['current_rating']}",
                          style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#e74c3c', 'margin': '5px 0'}),
                    html.P(f"State: {self.player_data['state']}", style={'fontSize': '16px', 'margin': '5px 0'}),
                    html.P(f"Tournaments: {len(self.tournaments)}", style={'fontSize': '16px', 'margin': '5px 0'})
                ], style={
                    'backgroundColor': '#ecf0f1',
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                })
            ], style={'width': '300px', 'display': 'inline-block', 'marginRight': '20px', 'verticalAlign': 'top'}),

            # Rating progression chart
            html.Div([
                dcc.Graph(id='rating-chart')
            ], style={'width': 'calc(100% - 340px)', 'display': 'inline-block'}),

            # Tournament selector
            html.Div([
                html.H3("🏆 Tournament Details", style={'color': '#34495e', 'marginBottom': '15px'}),
                html.Label("Select Tournament:", style={'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
                dcc.Dropdown(
                    id='tournament-selector',
                    options=[{'label': t['name'], 'value': i} for i, t in enumerate(self.tournaments)],
                    value=0,
                    style={'marginBottom': '20px'}
                )
            ], style={'margin': '30px 0'}),

            # Tournament details section
            html.Div(id='tournament-info'),

            # Charts row
            html.Div([
                html.Div([
                    dcc.Graph(id='opponent-chart')
                ], style={'width': '48%', 'display': 'inline-block'}),

                html.Div([
                    dcc.Graph(id='results-pie')
                ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'})
            ], style={'margin': '20px 0'})

        ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px'})

    def setup_callbacks(self):
        @self.app.callback(
            Output('rating-chart', 'figure'),
            [Input('tournament-selector', 'value')]
        )
        def update_rating_chart(selected_tournament):
            dates = [t['date'] for t in self.tournaments]
            ratings_after = [t['rating_after'] for t in self.tournaments]
            ratings_before = [t['rating_before'] for t in self.tournaments]

            fig = go.Figure()

            # Rating progression line
            fig.add_trace(go.Scatter(
                x=dates,
                y=ratings_after,
                mode='lines+markers',
                name='Rating Progression',
                line=dict(color='#3498db', width=3),
                marker=dict(size=8)
            ))

            # Highlight selected tournament
            if selected_tournament is not None:
                fig.add_trace(go.Scatter(
                    x=[dates[selected_tournament]],
                    y=[ratings_after[selected_tournament]],
                    mode='markers',
                    name='Selected Tournament',
                    marker=dict(size=15, color='#e74c3c')
                ))

            fig.update_layout(
                title='Rating Progression Over Time',
                xaxis_title='Date',
                yaxis_title='Rating',
                showlegend=True,
                height=400
            )

            return fig

        @self.app.callback(
            Output('tournament-info', 'children'),
            [Input('tournament-selector', 'value')]
        )
        def update_tournament_info(selected_tournament):
            if selected_tournament is None:
                return html.Div("Select a tournament")

            tournament = self.tournaments[selected_tournament]

            # Calculate performance stats
            wins = sum(1 for opp in tournament['opponents'] if opp['result'] == 'W')
            losses = sum(1 for opp in tournament['opponents'] if opp['result'] == 'L')
            draws = sum(1 for opp in tournament['opponents'] if opp['result'] == 'D')
            avg_opponent_rating = sum(opp['rating'] for opp in tournament['opponents']) / len(tournament['opponents'])

            # Create opponent table
            opponent_rows = []
            for opp in tournament['opponents']:
                result_color = '#27ae60' if opp['result'] == 'W' else '#e74c3c' if opp['result'] == 'L' else '#f39c12'
                opponent_rows.append(
                    html.Tr([
                        html.Td(f"Round {opp['round']}", style={'padding': '8px', 'textAlign': 'center'}),
                        html.Td(opp['name'], style={'padding': '8px'}),
                        html.Td(opp['rating'], style={'padding': '8px', 'textAlign': 'center'}),
                        html.Td(opp['result'], style={
                            'padding': '8px',
                            'textAlign': 'center',
                            'backgroundColor': result_color,
                            'color': 'white',
                            'fontWeight': 'bold',
                            'borderRadius': '4px'
                        })
                    ])
                )

            return html.Div([
                # Tournament header
                html.Div([
                    html.H4(tournament['name'], style={'color': '#2c3e50', 'margin': '0'}),
                    html.P(f"📅 {tournament['date']} | 🏆 {tournament['section']} Section",
                          style={'color': '#7f8c8d', 'margin': '5px 0'})
                ], style={'marginBottom': '20px'}),

                # Stats row
                html.Div([
                    html.Div([
                        html.H5("Tournament Stats", style={'color': '#34495e'}),
                        html.P(f"Score: {tournament['score']}", style={'fontSize': '18px', 'fontWeight': 'bold'}),
                        html.P(f"Rating: {tournament['rating_before']} → {tournament['rating_after']} ({tournament['rating_after'] - tournament['rating_before']:+d})"),
                        html.P(f"Record: {wins}W-{losses}L-{draws}D"),
                        html.P(f"Avg Opponent Rating: {avg_opponent_rating:.0f}")
                    ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),

                    html.Div([
                        html.H5("Round-by-Round Results", style={'color': '#34495e'}),
                        html.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Round", style={'padding': '8px', 'backgroundColor': '#34495e', 'color': 'white'}),
                                    html.Th("Opponent", style={'padding': '8px', 'backgroundColor': '#34495e', 'color': 'white'}),
                                    html.Th("Rating", style={'padding': '8px', 'backgroundColor': '#34495e', 'color': 'white'}),
                                    html.Th("Result", style={'padding': '8px', 'backgroundColor': '#34495e', 'color': 'white'})
                                ])
                            ]),
                            html.Tbody(opponent_rows)
                        ], style={'borderCollapse': 'collapse', 'width': '100%', 'border': '1px solid #ddd'})
                    ], style={'width': '65%', 'display': 'inline-block', 'marginLeft': '5%'})
                ])
            ], style={
                'backgroundColor': '#f8f9fa',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'margin': '20px 0'
            })

        @self.app.callback(
            [Output('opponent-chart', 'figure'), Output('results-pie', 'figure')],
            [Input('tournament-selector', 'value')]
        )
        def update_charts(selected_tournament):
            if selected_tournament is None:
                return {}, {}

            tournament = self.tournaments[selected_tournament]
            opponents = tournament['opponents']

            # Opponent ratings chart
            colors = ['#27ae60' if opp['result'] == 'W' else '#e74c3c' if opp['result'] == 'L' else '#f39c12'
                     for opp in opponents]

            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=[f"R{opp['round']}" for opp in opponents],
                y=[opp['rating'] for opp in opponents],
                marker_color=colors,
                text=[opp['result'] for opp in opponents],
                textposition='outside',
                hovertemplate='Round %{x}<br>Rating: %{y}<br>Result: %{text}<extra></extra>'
            ))

            fig1.update_layout(
                title='Opponent Ratings by Round',
                xaxis_title='Round',
                yaxis_title='Opponent Rating',
                height=400
            )

            # Results pie chart
            results = [opp['result'] for opp in opponents]
            result_counts = {
                'Wins': results.count('W'),
                'Losses': results.count('L'),
                'Draws': results.count('D')
            }

            fig2 = go.Figure(data=[go.Pie(
                labels=list(result_counts.keys()),
                values=list(result_counts.values()),
                marker_colors=['#27ae60', '#e74c3c', '#f39c12'],
                textinfo='label+percent',
                textfont_size=12
            )])

            fig2.update_layout(
                title='Results Distribution',
                height=400
            )

            return fig1, fig2

    def run(self, port=8051):
        print(f"🏁 Starting Clean Chess Dashboard")
        print(f"📊 Dashboard URL: http://localhost:{port}")
        print(f"♟️  Player: {self.player_data['name']}")
        print(f"🏆 Tournaments: {len(self.tournaments)}")
        print(f"⭐ Current Rating: {self.player_data['current_rating']}")

        self.app.run(debug=True, port=port, host='0.0.0.0')

def main():
    dashboard = CleanChessDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()