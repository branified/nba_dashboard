import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go

df = pd.read_csv('nba_2022-23_all_stats_with_salary.csv')

app = Dash(__name__)

app.layout = html.Div([
    html.H1("NBA Team Comparison Dashboard"),

    # Team selection dropdowns
    html.Label("Select Team 1"),
    dcc.Dropdown(
        id="team1-dropdown",
        options=[{"label": team, "value": team} for team in df["Team"].unique()],
        value=df["Team"].unique()[0]
    ),

    html.Label("Select Team 2"),
    dcc.Dropdown(
        id="team2-dropdown",
        options=[{"label": team, "value": team} for team in df["Team"].unique()],
        value=df["Team"].unique()[1]
    ),

    # Stats selection for radar plot
    html.Label("Select Stats to Visualize"),
    dcc.Dropdown(
        id="stats-dropdown",
        options=[{"label": stat, "value": stat} for stat in ["FG", "3P", "2P", "FT", "TRB", "AST", "STL", "BLK", "TOV", "PF", "PTS", "PER"]],
        value=["FG", "3P", "2P", "FT", "TRB", "AST", "STL", "BLK", "TOV", "PF", "PTS", "PER"],  # Default stats
        multi=True
    ),

    # Toggle player stats view
    dcc.Checklist(
        id="show-player-stats",
        options=[{"label": "Show Player Stats", "value": "show"}],
        value=[]
    ),

    # Dropdowns for player comparison
    html.Label("Select Player from Team 1"),
    dcc.Dropdown(id="player1-dropdown", placeholder="Select Player from Team 1", searchable=True),

    html.Label("Select Player from Team 2"),
    dcc.Dropdown(id="player2-dropdown", placeholder="Select Player from Team 2", searchable=True),
    html.Div([
        # Left column: Team stats + Player comparison
        html.Div([
            # Team comparison radar plot
            html.Div(id="team-stats-output", style={'width': '100%', 'display': 'inline-block'}),

            # Player comparison radar plot
            html.Div(id="player-comparison-output", style={'width': '100%', 'display': 'inline-block'}),
        ], style={'width': '50%', 'display': 'inline-block'}),

        # Right column: Player stats bar chart
        html.Div(id="player-stats-output", style={'width': '50%', 'display': 'inline-block'}),
        ], 
            style={'display': 'flex', 'justify-content': 'space-between'}),
    ])

# Callbacks to update player options based on team selections
@app.callback(
    Output("player1-dropdown", "options"),
    Input("team1-dropdown", "value")
)
def update_player1_options(team1):
    team1_players = df[df["Team"] == team1]["Player Name"].unique()
    return [{"label": player, "value": player} for player in team1_players]

@app.callback(
    Output("player2-dropdown", "options"),
    Input("team2-dropdown", "value")
)
def update_player2_options(team2):
    team2_players = df[df["Team"] == team2]["Player Name"].unique()
    return [{"label": player, "value": player} for player in team2_players]

