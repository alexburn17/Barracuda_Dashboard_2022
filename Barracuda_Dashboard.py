# Barracuda Dashboard
# Authors: Alex Burnham, Quinlan Dubois
# Latest Revision: 0.2.4
# Latest Revision Date: 10/30/2022


# File Header containing imports, constants, and start-up processing.
########################################################################################################################
import pathlib
import json
import numpy as np
from urllib.request import urlopen
import dash
from dash import dcc
from dash import html
import dash_loading_spinners as dls
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import time
import os
from flask_caching import Cache

from App import app
from App import server

from Barracuda_Processing import control_sort, aggregate_dataframe
from Barracuda_Plotting import default_chart, plot_line, plot_control, plot_choropleth, plot_statespace, plot_hist, plot_bar
from Barracuda_Styles import data_styles

DEFAULT_OPACITY = 0.8

# Load data
APP_PATH = str(pathlib.Path(__file__).parent.resolve())

# set mapbox token and style
mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A"
mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"

# read in fips shape data
file = open("data/geojson-counties-fips.json")
counties = json.load(file)

# Dataset Loader
#     - A new line needs to be added here when a new dataset is added to the dashboard
#############################################################################
# read in climate data
data_annual_climate = "data/output.csv"
df_annual_climate = pd.read_csv(data_annual_climate, dtype={'fips': str})

# read in kestral range shift data
data_kestral_model = "data/kestralModel.csv"
df_kestral_model = pd.read_csv(data_kestral_model)

# read in carya ovata range shift data
data_carya_ovata = "data/Carya_ovata.csv"
df_carya_ovata = pd.read_csv(data_carya_ovata)

# read in carya ovata range shift data
zips = "data/zips_dash.csv"
zips_df = pd.read_csv(zips)

# read in carya ovata range shift data imported from spacetime API
crop_climate_trends_spacetime = "data/crop_climate_trends.csv"
df_crop_climate_trends_spacetime = pd.read_csv(crop_climate_trends_spacetime, dtype={'fips': str})
df_crop_climate_trends_spacetime["time"] = 1


# read in carya ovata range shift data imported from spacetime API
pest = "data/pestAtlas.csv"
df_pest = pd.read_csv(pest)

cm = "data/crop_model.csv"
df_cm = pd.read_csv(cm)

# read in crop switching
crop_switching = "data/crop_switching.csv"
df_crop_switching = pd.read_csv(crop_switching)

#############################################################################

# Import Data labels JSON
data_json_path = "data/dataset-names.json"
data_json_dict = {}
try:
    with open(data_json_path) as json_file:
        data_json_dict = json.load(json_file)
except json.JSONDecodeError as error:
    print(">>> JSON ERROR: JSON empty or invalid structure. Dataframe Selectors will not work properly! <<<")
    data_json_dict = {}
except FileNotFoundError as error:
    print(
        ">>> JSON ERROR: JSON " + data_json_path + " does not exist. Dataframe Selectors will not work properly! <<<")
    data_json_dict = {}

# Create dropdown list for datasets
dataset_options = []
for key in data_json_dict.keys():
    dataset_options.append(
        {'label': data_json_dict[key]['dataset_label'],
         'value': key}
    )

# Create list of control chart selectors for checklist
data_style_options = []
for key in data_styles:
    data_style_options.append({'label': key, 'value': key})

########################################################################################################################


cache = Cache(app.server, config={
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})
app.config.suppress_callback_exceptions = True

timeout = 300

