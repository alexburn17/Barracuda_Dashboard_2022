import dash
from dash import html

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
#import dash
from dash import dcc
#from dash import html
import dash_loading_spinners as dls
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import time
import os
from flask_caching import Cache
from Barracuda_Processing import control_sort, aggregate_dataframe
from Barracuda_Plotting import default_chart, plot_line, plot_control, plot_choropleth, plot_statespace, plot_hist, plot_bar
from Barracuda_Styles import data_styles

from Dash_page_blueprint import data_style_options, mapbox_access_token, mapbox_style
from Dash_page_blueprint import data_dict_all_cats


# App layout
# This layout is used by all pages
########################################################################################################################
def app_layout(category):

    #page_path = "/" + category
    data_json_dict = data_dict_all_cats[category]

    # Create dropdown list for datasets in this category
    dataset_options = []
    for key in data_json_dict.keys():
        dataset_options.append(
            {'label': data_json_dict[key]['dataset_label'],
             'value': key}
        )

    #
    # Apply the header info for this page and instantiate with the dataset_options above
    subheader = html.Div(id="sub-header",   #className="container",
                     children=[
                        html.H3(children=" Category: " + category, id="category-meta" ),
                        html.Div(children=" Barracuda completed research to understand how humans, plants, and animals may adapt to their changing climate.  This research began in 2020 and runs through fall of 2025.  Some products are still being released and updated.", id="category-meta" ),
                        html.P(children=" These products are collected in the categories seen in the navigation above.", id="category-meta-sub" ),
                        html.P(children="  To see all products over the period of the grant visit:"),
                        html.A("https://biobarracuda.org/all-products-final/",href="https://biobarracuda.org/all-products-final/"),
                        html.P(children="  To learn more about the work and the researchers behind it visit the Barracuda website:"),
                        html.A("biobarracuda.org/about-us",href="https://biobarracuda.org/about-us/"),
                         ],
             )

    #header = "HEADER GOES HERE"
    layout = html.Div(
        id="root",
        children=[
        # Display navigation header with current page in bold
        #header,
        subheader,

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
                                    #value='output.csv',
                                    value='',
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
    ])
    return(layout)
