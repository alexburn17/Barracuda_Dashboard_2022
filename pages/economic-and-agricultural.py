import dash
from Page_Template import app_layout

category = 'economic-and-agricultural'
page_path='/'+category
dash.register_page(__name__, path=page_path)
layout = app_layout(category)