# App layout
########################################################################################################################
app.layout = html.Div(
    id="root",
    children=[
        # App Header
        html.Div(
            id="header",
            children=[
                html.A(
                    html.Img(id="logo", src=app.get_asset_url("barracuda_logo_final.png")),
                    href="https://www.uvm.edu/",
                ),
                html.H4(children=" Barracuda Data Visualization Dashboard"),
                html.P(
                    id="description",
                    children="Biodiversity and Rural Response to Climate Change Using Data Analysis",
                ),
            ],
        ),

        # App Container
        html.Div(
            id="app-container", className="container",
            children=[

                # Left Column: For desktop, groups data selectors and Choropleth map together visually
                ########################################################################################################


                html.Div(
                    id="left-column", className="inner-container",
                    children=[

                        # Panel for data selector dropdowns
                        html.Div(
                            id="dropdown-container", className="panel",
                            children=[
                                html.P(id="dataframe-title", children="Select a Dataset"),
                                dcc.Dropdown(
                                    options=dataset_options,
                                    value='output.csv',
                                    id="dataframe-dropdown"
                                ),

                                html.Div(
                                    id="left-column-small", className="small-inner-container",
                                    children=[
                                        html.P(id="data-title", children="Select a Variable to Plot"),
                                            dcc.Dropdown(
                                                options=[
                                                    {
                                                    "label": "Average of Nighttime Minimum Temperature, (deg. C)",
                                                    "value": "tmin",
                                                    },
                                                    {
                                                    "label": "Average of Daytime High Temperature, (deg. C)",
                                                    "value": "tmax",
                                                    },
                                                    {
                                                    "label": "Average of Daily Mean Temperature, (deg. C)",
                                                    "value": "tmean",
                                                    },
                                                    {
                                                    "label": "Total Annual Precipitation, (mm)",
                                                    "value": "prec",
                                                    },
                                                    {
                                                    "label": "Total April Precipitation, (mm)",
                                                    "value": "aprec",
                                                    },
                                                    {
                                                    "label": "Length of Frost Free Period, (days)",
                                                    "value": "ffp",
                                            },
                                        ],
                                        value="tmin",
                                        id="data-dropdown",
                                        style={"width": "100%"},
                                        ),

                                        html.P(id="address-input", children="Type in Your City and State and Hit Return"),
                                            dcc.Input(
                                                id="address",
                                                autoComplete = 'on',
                                                placeholder="ex. Burlington, VT",
                                                type="text",
                                                value="",
                                                debounce=True,
                                                style={"width": "100%"},
                                        ),

                                    ],

                                ),

                            ],

                        ),



                        # Panel for Choropleth, includes Year Slider
                        html.Div(

                            id="choropleth-panel", className="panel",

                            children=[
                                html.Div(
                                    id="heatmap-container",
                                    children=[
                                        html.P(
                                            "Heatmap Over Time (Select Year Below Map)",
                                            id="heatmap-title", className="panel-title"
                                        ),
                                        dcc.Loading(dcc.Graph(
                                            id="county-choropleth", className="chart-content",
                                            figure=dict(
                                                layout=dict(
                                                    mapbox=dict(
                                                        layers=[],
                                                        accesstoken=mapbox_access_token,
                                                        style=mapbox_style,
                                                        center=dict(
                                                            lat=38.72490, lon=-95.61446
                                                        ),
                                                        pitch=0,
                                                        zoom=3.5,
                                                    ),

                                                    autosize=True,

                                                ),
                                            ),
                                        ), type="dot",
                                        ),
                                    ],
                                ),


                                html.Div(
                                    id="year-container",
                                    children=[
                                        html.P(id="year-title", children="Select a Year to Plot"),
                                        dcc.Slider(
                                            value=1950,
                                            min=1950,
                                            max=2019,
                                            step=1,
                                            marks={
                                                1950: {'label': '1950'},
                                                1967: {'label': '1967'},
                                                1985: {'label': '1985'},
                                                2002: {'label': '2002'},
                                                2019: {'label': '2019'},
                                            },
                                            tooltip={"placement": "bottom", "always_visible": True},
                                            id="year-slider",
                                        ),
                                    ],
                                ),
                            ]
                        ),
                    ],
                ),
                ########################################################################################################

                # Right Column: For desktop, groups chart selector, charts, and chart controls together visually
                ########################################################################################################
                html.Div(
                    id="right-column", className="inner-container",
                    children=[

                        # Panel for chart selectors
                        html.Div(
                            id='chart-selector', className="panel",
                            children=[
                                html.P(id="chart-select-title", children="Select the chart you would like to display."),
                                html.Div(
                                    children=[
                                        dcc.Dropdown(
                                            options=[
                                                {
                                                    "label": "Summary Chart",
                                                    "value": "linechart",
                                                },
                                                {
                                                    "label": "Control Chart",
                                                    "value": "controlchart",
                                                },
#                                                 {
#                                                     "label": "Statespace Chart",
#                                                     "value": "statespace",
#                                                 },
                                            ],
                                            value="linechart",
                                            id="chart-swapper",
                                        ),
                                    ],
                                ),
                                html.P(id="aggregation-title", children="Select summary statistic to plot:"),
                                dcc.Dropdown(
                                    options=[
                                        {
                                            "label": "Mean Value",
                                            "value": "mean",
                                        },
                                        {
                                            "label": "Median Value",
                                            "value": "median",
                                        },
                                        {
                                            "label": "Min. Value",
                                            "value": "min",
                                        },
                                        {
                                            "label": "Max. Value ",
                                            "value": "max",
                                        },
                                    ],
                                    value="mean",
                                    id="aggregation-dropdown",
                                ),
                            ]
                        ),

                        # Panel for charts
                        html.Div(
                            id="graph-container", className="panel",
                            children=[
                                html.Div(
                                    id="line-chart-container",
                                    children=[
                                        html.P(
                                            "Summary Chart",
                                            id="line-title", className="panel-title"
                                        ),
                                        dcc.Graph(
                                            id="line-chart", className="chart-content",
                                            figure=dict(
                                                data=[dict(x=0, y=0)],
                                                layout=dict(
                                                    paper_bgcolor="#F4F4F8",
                                                    plot_bgcolor="#F4F4F8",
                                                    autofill=True,
                                                    margin={"r": 0, "t": 0, "l": 20, "b": 0},
                                                ),
                                            ),
                                        ),
                                    ],
                                    style={'display': 'block'}
                                ),
                                html.Div(
                                    id="control-chart-container",
                                    children=[
                                        html.P(
                                            "Control Chart",
                                            id="control-title", className="panel-title"
                                        ),
                                        html.P(
                                            id="controls-text",
                                            children="Control options are below charts."
                                        ),
                                        dcc.Graph(
                                            id="control-chart", className="chart-content",
                                            figure=dict(
                                                data=[dict(x=0, y=0)],
                                                layout=dict(
                                                    paper_bgcolor="#F4F4F8",
                                                    plot_bgcolor="#F4F4F8",
                                                    autofill=True,
                                                    margin={"r": 0, "t": 0, "l": 20, "b": 0},
                                                ),

                                            ),
                                        ),
                                    ],
                                    style={'display': 'none'}
                                ),
                                html.Div(
                                    id="statespace-chart-container",
                                    children=[
                                        html.P(
                                            "Statespace Chart",
                                            id="statespace-title", className="panel-title"
                                        ),
                                        dcc.Graph(
                                            id="statespace-chart", className="chart-content",
                                            figure=dict(
                                                data=[dict(x=0, y=0)],
                                                layout=dict(
                                                    paper_bgcolor="#F4F4F8",
                                                    plot_bgcolor="#F4F4F8",
                                                    autofill=True,
                                                    margin={"r": 0, "t": 0, "l": 20, "b": 0},
                                                ),
                                            ),
                                        ),
                                    ],
                                    style={'display': 'none'}
                                ),
                            ],
                        ),

                        # Panel for chart controls
                        html.Div(
                            id="control-container", className="panel",
                            children=[
                                html.H4(children="Chart Display Options: "),
                                html.Div(className="slider-box", children=[
                                    html.P(className="control_title",
                                           children="Display outlying values by deviation amount:"),
                                    dcc.Slider(
                                        id='deviation-slider',
                                        value=1,
                                        min=1,
                                        max=3,
                                        step=1,
                                        marks={
                                            0: {'label': '0'},
                                            1: {'label': '1'},
                                            2: {'label': '2'},
                                            3: {'label': '3'}
                                        },
                                        tooltip={'placement': 'bottom', 'always_visible': True}
                                    ),
                                ]),
                                html.Div(className="slider-box", children=[
                                    html.P(className="control-title",
                                           children="Minimum amount of years for a trend to occur:"),
                                    dcc.Slider(
                                        id='trend-slider',
                                        value=10,
                                        min=2,
                                        max=20,
                                        step=1,
                                        marks={
                                            2: {'label': '2'},
                                            10: {'label': '10'},
                                            20: {'label': '20'}
                                        },
                                        tooltip={'placement': 'bottom', 'always_visible': True}
                                    ),
                                ]),
                                html.Div(className="control-box", children=[
                                    html.P(className="control-title", children="Select which markers to display:"),
                                    dcc.Checklist(
                                        id='flag-checklist',
                                        options=data_style_options[1:],
                                        value=list(data_styles.keys())[1:],
                                        labelStyle={'display': 'block'}
                                    ),
                                ]),
                                html.Div(children=[
                                    html.P(className="control-title", children="Display non-significant trend lines:"),
                                    dcc.Checklist(
                                        id='all-trend-checklist',
                                        options=[{'label': 'True',
                                                  'value': 'true'}],
                                        value=[],
                                        labelStyle={'display': 'inline'}
                                    ),
                                ]),
                            ],
                        )
                    ],
                ),
                ########################################################################################################
            ],
        ),
    ],
)
########################################################################################################################

