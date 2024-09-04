# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 17:36:21 2024

@author: Bora
"""


import pandas as pd
import folium
from folium.plugins import HeatMap
import streamlit as st
from streamlit_folium import st_folium
import geopandas as gpd

st.set_page_config(
    layout="wide",
    page_title="Heatmap",
)

st.markdown(
        """
            <style>
                .appview-container .main .block-container {{
                    padding-top: {padding_top}rem;
                    padding-bottom: {padding_bottom}rem;
                    }}

            </style>""".format(
            padding_top=0.2, padding_bottom=1
        ),
        unsafe_allow_html=True,
)
# Havalimanı uçuş verisini yükleyin
file_path_flight = 'weekly_flight_count.csv'
weekly_flight_data = pd.read_csv(file_path_flight)

file_path_flight_total = 'total_flight_counts.csv'
total_flight_data = pd.read_csv(file_path_flight_total)

# Ülke ziyaretçi verisini yükleyin
file_path_country = 'Country_Flights_Mutamers_Population.csv'
country_data = pd.read_csv(file_path_country)

# GeoJSON dosyasını yükleyin
geo_json_path =  'countries.geo.json'
geo_json_data = gpd.read_file(geo_json_path)

# Convert the 'Week' column to datetime format
weekly_flight_data['Week'] = pd.to_datetime(weekly_flight_data['Week'], format='%Y-%m-%d')

# Extract the unique week dates (no duplicates)
weeks = sorted(weekly_flight_data['Week'].dt.strftime('%Y-%m-%d').unique())

# Streamlit app title
st.title("Country & Flight Heatmap")


# Create columns to place the selections side by side
col1, col2, col3 = st.columns(3)

# Flight data selection (Overall or Weekly)
with col1:
    flight_data_selection = st.radio(
        "Select Period",
        ('Overall', 'Weekly')
    )

# Visualization type selection (Heatmap or Circles)
with col2:
    visualization_type = st.radio(
        "Select Visualization Type for Flights",
        ('Heatmap', 'Circles'),
        index=0  # Heatmap is selected by default
    )

# Second layer data selection (Visitor Numbers or Population)
with col3:
    country_column = st.selectbox(
        "Select Country Metric to Show",
        options=['1445h Direct Flights Multiplier', '1446h 2m Direct Flights Multiplier','Estimated Muslim Population 2023', 'Total Population 2023'],
        index=0 # Assuming these columns exist in the country data
        )
    

# Conditionally display the week selectbox if 'Weekly' is selected
if flight_data_selection == 'Weekly':
    selected_week = st.selectbox("Select Week", options=weeks)
else:
    selected_week = None


# Extract country names from GeoJSON
# Assuming the GeoJSON file has a 'name' field in 'properties' for each feature
geo_countries = geo_json_data['name'].unique()

# Ensure all countries in the GeoJSON are present in the country data
missing_countries = set(geo_countries) - set(country_data['name'])

# Create a DataFrame for the missing countries with 0 values for Visitor_Count and Population
missing_df = pd.DataFrame({
    'name': list(missing_countries),
    'Estimated Muslim Population 2023': 0,
    'Total Population 2023': 0,
    '1445h Direct Flights Multiplier': 0,
    '1446h 2m Direct Flights Multiplier': 0

})

# Append missing countries to the existing country data
country_data = pd.concat([country_data, missing_df], ignore_index=True)
    
# Define threshold scales 

muslim_pop_thresholds = country_data['Estimated Muslim Population 2023'].quantile([0.35, 0.65, 0.90]).tolist()
muslim_pop_thresholds = [0] + muslim_pop_thresholds + [country_data['Estimated Muslim Population 2023'].max()]

total_pop_thresholds = country_data['Total Population 2023'].quantile([0.35, 0.65, 0.90]).tolist()
total_pop_thresholds = [0] + total_pop_thresholds + [country_data['Total Population 2023'].max()]

multiplier_thresholds = [0, 5, 100, 1000, 100000]

# Select appropriate thresholds based on the selected country data column
if country_column == 'Estimated Muslim Population 2023':
    threshold_scales = muslim_pop_thresholds
elif country_column == 'Total Population 2023':
    threshold_scales = total_pop_thresholds
elif country_column == '1445h Direct Flights Multiplier':
     threshold_scales = multiplier_thresholds   
elif country_column == '1446h 2m Direct Flights Multiplier':
    threshold_scales = multiplier_thresholds
    
# Ensure all thresholds are integers
threshold_scales = [int(threshold) for threshold in threshold_scales]

# Function to determine circle color based on flight count and data selection
def get_color(flight_count, is_overall):
    if is_overall:
        # Different thresholds for overall data
        if flight_count >= 300:
            return 'darkblue'
        elif 120 <= flight_count < 300:
            return 'blue'
        elif 30 <= flight_count < 120:
            return 'lightblue'
        else:
            return 'lightblue'
    else:
        # Different thresholds for weekly data
        if flight_count >= 30:
            return 'darkblue'
        elif 14 <= flight_count < 30:
            return 'blue'
        elif 7 <= flight_count < 14:
            return 'lightblue'
        else:
            return 'lightblue'
    
# Function to generate the map
def generate_map(week, vis_type, flight_data_selection, country_column):
    # Initialize the map centered on Mecca, Saudi Arabia
    m = folium.Map(location=[24.4225, 37.8262], zoom_start=4)

    # Choose the appropriate flight data
    if flight_data_selection == 'Weekly':
        # Convert selected week back to datetime format
        week = pd.to_datetime(week)
        flight_data = weekly_flight_data[weekly_flight_data['Week'] == week]
        is_overall = False
    else:
        flight_data = total_flight_data
        is_overall = True

    ### Visualization for Flight Counts
    if vis_type == 'Heatmap':
        # Create the heatmap with custom gradient
        heat_data = [
            [row['latitude'], row['longitude'], row['flight_count']] for index, row in flight_data.iterrows()
        ]
        HeatMap(
            heat_data,
            radius=15,
        ).add_to(m)
    elif vis_type == 'Circles':
        # Add CircleMarkers to the map with colors based on flight count
        for index, row in flight_data.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=row['flight_count'] / (75 if is_overall else 10),  # Scale radius differently for overall vs weekly
                color=get_color(row['flight_count'], is_overall),  # Get color based on flight count and selection
                fill=True,
                fill_color=get_color(row['flight_count'], is_overall),
                fill_opacity=0.6
            ).add_to(m)

    ### Second Layer: Choropleth for Selected Country Data
    folium.Choropleth(
        geo_data=geo_json_data,  # Path to the uploaded GeoJSON file
        name=f'{country_column}',
        data=country_data,
        columns=['name', country_column],
        key_on='feature.properties.name',
        fill_color='YlOrRd',
        fill_opacity=0.6,
        line_opacity=0.2,
        legend_name=f'{country_column}',
        threshold_scale=threshold_scales
    ).add_to(m)
    
    ### Custom Legend
    legend_html = '''
     <div style="position: fixed; 
                 bottom: 50px; left: 50px; width: 300px; height: 150px; 
                 background-color: white; z-index:9999; font-size:14px; 
                 border:2px solid grey; padding: 10px;">
     &nbsp;<b>{}</b><br>
    '''.format(country_column)

    # Dynamically create legend entries based on available thresholds
    for i in range(len(threshold_scales) - 1):
        legend_html += '&nbsp;<i style="background: #f7fcf0"></i>&nbsp; {} - {} <br>'.format(threshold_scales[i], threshold_scales[i+1])

    legend_html += '&nbsp;<i style="background: #7bccc4"></i>&nbsp; {}+ <br></div>'.format(threshold_scales[-1])

    m.get_root().html.add_child(folium.Element(legend_html))

    ### Add Layer Control
    folium.LayerControl().add_to(m)

    # Display the map in Streamlit
    #st_folium(m, width=1200, height=700)
    st_folium(m, use_container_width=True)

# Generate the map based on user selections
generate_map(selected_week, visualization_type, flight_data_selection, country_column)
