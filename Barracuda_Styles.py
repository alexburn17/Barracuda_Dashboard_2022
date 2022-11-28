# CSS related styles
STYLES = {
    "chart_background": "#E6E4E6",
    "chart_grid": "#B3B1B3",
    "tick_font": "#111111",
    "font": "#111111",
    "line_colors": [
        "#21A0A6"
    ],
    "marker_colors": [
        "#FAEA48",
        "#c47e0e",
        "#4951de",
        "#bd51c9",
        "#4cbf39",
        "#c95034",
    ],
    "margins": {
        "r": 10, #10
        "l": 20,  #20
        "t": 50, #50
        "b": 10 #10
    }
}

# Flags and color associations
data_styles = {
    "base": [STYLES["line_colors"][0], 1],
    "above average": [STYLES["marker_colors"][0], 1],
    "below average": [STYLES["marker_colors"][1], 1],
    "deviation above": [STYLES["marker_colors"][2], 1],
    "deviation below": [STYLES["marker_colors"][3], 1],
    "trending up": [STYLES["marker_colors"][4], 1],
    "trending down": [STYLES["marker_colors"][5], 1]
}
