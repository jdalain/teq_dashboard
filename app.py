import datetime
import json

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# set the base URL for the API
url = "https://deprem.afad.gov.tr/apiv2/event/filter?"

# create a function to get earthquake data for a given date range
@st.cache_data
def get_earthquake_data(start_date, end_date):
    # format the dates in the required format
    start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
    # set the API parameters
    params = {
        "start": start_date_str,
        "end": end_date_str
    }
    # send the request to the API
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    # convert the response content into JSON format
    data = response.json()
    
    # convert the response content to a pandas dataframe
    df_r = pd.read_json(json.dumps(data))
    
    # filter data for Turkey
    df = df_r[df_r['country'] == ('Türkiye')].copy()
    
    # extract the date and time columns
    df["date"] = pd.to_datetime(df["date"])
    df["date_s"] = df["date"].dt.date
    df["GMT_time"] = df["date"].dt.time
    df["IST_time"] = (df["date"] + pd.Timedelta(hours=3)).dt.time
    df = df.set_index("date")
    
    # convert latitude and longitude columns to numeric
    df["latitude"] = pd.to_numeric(df["latitude"])
    df["longitude"] = pd.to_numeric(df["longitude"])
    return df

# set the default date range to start on Feb-6
end_date = datetime.datetime.now()
start_date = datetime.datetime.strptime('2023-02-06', '%Y-%m-%d')

# dashboard
# create the streamlit web dashboard
st.title("Türkiye Earthquakes Dashboard")

# create a sidebar slider for date
date_range = st.sidebar.slider(
    "Select a date range",
    value=(start_date.date(), end_date.date()),
    format="MM/DD/YYYY",
    key="date_slider"
)

# get the earthquake data for the selected date range
start_date_sel = datetime.datetime.combine(date_range[0], datetime.time.min)
end_date_sel = datetime.datetime.combine(date_range[1], datetime.time.max)
df = get_earthquake_data(start_date_sel, end_date_sel)

# export the dataframe to a CSV file
df.to_csv("earthquake_data.csv", index=False)

# create a sidebar slider for magnitude
magnitude_range = st.sidebar.slider('Select a magnitude range', 0.0, 8.0, (0.0,8.0), step=0.1)

# filter the dataframe based on the selected magnitude range
df_filtered = df[(df['magnitude'].astype(float) >= magnitude_range[0]) & (df['magnitude'].astype(float) <= magnitude_range[1])]

# display the total count of earthquakes in the filtered dataframe
st.sidebar.metric("Total Earthquakes Count", len(df_filtered))


# compute time differences between earthquakes
df_filtered = df_filtered.sort_values("date_s")
df_filtered["time_diff"] = df_filtered["date_s"].diff().apply(lambda x: x.total_seconds() / 60)
df_filtered = df_filtered.dropna(subset=["time_diff"])
time_diff_avg = df_filtered.groupby(df_filtered["date_s"])["time_diff"].mean() # group by date and compute average time difference
df["time_diff"] = df["date_s"].diff().apply(lambda x: x.total_seconds() / 60)


df_last_24_hours = df[df.index >= datetime.datetime.now() - datetime.timedelta(hours=24)]
time_between_last_24_hours = df_last_24_hours["time_diff"]
if not time_between_last_24_hours.empty and time_between_last_24_hours.notna().all():
    avg_time_between_last_24_hours = round(time_between_last_24_hours.mean())
    minutes, seconds = divmod(avg_time_between_last_24_hours, 60)
    hours, minutes = divmod(minutes, 60)
    # sidebar - Metric - Average time between earthquakes over time (detailed)
    avg_time_diff = df_last_24_hours.index.to_series().diff().mean()
    st.sidebar.write("Average Time Between Earthquakes (last 24 hours)", avg_time_diff)
# st.sidebar.metric("Average Time Between Earthquakes (last 24 hours)", f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
else:
    st.sidebar.warning("No data available for the selected filters.")

# scatter mapbox plot of earthquake locations
df_filtered["magnitude_num"] = pd.to_numeric(df_filtered["magnitude"]) # convert magnitude to numeric
df_sorted = df_filtered.sort_values("magnitude_num", ascending=True) # sort dataframe by magnitude
st.subheader("Earthquake Locations with Magnitude Map")
fig = px.scatter_mapbox(df_sorted, lat="latitude", lon="longitude", color="magnitude_num", size="magnitude_num",
hover_name="location", opacity = 0.7,
color_continuous_scale=px.colors.sequential.Burgyl, size_max=10, zoom=5)
fig.update_layout(mapbox_style="open-street-map")
st.plotly_chart(fig)

# line chart of earthquake magnitudes over time
st.subheader("Magnitude Over Time (average)")
df_filtered['magnitude'] = pd.to_numeric(df_filtered['magnitude'], errors='coerce')
df_filtered.dropna(subset=['magnitude'], inplace=True)
mag_over_time = df_filtered["magnitude"].resample("D").max()
st.area_chart(mag_over_time)

# create a bar chart of earthquake magnitudes
st.subheader("Magnitude Distribution (count)")
mag_counts = df_filtered["magnitude"].value_counts()
st.bar_chart(mag_counts)

# plot the average time difference over time chart
st.subheader("Average Time Between Earthquakes (minutes)")
st.line_chart(time_diff_avg)

# show the 10 strongest earthquakes
st.header("10 Strongest Earthquakes")
with st.expander('10 Strongest Earthquakes Table', expanded=False):
    st.table(df_filtered.sort_values("magnitude", ascending=False).head(10))

# download button
def convert_df(df_filtered):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df_filtered.to_csv().encode('utf-8')

csv = convert_df(df_filtered)
st.sidebar.text(" ")
st.sidebar.download_button(
    label="Download data as CSV",
    data=csv,
    file_name='earthquake_data.csv',
    mime='text/csv',
)
st.sidebar.markdown("Data source: [AFAD](https://deprem.afad.gov.tr/home-page)")