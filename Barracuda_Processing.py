import pandas as pd
import numpy as np


#######################################################################################################################
# Add masking columns to the dataset to allow the control chart to select the relevant rows for traces.
def control_sort(dataframe, y_col, trend_size, deviation, flags):
    avg = np.average(dataframe[y_col])
    std = np.std(dataframe[y_col])
    std_co = deviation
    segments = []

    for key in flags:
        if flags[key][1] == 1:
            if key == 'above average':
                dataframe[key+' mask'] = np.where(dataframe[y_col].values >= avg, 1, 0)

            if key == 'below average':
                dataframe[key + ' mask'] = np.where(dataframe[y_col].values < avg, 1, 0)

            if key == 'deviation above':
                dataframe[key + ' mask'] = np.where(dataframe[y_col].values >= avg + (std*std_co), 1, 0)

            if key == 'deviation below':
                dataframe[key + ' mask'] = np.where(dataframe[y_col].values < avg - (std * std_co), 1, 0)

            if key == 'trending up' or key == 'trending down':
                segments = trend_by_slope(dataframe, y_col, trend_size)

    return dataframe, segments


# Trend detection, runs cumulative linear slope calculations over the dataset, marking segments that constitute trends
def trend_by_slope(dataframe, y_col, t_size):
    min_change = t_size
    curr_changes = 0
    last_sign = 1
    last_change_idx = 0
    bounds_idx = [0]
    cumulative_slope = [0]

    dataframe['row'] = np.arange(len(dataframe))

    for i in range(1, dataframe.shape[0]):
        segment = dataframe.iloc[0:i+1, :]

        slope = calc_slope(segment, y_col)
        cumulative_slope.append(slope)

        # compare the current cumulative slope with the previous, and keep track of whether it increased or decreased
        # as well as how many times it has changed in that direction, and where it last changed direction
        if abs(cumulative_slope[i]) < abs(cumulative_slope[i-1]):
            if last_sign == 1:
                curr_changes = 0
            if curr_changes == 0:
                last_change_idx = i
            curr_changes += 1
            last_sign = -1

        elif abs(cumulative_slope[i]) > abs(cumulative_slope[i-1]):
            if last_sign == -1:
                curr_changes = 0
            if curr_changes == 0:
                last_change_idx = i
            curr_changes += 1
            last_sign = 1

        # if we meet the minimum amount of times the slope changes in a direction, mark the last time it changed
        # and reset the change counter
        if curr_changes == min_change:
            curr_changes = 0
            bounds_idx.append(last_change_idx)

    # add the last point in the dataset to the bounds just to ensure we encapsulate all points
    bounds_idx.append(dataframe.shape[0]-1)

    return bounds_idx


# Aggregators for the dataset
def aggregate_dataframe(df, time_val, lat_val, lon_val, y_val, agg_type):
    if agg_type == "mean":
        summ_df = df[[time_val, lat_val, lon_val, y_val]].groupby(time_val).mean().reset_index()

    # if the dataset is of even length, round down to the next closest median.
    if agg_type == "median":
        if len(df.index) % 2 == 0:
            sorted_df = df.sort_values(by=[y_val], ascending=True)
            summ_df = sorted_df.groupby(time_val).apply(
                lambda x: x[x[y_val] == x[y_val].iloc[0:(int(len(x) - 1))].median()])
        else:
            summ_df = df.groupby(time_val).apply(
                lambda x: x[x[y_val] == x[y_val].median()])

    if agg_type == "max":
        summ_df = df.groupby(time_val).apply(lambda x: x[x[y_val] == x[y_val].max()])

    if agg_type == "min":
        summ_df = df.groupby(time_val).apply(lambda x: x[x[y_val] == x[y_val].min()])

    return summ_df
#######################################################################################################################


# Helper Functions
#######################################################################################################################
# helper function to calculate slope of a dataframe
def calc_slope(df, y_val):
    slope = np.polyfit(df['row'], df[y_val], 1)
    return slope[0]