'''
Below are the Callbacks for updating elements when the user interacts with the dashboard.

update_year_slider_visibility - Updates the visibility of the year slider based on the spatial data type of the 
                                dataset. Datasets with county level data need a manual slider, while 
                                latitude/longitude centric datasets have an animated slider built in. 
                                
                  display_map - Updates the choropleth chart with the selected data.
                                
        display_selected_data - Updates the plot charts using the data selected on the choropleth chart.
                                
                 change_panel - Updates the panel containing the plots to display the currently selected plot.
                                
         update_data_selector - Updates the variable selector dropdown with the relevant variables present in the
                                chosen dataset.
'''


# Callbacks
########################################################################################################################
# Update Year Slider visibility, county based datasets need a manual slider.


@app.callback(
    Output(component_id='year-container', component_property='style'),
    [
        Input(component_id='dataframe-dropdown', component_property='value')
    ]
)


def update_year_slider_visibility(visibility_state):

    if data_json_dict[visibility_state]['dataset_label'] != 'Annual Weather Data':
        return {'display': 'none'}



# Callback for Choropleth figure
@app.callback(
    Output("county-choropleth", "figure"),
    [
        State("county-choropleth", "figure"),
        Input("data-dropdown", "value"),
        Input("dataframe-dropdown", "value"),
        Input("year-slider", "value"),
        Input("address", "value")
    ],
)

