# %pip install kaggle streamlit pandas plotly
import os, zipfile
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# Set up Kaggle API credentials (for Streamlit Cloud)
if 'KAGGLE_USERNAME' in os.environ and 'KAGGLE_KEY' in os.environ:
    os.makedirs(os.path.expanduser('~/.kaggle'), exist_ok=True)
    with open(os.path.expanduser('~/.kaggle/kaggle.json'), 'w') as f:
        f.write('{"username":"%s","key":"%s"}' % (os.environ['KAGGLE_USERNAME'], os.environ['KAGGLE_KEY']))

# Download the dataset if not already present
if not os.path.exists("air-quality-madrid.zip"):
    os.system('kaggle datasets download -d decide-soluciones/air-quality-madrid')

# Unzip if not already unzipped
if not os.path.exists("archive"):
    with zipfile.ZipFile("air-quality-madrid.zip", "r") as zip_ref:
        zip_ref.extractall("archive")

print("Path to dataset files:", os.path.abspath("archive"))

# Define key pollutants and their units
pollutants = ['SO_2', 'CO', 'NO_2', 'PM10', 'PM25', 'O_3']
units = {'SO_2': 'μg/m³', 'CO': 'mg/m³', 'NO_2': 'μg/m³', 'PM10': 'μg/m³', 'PM25': 'μg/m³', 'O_3': 'μg/m³'}

# Load and process data
yearly_station_averages = []
for year in range(2001, 2019):
    df_year = pd.read_csv(f'archive/csvs_per_year/csvs_per_year/madrid_{year}.csv')
    df_year['year'] = year
    # Find which pollutants are present in this year's data
    available_pollutants = [p for p in pollutants if p in df_year.columns]
    # Group by station and calculate mean for available pollutants
    station_averages = df_year.groupby('station')[available_pollutants].mean().reset_index()
    station_averages['year'] = year
    # Add missing pollutant columns as NaN
    for p in pollutants:
        if p not in station_averages.columns:
            station_averages[p] = float('nan')
    # Ensure columns are in the same order
    station_averages = station_averages[['station'] + pollutants + ['year']]
    yearly_station_averages.append(station_averages)

# Concatenate all yearly averages
all_station_averages = pd.concat(yearly_station_averages, ignore_index=True)

# Calculate city-wide yearly averages
city_wide_averages = all_station_averages.groupby('year')[pollutants].mean().reset_index()

# Create the interactive plot
fig = go.Figure()

highlight_colors = {
    'SO_2': '#636EFA',
    'CO': '#EF553B',
    'NO_2': '#00CC96',
    'PM10': '#AB63FA',
    'PM25': '#FFA15A',
    'O_3': '#19D3F3'
}
default_gray = 'rgba(180,180,180,0.7)'

# Add a trace for each pollutant (all visible initially, e.g only SO2 colored)
for i, pollutant in enumerate(pollutants):
    fig.add_trace(
        go.Scatter(
            x=city_wide_averages['year'],
            y=city_wide_averages[pollutant],
            name=pollutant,
            mode='lines+markers',
            visible=True,
            line=dict(
                color=highlight_colors[pollutant] if pollutant == 'SO_2' else default_gray,
                width=4 if pollutant == 'SO_2' else 2
            ),
            hovertemplate=f'{pollutant}: %{{y:.2f}} {units[pollutant]}<extra></extra>'
        )
    )

buttons = []

# 1. Highlight Pollutants: Each pollutant highlighted, others gray
for highlight_idx, highlight_pollutant in enumerate(pollutants):
    colors = [highlight_colors[p] if i == highlight_idx else default_gray for i, p in enumerate(pollutants)]
    widths = [4 if i == highlight_idx else 2 for i in range(len(pollutants))]
    buttons.append(
        dict(
            label=f"Highlight {highlight_pollutant}",
            method="update",
            args=[
                {
                    "visible": [True] * len(pollutants),
                    "line.color": colors,
                    "line.width": widths
                },
                {"yaxis": {
                    "title": {"text": "Pollutant Concentration"},
                    "gridcolor": 'rgba(200,200,200,0.3)',
                    "gridwidth": 1,
                }}
            ]
        )
    )

# 2. Pollutants: Only the selected pollutant is shown
for i, pollutant in enumerate(pollutants):
    visible = [False] * len(pollutants)
    visible[i] = True
    buttons.append(
        dict(
            label=f"{pollutant}",
            method="update",
            args=[
                {
                    "visible": visible,
                    "line.color": [highlight_colors[pollutant]],
                    "line.width": [4]
                },
                {"yaxis": {
                    "title": {"text": f"{pollutant} Concentration ({units[pollutant]})"},
                    "gridcolor": 'rgba(200,200,200,0.3)',
                    "gridwidth": 1,
                }}
            ]
        )
    )

# 3. All: All pollutants shown in color
buttons.append(
    dict(
        label="All",
        method="update",
        args=[
            {
                "visible": [True] * len(pollutants),
                "line.color": [highlight_colors[p] for p in pollutants],
                "line.width": [3] * len(pollutants)
            },
            {"yaxis": {
                "title": {"text": "Pollutant Concentration"},
                "gridcolor": 'rgba(200,200,200,0.3)',
                "gridwidth": 1,
            }}
        ]
    )
)

# Update layout with dropdown, and titles
fig.update_layout(
    title={
        'text': 'Evolution of Pollution in Madrid (2001-2018)',
        'x': 0.5,
        'xanchor': 'center'
    },
    xaxis_title='Year',
    yaxis_title='Pollutant Concentration',
    xaxis=dict(
        showgrid=False,
        rangeslider=dict(visible=False),
        type='linear'
    ),
    yaxis=dict(
        gridcolor='rgba(200,200,200,0.3)',
        gridwidth=1
    ),
    updatemenus=[
        dict(
            buttons=buttons,
            direction='down',
            showactive=True,
            x=0.1,
            xanchor='left',
            y=1.1,
            yanchor='top'
        )
    ],
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)
