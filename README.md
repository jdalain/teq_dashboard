# Türkiye Earthquake Dashboard

Earthquake data dashboard based on [AFAD](https://deprem.afad.gov.tr/home-page)'s (The Turkish Disaster and Emergency Management Presidency) data.

This is a Python script that creates a dashboard for monitoring earthquakes in Turkey. The script uses Streamlit to create the dashboard and requests, json, pandas, datetime, and plotly.express libraries to gather, process, and visualize earthquake data.

Starts by setting the base URL for the API and defining a function to get earthquake data for a given date range. The function sends a request to the API and converts the response content into a pandas dataframe. The dataframe is then filtered for Turkey and the date and time columns are extracted and formatted.

A Streamlit web dashboard is created to include visual reporesntation of the data, in addition to sidebar sliders for selecting date and magnitude ranges. 

Exporting the filtered data to a CSV file also added added. 