#@cache.memoize(timeout=timeout)  # in seconds
#@cache.cached(timeout=timeout, key_prefix="XYZ-no-suitable_constant")
def display_map(figure, data_dropdown, dataframe_dropdown, year_slider, address):

    #print("dataframe_dropdown: " + str(dataframe_dropdown))
    map_dat = cache.get("map_dat" + str(dataframe_dropdown))
    if map_dat is None:
        map_dat = select_dataframe(dataframe_dropdown)
        cache.set("map_dat" + str(dataframe_dropdown), map_at)
    #    print("map_dat cache miss")
    #else:
    #    print("map_dat cache hit")

    #print("map_dat: " + str(map_dat))

    fig = cache.get("fig_" + str(dataframe_dropdown))
    if fig is None:
        fig = plot_choropleth(
            map_dat, dataframe_dropdown, data_dropdown, data_json_dict, year_slider, counties, address, zips_df
        )
        cache.set("fig_" + str(dataframe_dropdown), fig)
    #    print("fig cache miss")
    #else:
    #    print("fig cache hit")

    return fig


# Update Line Chart
@app.callback(
    Output("line-chart", "figure"),
    [
        Input("county-choropleth", "selectedData"),
        Input("aggregation-dropdown", "value"),
        Input("data-dropdown", "value"),
        Input("dataframe-dropdown", "value"),
        State("data-dropdown", "options"),
        State("line-chart-container", "style"),
    ],
)
def display_line_chart(selected_data, chart_dropdown, data_dropdown, dataframe_dropdown, opts, line_chart_style):
    if line_chart_style['display'] != 'none':

        if selected_data is None:
            fig = default_chart()
            return fig

        chart_dat = select_dataframe(dataframe_dropdown)
        y_val = data_dropdown
        lat_val = data_json_dict[dataframe_dropdown]['space_keys'][0]
        lon_val = data_json_dict[dataframe_dropdown]['space_keys'][1]
        time_val = data_json_dict[dataframe_dropdown]['temporal_key']

        # find points from the selected data
        pts = selected_data["points"]

        the_label = [x['label'] for x in opts if x['value'] == data_dropdown]
        the_label = str(the_label).replace('[', '').replace(']', '')

        if data_json_dict[dataframe_dropdown]["space_type"] == 'latlong':

            # get a list of all locations selected
            lat_vals = [d["lat"] for d in pts if "lat" in d]
            lon_vals = [d["lon"] for d in pts if "lon" in d]
            vals = list(zip(lat_vals, lon_vals))

            # find the values for all selected counties for all years
            df = chart_dat.set_index([lat_val, lon_val], drop=False)
            sub_df = df.loc[df.index.isin(vals)]

        else:
            fips_val = data_json_dict[dataframe_dropdown]['space_keys'][2]

            # get a list of all locations selected
            vals = [d['location'] for d in pts if 'location' in d]

            # find the values for all selected counties for all years
            df = chart_dat.set_index([fips_val])
            sub_df = df.loc[df.index.isin(vals)]

        if sub_df.empty:
            fig = default_chart()
            return fig

        # make fips code and index
        if "fips" == sub_df.index.name:
            sub_df = sub_df.reset_index()

        # select the data to plot
        summ_df = aggregate_dataframe(sub_df, time_val, lat_val, lon_val, y_val, chart_dropdown)

        # calculate time length
        ky = data_json_dict[dataframe_dropdown]['temporal_key']
        time = summ_df.nunique()[ky]

        if time > 2:
            fig_out = plot_line(summ_df, time_val, y_val, the_label)
        if time == 1:
            fig_out = plot_hist(sub_df, y_val, the_label, chart_dropdown)
        if time == 2:
            fig_out = plot_bar(summ_df, y_val, time_val, the_label, chart_dropdown)

        return fig_out

    else:
        fig = default_chart()
        return fig


