# -*- coding: utf-8 -*-
"""
Created on Sat Aug 31 16:02:43 2024

@author: Bora
"""

import pandas as pd
import folium
import branca.colormap as cm
from folium.plugins import HeatMap
from folium.features import DivIcon

# Havalimanı uçuş verisini yükleyin
file_path_flight = r'C:\Users\Bora\Desktop\Haj\FlıghtApi\total_flight_counts.csv'
airport_data = pd.read_csv(file_path_flight)

# Ülke ziyaretçi verisini yükleyin
file_path_country = r'C:\Users\Bora\Desktop\Haj\FlıghtApi\Country_Flights_Mutamers_Population.csv'
country_data = pd.read_csv(file_path_country)

# GeoJSON dosyasını yükleyin
geo_json_data =  r'C:\Users\Bora\Desktop\Haj\FlıghtApi\countries.geo.json'

center_lat = df['latitude'].mean()
center_lon = df['longitude'].mean()

# Initialize the map centered globally
m = folium.Map(location=[21.4225, 39.8262], zoom_start=4)

### First Layer: CircleMarker for Flight Counts
flight_layer = folium.FeatureGroup(name="Flight Counts").add_to(m)

# Define color mapping for specific flight count ranges
def get_color(flight_count):
    if flight_count >= 300:
        return 'red'
    elif 120 <= flight_count < 300:
        return 'orange'
    elif 30 <= flight_count < 120:
        return 'yellow'
    else:
        return 'green'

# Add CircleMarkers for each airport
for _, row in airport_data.iterrows():
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=7,  # You can adjust this for visibility
        color=get_color(row['flight_count']),
        fill=True,
        fill_color=get_color(row['flight_count']),
        fill_opacity=0.7
    ).add_to(flight_layer)

### Second Layer: Choropleth for Visitor Numbers
visitor_layer = folium.FeatureGroup(name="Direct Flights Multiplier").add_to(m)

# Fill missing data with 0
country_data_filled = country_data.set_index('name').reindex([feature['properties']['name'] for feature in folium.GeoJson(geo_json_data).data['features']], fill_value=0).reset_index()

folium.Choropleth(
    geo_data=geo_json_data,
    name='Direct Flights Multiplier',
    data=country_data_filled,
    columns=['name', '1445h Direct Flights Multiplier'],  # Update based on actual column names
    key_on='feature.properties.name',  # Match with the 'name' property in GeoJSON
    fill_color='YlOrRd',  # Color scale
    fill_opacity=0.6,
    line_opacity=0.2,
    legend_name='Direct Flights Multiplier',
    threshold_scale=[0, 5, 10, 100, 1000, 10000]  # Custom thresholds
).add_to(m)

### Add Layer Control to Toggle Layers
folium.LayerControl().add_to(m)


### Custom Legend for Flight Counts
flight_legend_html = '''
     <div style="position: fixed;
                 bottom: 50px; left: 10px; width: 200px; height: 160px;
                 background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
                 padding: 10px;">
                 <b>1446h 2m Flight Counts</b><br>
                 <i style="background:red;width:20px;height:20px;display:inline-block;"></i>&nbsp; 300+ Flights<br>
                 <i style="background:orange;width:20px;height:20px;display:inline-block;"></i>&nbsp; 120-300 Flights<br>
                 <i style="background:yellow;width:20px;height:20px;display:inline-block;"></i>&nbsp; 30-120 Flights<br>
                 <i style="background:green;width:20px;height:20px;display:inline-block;"></i>&nbsp; <30 Flights<br>
     </div>
     '''
m.get_root().html.add_child(folium.Element(flight_legend_html))

# Save the map to an HTML file
m.save(r'C:\Users\Bora\Desktop\Haj\FlıghtApi\heatmap_flight_counts_and_multipliers.html')