# Main callback to update team stats, player stats, and player comparison outputs
@app.callback(
    [Output("team-stats-output", "children"),
     Output("player-stats-output", "children"),
     Output("player-comparison-output", "children")],
    [Input("team1-dropdown", "value"),
     Input("team2-dropdown", "value"),
     Input("stats-dropdown", "value"),
     Input("show-player-stats", "value"),
     Input("player1-dropdown", "value"),
     Input("player2-dropdown", "value")]
)
def update_stats(team1, team2, selected_stats, show_player_stats, player1, player2):
    # Filter datasets for each team
    team1_df = df[df["Team"] == team1]
    team2_df = df[df["Team"] == team2]

    # Calculate team stats for radar plot. Using sum to get total for all players
    team1_stats = team1_df[selected_stats].sum()
    team2_stats = team2_df[selected_stats].sum()

    # Standardize to a common scale (min-max scaling)
    all_stats_df = df[selected_stats]  # Subset of stats for scaling
    min_vals = all_stats_df.min()
    max_vals = all_stats_df.max()

    team1_scaled = [(team1_stats[stat] - min_vals[stat]) / (max_vals[stat] - min_vals[stat])/10 for stat in selected_stats]
    team2_scaled = [(team2_stats[stat] - min_vals[stat]) / (max_vals[stat] - min_vals[stat])/10 for stat in selected_stats]

    # Actual stats (unscaled values) for hover display
    team1_actual = [team1_stats[stat] for stat in selected_stats]
    team2_actual = [team2_stats[stat] for stat in selected_stats]

    # Create radar plot
    team_comparison_fig = go.Figure()

    # Add scaled number and actual stat number for team 1 and team 2
    team_comparison_fig.add_trace(go.Scatterpolar(
        r=team1_scaled,
        theta=selected_stats,
        fill='toself',
        name=team1,
        customdata=[round(value, 2) for value in team1_actual], # Actual Stats
        hovertemplate='<b>%{theta}</b><br>Scaled: %{r:.2f}<br>Actual Stat: %{customdata}'
    ))

    team_comparison_fig.add_trace(go.Scatterpolar(
        r=team2_scaled,
        theta=selected_stats,
        fill='toself',
        name=team2,
        customdata=[round(value, 2) for value in team2_actual], # Actual Stats
        hovertemplate='<b>%{theta}</b><br>Scaled: %{r:.2f}<br>Actual Stat: %{customdata}'
    ))

    team_comparison_fig.update_layout(
        title=f"Team Comparison: {team1} vs {team2}",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True
    )

    team_comparison_output = html.Div([
        html.H3(f"Team Comparison: {team1} vs {team2}"),
        dcc.Graph(figure=team_comparison_fig)
    ])

    # Show player stats if selected
    player_stats_output = None
    if "show" in show_player_stats:
        team1_fig = px.bar(team1_df, x="Player Name", y=["PTS", "AST", "TRB"], title=f"{team1} Player Stats")
        team2_fig = px.bar(team2_df, x="Player Name", y=["PTS", "AST", "TRB"], title=f"{team2} Player Stats")
        player_stats_output = html.Div([
            dcc.Graph(figure=team1_fig),
            dcc.Graph(figure=team2_fig)
        ])

    # Player comparison output as a radar plot
    player_comparison_output = None
    if player1 and player2:
        player1_data = team1_df[team1_df["Player Name"] == player1]
        player2_data = team2_df[team2_df["Player Name"] == player2]

        if player1_data.empty or player2_data.empty:
            player_comparison_output = html.Div([
                html.P("One or both player names are not found in the selected teams.")
            ])
        else:
            # Extract stats into a list
            stats = ["FG", "3P", "2P", "FT", "TRB", "AST", "STL", "BLK", "TOV", "PF", "PTS", "PER"]
            all_stats_df = df[stats]
            min_vals = all_stats_df.min()
            max_vals = all_stats_df.max()

            player1_scaled = [(player1_data[stat].values[0] - min_vals[stat]) / (max_vals[stat] - min_vals[stat]) for stat in stats]
            player2_scaled = [(player2_data[stat].values[0] - min_vals[stat]) / (max_vals[stat] - min_vals[stat]) for stat in stats]

            # Actual stats (unscaled values) for hover display
            player1_actual = [player1_data[stat].values[0] for stat in stats]
            player2_actual = [player2_data[stat].values[0] for stat in stats]


            # Create radar plot
            comparison_fig = go.Figure()

            comparison_fig.add_trace(go.Scatterpolar(
              r=player1_scaled,
              theta=stats,
              fill='toself',
              name=player1,
              customdata=player1_actual,  # Actual Stats
              hovertemplate='<b>%{theta}</b><br>Scaled: %{r:.2f}<br>Actual Stat: %{customdata}'
          ))

            comparison_fig.add_trace(go.Scatterpolar(
                r=player2_scaled,
                theta=stats,
                fill='toself',
                name=player2,
                customdata=player2_actual,  # Actual Stats
                hovertemplate='<b>%{theta}</b><br>Scaled: %{r:.2f}<br>Actual Stat: %{customdata}'
            ))

            comparison_fig.update_layout(
                title=f"Player Comparison: {player1} vs {player2}",
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )
                ),
                showlegend=True
            )

            player_comparison_output = html.Div([
                html.H3(f"Player Comparison: {player1} vs {player2}"),
                dcc.Graph(figure=comparison_fig)
            ])

    return team_comparison_output, player_stats_output, player_comparison_output


app.run_server()