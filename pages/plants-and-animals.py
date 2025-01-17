import dash
from Page_Template import app_layout

#from dash import html
#from Dash_page_blueprint import data_dict_all_cats

category = 'plants-and-animals'
page_path='/'+category
dash.register_page(__name__, path=page_path)
layout = app_layout(category)
