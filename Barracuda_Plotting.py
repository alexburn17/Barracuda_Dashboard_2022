import pandas as pd
from pandas.api.types import is_numeric_dtype
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import datetime
import statsmodels.api as sm
from Barracuda_Styles import STYLES
#######################################################################################################################


# Primary Plotting Functions
#######################################################################################################################
def default_chart(message="Click drag on the map to select counties"):
    fig = go.Figure(
        data=[],
        layout=dict(
            title=message,
            paper_bgcolor=STYLES["chart_background"],
            plot_bgcolor=STYLES["chart_background"],
            font=dict(color=STYLES["font"]),
            margin=STYLES['margins'],
        )
    )
    return fig


# Creates a simple line plot.
def plot_line(df, time_val, y_val, label):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[time_val],
        y=df[y_val],
        mode='lines+markers',
        line={'color': STYLES['line_colors'][0]},
        showlegend=False
    ))

    fig_layout = style_figure(fig['layout'], label)
    fig.layout.width = 660

    return fig


# Creates a control chart plotly figure based on the input DataFrame and parameters
def plot_control(dataframe, segments, y_col, time_key, label, show_all, flags):

    fig = go.Figure()

    # Base line trace for the markers to sit on top of
    fig.add_trace(go.Scatter(x=dataframe[time_key],
                             y=dataframe[y_col],
                             mode='lines',
                             line_color=flags["base"][0],
                             showlegend=False))

    print_trend = True

    # loop to generate a trace for each flag
    for d in flags:
        if flags[d][1] == 1:
            if (d == 'trending up' or d == 'trending down') and print_trend:
                fig = plot_trends(fig, dataframe, segments, y_col, time_key, show_all, flags)
                print_trend = False

            # For all non-trend data, we use scatter plot markers.
            elif d not in ['trending up', 'trending down']:
                d_filter = d + ' mask'
                df = dataframe.loc[dataframe[d_filter] == 1]
                fig.add_trace(go.Scatter(x=df[time_key],
                                         y=df[y_col],
                                         mode='markers',
                                         name=d,
                                         marker_color=flags[d][0],
                                         showlegend=False if d == 'base' else True))

    # Line indicating average value of the dataset
    fig.add_shape(type="line",
                  line_color='blue',
                  line_width=2,
                  line_dash='dot',
                  x0=0,
                  x1=1,
                  xref='paper',
                  y0=np.average(dataframe[y_col]),
                  y1=np.average(dataframe[y_col]),
                  yref='y'
                  )

    fig_layout = style_figure(fig['layout'], label)
    fig.layout.width = 660


    return fig


# Create statespace figure
def plot_statespace(df, time_val, lat_val, lon_val, label):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[time_val],
        y=df[lat_val],
        mode='lines',
        name="Latitude",
    ))
    fig.add_trace(go.Scatter(
        x=df[time_val],
        y=df[lon_val],
        mode='lines',
        name="Longitude",
    ))

    fig_layout = style_figure(fig['layout'], label)
    fig.layout.width = 660

    return fig


# Creates Choropleth figure
def plot_choropleth(dataframe, dataframe_label, data_label, data_json, years, counties, address, zips_df):

    if data_json[dataframe_label]['space_type'] == 'latlong':

        lat = 43
        lon = -74
        zoom = 4.5

        if ',' in address:
            addressSplit = address.split(",") # split address by comma

            # get row of data frame based on city and state
            coords = zips_df[(zips_df['city'] == addressSplit[0]) & (zips_df['state_id'] == addressSplit[1].strip())].head(1)
            lat = float(coords["lat"]) # get coords
            lon = float(coords["lon"]) # get coords
            zoom = 9


        dataframe['timeChar'] = dataframe[data_json[dataframe_label]['temporal_key']].astype('str')
        max_val = np.nanmax(dataframe[data_label])


        fig = px.scatter_mapbox(dataframe, lat=data_json[dataframe_label]['space_keys'][0],
                                lon=data_json[dataframe_label]['space_keys'][1],
                                color=data_label,
                                animation_frame='timeChar',
                                range_color=(0, max_val),
                                color_continuous_scale="Viridis",
                                opacity=0.8,
                                )

        # Choropleth Layout
        fig.update_layout(mapbox_style="carto-darkmatter", mapbox_zoom=zoom, mapbox_center={"lat": lat, "lon": lon}, )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 20, "b": 0},
                          plot_bgcolor=STYLES["chart_background"],
                          paper_bgcolor=STYLES["chart_background"],
                          font=dict(color=STYLES["font"]),
                          # dragmode="lasso",
                          )

        unique_times = len(pd.unique(dataframe['timeChar']))

        fig.layout.height = 600
        fig.layout.coloraxis.showscale = True

        if unique_times > 1:
            fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 200
            fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 200
            fig.layout.sliders[0].pad.t = 10
            fig.layout.updatemenus[0].pad.t = 10

    else:

        lat = 34.640033
        lon = -95.981758
        zoom = 2.9

        if ',' in address:
            addressSplit = address.split(",") # split address by comma

            # get row of data frame based on city and state
            coords = zips_df[(zips_df['city'] == addressSplit[0]) & (zips_df['state_id'] == addressSplit[1].strip())].head(1)
            lat = float(coords["lat"]) # get coords
            lon = float(coords["lon"]) # get coords
            zoom = 9

        # Find max value for heat map bar
        max_val = max(dataframe[data_label])

        if data_json[dataframe_label]['dataset_label'] != 'Annual Weather Data':


            dataframe['timeChar'] = dataframe[data_json[dataframe_label]['temporal_key']].astype('str')

            fig = px.choropleth_mapbox(dataframe, geojson=counties, locations='fips', color=data_label,
                               color_continuous_scale="Viridis",
                               range_color=(0, max_val),
                               animation_frame='timeChar',
                               mapbox_style="carto-darkmatter",
                               zoom=zoom, center={"lat": lat, "lon": lon},
                               opacity=0.9,
                               labels={data_label: ' ', 'time': 'Time', 'Counties': 'County Code'}
                               )
        else:

            # filter by year
            dataframe = dataframe[(dataframe[data_json[dataframe_label]['temporal_key']] == years)]
            fig = px.choropleth_mapbox(dataframe, geojson=counties, locations='fips', color=data_label,
                           color_continuous_scale="Viridis",
                           range_color=(0, max_val),
                           mapbox_style="carto-darkmatter",
                           zoom=zoom, center={"lat": lat, "lon": lon},
                           opacity=0.9,
                           labels={data_label: ' ', 'time': 'Time', 'Counties': 'County Code'}
                           )

        fig.update_layout(margin={"r": 0, "t": 0, "l": 20, "b": 0},
                          geo_scope='usa',
                          plot_bgcolor=STYLES["chart_background"],
                          paper_bgcolor=STYLES["chart_background"],
                          font=dict(color=STYLES["font"]),
                          height=600,
                          )

    return fig