# Update Control Chart
@app.callback(
    Output('control-chart', 'figure'),
    [
        Input("county-choropleth", "selectedData"),
        Input("aggregation-dropdown", "value"),
        Input("data-dropdown", "value"),
        Input("dataframe-dropdown", "value"),
        Input("trend-slider", "value"),
        Input("deviation-slider", "value"),
        Input("flag-checklist", "value"),
        Input("all-trend-checklist", "value"),
        State("data-dropdown", "options"),
        State("control-chart-container", "style"),
    ],

)
def display_control_chart(selected_data, chart_dropdown, data_dropdown, dataframe_dropdown, trend, deviation,
                          flag_checklist, all_trends, opts, control_chart_style):
    if control_chart_style['display'] != 'none':
        if selected_data is None:
            fig = default_chart()
            return fig

        chart_dat = select_dataframe(dataframe_dropdown)
        y_val = data_dropdown
        lat_val = data_json_dict[dataframe_dropdown]['space_keys'][0]
        lon_val = data_json_dict[dataframe_dropdown]['space_keys'][1]
        time_val = data_json_dict[dataframe_dropdown]['temporal_key']

        # find points from the selected data
        pts = selected_data["points"]

        the_label = [x['label'] for x in opts if x['value'] == data_dropdown]
        the_label = str(the_label).replace('[', '').replace(']', '')

        if data_json_dict[dataframe_dropdown]["space_type"] == 'latlong':

            # get a list of all locations selected
            lat_vals = [d["lat"] for d in pts if "lat" in d]
            lon_vals = [d["lon"] for d in pts if "lon" in d]
            vals = list(zip(lat_vals, lon_vals))

            # find the values for all selected counties for all years
            df = chart_dat.set_index([lat_val, lon_val], drop=False)
            sub_df = df.loc[df.index.isin(vals)]

        else:
            fips_val = data_json_dict[dataframe_dropdown]['space_keys'][2]

            # get a list of all locations selected
            vals = [d['location'] for d in pts if 'location' in d]

            # find the values for all selected counties for all years
            df = chart_dat.set_index([fips_val])
            sub_df = df.loc[df.index.isin(vals)]

        if sub_df.empty:
            fig = default_chart()
            return fig

        # select the data to plot
        summ_df = aggregate_dataframe(sub_df, time_val, lat_val, lon_val, y_val, chart_dropdown)

        # update enabled flags based on checklist state
        flag_dict = data_styles
        for fkey in flag_dict:
            if fkey not in flag_checklist:
                flag_dict[fkey][1] = 0
            else:
                flag_dict[fkey][1] = 1

        con_df, segments = control_sort(summ_df, y_val, trend, deviation, flag_dict)

        # Control Chart Fig
        control_fig = plot_control(con_df, segments, y_val, time_val, the_label, all_trends, flag_dict)

        return control_fig

    else:
        fig = default_chart()
        return fig


