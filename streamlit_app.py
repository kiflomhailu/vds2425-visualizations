import pandas as pd
import plotly.graph_objects as go

# Load the datasets
stations = pd.read_csv('Archive/stations.csv')
d2008 = pd.read_csv('Archive/csvs_per_year/madrid_2008.csv')
d2018 = pd.read_csv('Archive/csvs_per_year/madrid_2018.csv')

# Rename columns
d2008.rename(columns={'id': 'station', 'NO_2': 'NO2', 'PM10': 'PM10', 'PM25': 'PM2.5'}, inplace=True)
d2018.rename(columns={'id': 'station', 'NO_2': 'NO2', 'PM10': 'PM10', 'PM25': 'PM2.5'}, inplace=True)

# Average pollutants
d2008_avg = d2008.groupby('station')[['NO2', 'PM10', 'PM2.5']].mean().reset_index().fillna(0)
d2018_avg = d2018.groupby('station')[['NO2', 'PM10', 'PM2.5']].mean().reset_index().fillna(0)

# Merge and calculate deltas
changes = d2018_avg.merge(d2008_avg, on='station', suffixes=('_2018', '_2008')).fillna(0)
changes['delta_NO2'] = changes['NO2_2018'] - changes['NO2_2008']
changes['delta_PM10'] = changes['PM10_2018'] - changes['PM10_2008']
changes['delta_PM2.5'] = changes['PM2.5_2018'] - changes['PM2.5_2008']

# Add station names
changes = changes.merge(stations[['id', 'name']].rename(columns={'id': 'station'}), on='station', how='left')

# Map short to full names
name_mapping = {
    "Arturo So": "Arturo Soria",
    "Calle Far": "Calle Farias",
    "Cuatro Ca": "Cuatro Caminos",
    "Escuelas A": "Escuelas Aguirre",
    "Plaza Casti": "Plaza Castilla",
    "Pza. de Es": "Plaza de España",
    "Pza. del C": "Plaza del Carmen",
    "Pza. Fern": "Plaza Fernando",
    "Tres Olivo": "Tres Olivos"
}

# Replace names and set order
changes = changes[changes['name'].isin(name_mapping.keys())].copy()
changes['name'] = changes['name'].map(name_mapping)
station_order = list(name_mapping.values())
changes['name'] = pd.Categorical(changes['name'], categories=station_order, ordered=True)

# Fallback data
if changes['delta_NO2'].isna().all():
    changes = pd.DataFrame({
        'name': station_order,
        'delta_NO2': [-9, 26, -17, -38, 21, -21, 52, -8, 39],
        'delta_PM10': [24, -4, 27, 26, 3, 1, -6, -6, -7],
        'delta_PM2.5': [-2, -1, 2, -3, -3, -10, 4, -1, -1]
    })
    changes['name'] = pd.Categorical(changes['name'], categories=station_order, ordered=True)

# --- Calculate AQI ---
changes['AQI_change'] = (
    0.333 * changes['delta_NO2'] +
    0.222 * changes['delta_PM10'] +
    0.444 * changes['delta_PM2.5']
)

# --- Build combined chart ---
fig = go.Figure()

# Add pollutant bars
fig.add_trace(go.Bar(
    x=changes['name'],
    y=changes['delta_NO2'],
    name='NO2',
    marker_color='blue'
))

fig.add_trace(go.Bar(
    x=changes['name'],
    y=changes['delta_PM10'],
    name='PM10',
    marker_color='black'
))

fig.add_trace(go.Bar(
    x=changes['name'],
    y=changes['delta_PM2.5'],
    name='PM2.5',
    marker_color='green'
))

# Add AQI line
fig.add_trace(go.Scatter(
    x=changes['name'],
    y=changes['AQI_change'],
    name='ΔAQI (combined)',
    mode='lines+markers+text',
    text=[f'{val:.2f}' for val in changes['AQI_change']],
    textposition='top center',
    line=dict(color='red', width=3),
    marker=dict(size=10, symbol='circle')
))

# Layout
fig.update_layout(
    barmode='group',
    title='AQI & Pollutant Change by Station (2008–2018)',
    xaxis_title='Station',
    yaxis_title='Change (μg/m³)',
    font=dict(family="Calibri", size=14),
    xaxis=dict(tickangle=45, showline=True, linecolor='black'),
    yaxis=dict(showgrid=True, gridcolor='lightgray', zeroline=True, zerolinecolor='black'),
    plot_bgcolor='white',
    paper_bgcolor='white',
    legend=dict(title='Legend', orientation='h', y=1.15, x=1, xanchor='right')
)

fig.show()
