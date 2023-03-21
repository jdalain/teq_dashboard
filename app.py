# import the required libraries
import streamlit as st
import requests
import json
import pandas as pd
import datetime
import plotly.express as px

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
    
    # convert the response content into JSON format
    data = json.loads(response.content)
    
    # convert the response content to a pandas dataframe
    df_r = pd.DataFrame(data)
    
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
    format="MM/DD/YYYY"
)

# get the earthquake data for the selected date range
start_date_sel = datetime.datetime.combine(date_range[0], datetime.time.min)
end_date_sel = datetime.datetime.combine(date_range[1], datetime.time.max)
df = get_earthquake_data(start_date_sel, end_date_sel)

# export the dataframe to a CSV file
df.to_csv("earthquake_data.csv", index=False)

# create a sidebar slider for magnitude
# magnitude = st.sidebar.slider('Select a magnitude range', min_value=1, max_value=8, value=8, step=1)
magnitude = st.sidebar.slider('Select a magnitude range', 0.0, 8.0, (0.0,8.0), step=0.1)
df = df[(df['magnitude'].astype(float) >= magnitude[0]) & (df['magnitude'].astype(float) <= magnitude[1])]

# sidebar - Metric - Filter data for earthquakes after Feb-6
start_date = datetime.datetime.strptime('2023-02-06', '%Y-%m-%d').date()
start_time = datetime.datetime.strptime('01:17:32', '%H:%M:%S').time()
data = df[(df['date_s'] >= start_date) & (df['GMT_time'] >= start_time)]
total_quakes = len(data)-2 #removing the 2 earthquakes recoreded earlier on Feb-6
st.sidebar.metric("Total Earthquakes Count", total_quakes)

# compute time differences between earthquakes
df = df.sort_values("date_s")
df["time_diff"] = df["date_s"].diff().apply(lambda x: x.total_seconds() / 60)
df = df.dropna(subset=["time_diff"])
time_diff_avg = df.groupby(df["date_s"])["time_diff"].mean() # group by date and compute average time difference

# compute time differences between earthquakes in the past 24 hours
df_last_24_hours = df[df.index >= datetime.datetime.now() - datetime.timedelta(hours=24)]
time_between_last_24_hours = df_last_24_hours.index.to_series().diff().dt.total_seconds().div(60)
avg_time_between_last_24_hours = round(time_between_last_24_hours.mean())
st.sidebar.metric("Average Time Between Earthquakes (last 24 hours)", f"{int(avg_time_between_last_24_hours//60):02d}:{int(avg_time_between_last_24_hours % 60):02d}:{int(avg_time_between_last_24_hours //60 % 60):02d}")

# sidebar - Metric - Average time between earthquakes over time (detailed)
avg_time_diff = df_last_24_hours.index.to_series().diff().mean()
st.sidebar.write(avg_time_diff)

# scatter mapbox plot of earthquake locations
df["magnitude_num"] = pd.to_numeric(df["magnitude"]) # convert magnitude to numeric
df_sorted = df.sort_values("magnitude_num", ascending=True) # sort dataframe by magnitude
st.subheader("Earthquake Locations with Magnitude Map")
fig = px.scatter_mapbox(df_sorted, lat="latitude", lon="longitude", color="magnitude_num", size="magnitude_num",
hover_name="location", opacity = 0.7,
color_continuous_scale=px.colors.sequential.Burgyl, size_max=10, zoom=5)
fig.update_layout(mapbox_style="open-street-map")
st.plotly_chart(fig)

# line chart of earthquake magnitudes over time
st.subheader("Magnitude Over Time (average)")
df['magnitude'] = pd.to_numeric(df['magnitude'], errors='coerce')
df.dropna(subset=['magnitude'], inplace=True)
mag_over_time = df["magnitude"].resample("D").max()
st.area_chart(mag_over_time)

# create a bar chart of earthquake magnitudes
st.subheader("Magnitude Distribution (count)")
mag_counts = df["magnitude"].value_counts()
st.bar_chart(mag_counts)

# plot the average time difference over time chart
st.subheader("Average Time Between Earthquakes (minutes)")
st.line_chart(time_diff_avg)

# show the 10 strongest earthquakes
st.header("10 Strongest Earthquakes")
with st.expander('10 Strongest Earthquakes Table', expanded=False):
    st.table(df.sort_values("magnitude", ascending=False).head(10))

# download button
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

csv = convert_df(df)
st.sidebar.text(" ")
st.sidebar.download_button(
    label="Download data as CSV",
    data=csv,
    file_name='earthquake_data.csv',
    mime='text/csv',
)
st.sidebar.markdown("Data source: [AFAD](https://deprem.afad.gov.tr/home-page)")