# Update Statespace Chart
@app.callback(
    Output('statespace-chart', 'figure'),
    [
        Input("county-choropleth", "selectedData"),
        Input("aggregation-dropdown", "value"),
        Input("data-dropdown", "value"),
        Input("dataframe-dropdown", "value"),
        State("data-dropdown", "options"),
        State("statespace-chart-container", "style")
    ],
)
def display_statespace_chart(selected_data, chart_dropdown, data_dropdown, dataframe_dropdown,
                             opts, statespace_chart_style):
    if statespace_chart_style['display'] != 'none':
        if selected_data is None:
            fig = default_chart()
            return fig

        chart_dat = select_dataframe(dataframe_dropdown)
        y_val = data_dropdown
        lat_val = data_json_dict[dataframe_dropdown]['space_keys'][0]
        lon_val = data_json_dict[dataframe_dropdown]['space_keys'][1]
        time_val = data_json_dict[dataframe_dropdown]['temporal_key']

        # find points from the selected data
        pts = selected_data["points"]

        the_label = [x['label'] for x in opts if x['value'] == data_dropdown]
        the_label = str(the_label).replace('[', '').replace(']', '')

        if data_json_dict[dataframe_dropdown]["space_type"] == 'latlong':

            # get a list of all locations selected
            lat_vals = [d["lat"] for d in pts if "lat" in d]
            lon_vals = [d["lon"] for d in pts if "lon" in d]
            vals = list(zip(lat_vals, lon_vals))

            # find the values for all selected counties for all years
            df = chart_dat.set_index([lat_val, lon_val], drop=False)
            sub_df = df.loc[df.index.isin(vals)]

        else:
            fips_val = data_json_dict[dataframe_dropdown]['space_keys'][2]

            # get a list of all locations selected
            vals = [d['location'] for d in pts if 'location' in d]

            # find the values for all selected counties for all years
            df = chart_dat.set_index([fips_val])
            sub_df = df.loc[df.index.isin(vals)]

        if sub_df.empty:
            fig = default_chart()
            return fig

        # chart isn't designed to work with average values, so ensure a different aggregation function is selected.
        if chart_dropdown != "mean":
            statespace_df = sub_df[[time_val, y_val, lat_val, lon_val]]

            statespace_chart_df = aggregate_dataframe(statespace_df, time_val, lat_val, lon_val, y_val, chart_dropdown)

            # State-space chart
            statespace_fig = plot_statespace(statespace_chart_df, time_val, lat_val, lon_val, the_label)
        else:
            statespace_fig = default_chart("Please select a summary statistic.")

        return statespace_fig

    else:
        fig = default_chart()
        return fig