#######################################################################################################################


# Helper Functions
#######################################################################################################################
# Add trend lines to figure, plots trend lines of imported segments for the dataset.
def plot_trends(fig, df_plot, segments, y_col, time_key, show_all, flags):

    for start_idx, end_idx in zip(segments[:-1], segments[1:]):
        segment = df_plot.iloc[start_idx:end_idx + 1, :].copy()

        # Serialize the temporal column if it isn't already numeric
        if not is_numeric_dtype(segment[time_key]):
            segment['serial_time'] = [(d - datetime.datetime(1970, 1, 1)).days for d in segment[time_key]]
        else:
            segment['serial_time'] = segment[time_key]

        x = sm.add_constant(segment['serial_time'])
        model = sm.OLS(segment[y_col], x).fit()
        segment['fitted_values'] = model.fittedvalues

        fit_color = flags['trending up'][0] if model.params['serial_time'] > 0 \
            else flags['trending down'][0]

        trend_name = "Trending Up" if model.params['serial_time'] > 0 else "Trending Down"

        # Determine whether the current segment should be printed or not.
        print_trend = False

        if show_all:
            if (flags['trending up'][1] == 1 and model.params['serial_time'] > 0) \
                    or (flags['trending down'][1] == 1 and model.params['serial_time'] <= 0):
                print_trend = True
            else:
                pass
        else:
            if model.f_pvalue < 0.05:
                if (flags['trending up'][1] == 1 and model.params['serial_time'] > 0) \
                        or (flags['trending down'][1] == 1 and model.params['serial_time'] <= 0):
                    print_trend = True
                else:
                    pass
            else:
                pass

        if print_trend:
            fig.add_trace(go.Scatter(
                x=segment[time_key],
                y=segment['fitted_values'],
                mode='lines',
                line=dict(color=fit_color),
                name=trend_name,
            ))

    # Ensure duplicate legend items get removed
    legend_names = set()
    fig.for_each_trace(
        lambda trace:
        trace.update(showlegend=False) if (trace.name in legend_names) else legend_names.add(trace.name)
    )

    return fig


# Figure Style Information
def style_figure(layout, title):
    fig_layout = layout

    # See plot.ly/python/reference
    fig_layout["yaxis"]["title"] = title
    fig_layout["xaxis"]["title"] = "Time"
    fig_layout["yaxis"]["fixedrange"] = True
    fig_layout["xaxis"]["fixedrange"] = False
    fig_layout["hovermode"] = "closest"
    fig_layout["legend"] = dict(orientation="v")
    fig_layout["autosize"] = False
    fig_layout["height"] = 600
    fig_layout["width"] = 601
    fig_layout["paper_bgcolor"] = STYLES["chart_background"]
    fig_layout["plot_bgcolor"] = STYLES["chart_background"]
    fig_layout["font"]["color"] = STYLES["font"]
    fig_layout["xaxis"]["tickfont"]["color"] = STYLES["tick_font"]
    fig_layout["yaxis"]["tickfont"]["color"] = STYLES["tick_font"]
    fig_layout["xaxis"]["gridcolor"] = STYLES["chart_grid"]
    fig_layout["yaxis"]["gridcolor"] = STYLES["chart_grid"]
    fig_layout["margin"] = STYLES['margins']

    return fig_layout
#######################################################################################################################
