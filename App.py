import dash
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

#
# Navigation is generated at startup after all pages are registered from the pages/ directory
navigation = dbc.ListGroup(
                [
                    dbc.ListGroupItem(page["name"], href=page["path"])
                    for page in dash.page_registry.values()
                    if page["module"] != "pages.not_found_404"

                ]
            )

nav_sub_header = html.Div([" Dataset Categories: | ", navigation])
app.layout = html.Div(
    [
       # App Header, common to all pages
        html.Div(
            id="header",
            children=[
                html.A(
                    html.Img(id="logo", src=app.get_asset_url("barracuda_logo_final.png")),
                    href="https://biobarracuda.org/",
                ),
                html.H4(children=" Barracuda Data Visualization Dashboard"),
                html.P(
                    id="description",
                    children="Biodiversity and Rural Response to Climate Change Using Data Analysis",
                ),
                nav_sub_header,
            ],
        ),

        # Navigation generated above
        #dbc.ListGroupItem(" Dataset Categories: | "),
        #html.P(class="sub-header-item", " Dataset Categories: | "),
        #navigation,

        # content of each page
        dash.page_container
    ]
)


if __name__ == '__main__':
    app.run(debug=True)