# Update display for graph panel
@app.callback([
    Output("line-chart-container", "style"),
    Output("control-chart-container", "style"),
    Output("statespace-chart-container", "style"),
    Output("control-container", "style"),
    Output("aggregation-dropdown", "options"),
    Output("aggregation-dropdown", "value")
],
    [
        Input("chart-swapper", "value"),
        Input("aggregation-dropdown", "value")
    ],
    prevent_initial_call=True
)
def change_panel(chart_swapper, aggregation_dropdown):
    agg_opts = [
        {
            "label": "Mean Value",
            "value": "mean",
        },
        {
            "label": "Median Value",
            "value": "median",
        },
        {
            "label": "Min. Value",
            "value": "min",
        },
        {
            "label": "Max. Value ",
            "value": "max",
        },
    ]

    agg_val = aggregation_dropdown

    # Return Values:
    ##################################
    # Line Chart Visibility
    # Control Chart Visibility
    # State-Space Chart Visibility
    # Control Container Visibility
    # Aggregation Dropdown Options
    # Aggregation Dropdown Value
    ##################################
    if chart_swapper == "linechart":
        return {'display': 'block'}, \
               {'display': 'none'}, \
               {'display': 'none'}, \
               {'display': 'none'}, \
               agg_opts, \
               agg_val
    elif chart_swapper == "controlchart":
        return {'display': 'none'}, \
               {'display': 'block'}, \
               {'display': 'none'}, \
               {'display': 'flex'}, \
               agg_opts, \
               agg_val
    elif chart_swapper == "statespace":
        agg_opts.pop(0)  # remove mean from the possible choices.
        return {'display': 'none'}, \
               {'display': 'none'}, \
               {'display': 'block'}, \
               {'display': 'none'}, \
               agg_opts, \
               agg_val


# Update Data Selection Dropdown
@app.callback([
    Output("data-dropdown", "options"),
    Output("data-dropdown", "value"),
],
    [
        Input("dataframe-dropdown", "value")
    ]
)
def update_data_selector(dataframe_dropdown):
    data_opts = data_json_dict[dataframe_dropdown]['fields']
    data_value = data_json_dict[dataframe_dropdown]['fields'][0]["value"]

    return data_opts, data_value


########################################################################################################################


# Additional Helper Functions
########################################################################################################################

# Function for selecting which dataframe to load when we need to load a dataframe into a callback.
#   - A line needs to be added here when adding a new dataframe to the dashboard.
def select_dataframe(dataframe_label):
    if dataframe_label == 'output.csv':
        return df_annual_climate
    elif dataframe_label == 'kestralModel.csv':
        return df_kestral_model
    elif dataframe_label == 'Carya_ovata.csv':
        return df_carya_ovata
    elif dataframe_label == 'carya_ovata_10km.csv':
        return df_carya_ovata_spacetime
    elif dataframe_label == 'precip_past.csv':
        return df_precipitation
    elif dataframe_label == 'crop_climate_trends.csv':
        return df_crop_climate_trends_spacetime
    elif dataframe_label == 'crop_switching.csv':
        return df_crop_switching
    elif dataframe_label == 'pestAtlas.csv':
        return df_pest
    elif dataframe_label == 'crop_model.csv':
        return df_cm
    else:
        return pd.Dataframe()


########################################################################################################################


# run the server
########################################################################################################################
if __name__ == "__main__":
    app.run_server(debug=True)
