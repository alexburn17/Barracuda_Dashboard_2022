# Data_Json_Generator.py is meant to generate a JSON file to ensure all datasets are usable within the Barracuda Dashboard.

import json
import csv
import netCDF4 as nc
import os

JSON_FILE = "dataset-names.json"
KNOWN_KEYS_FILE = "known-keys.json"
DATA_DIRECTORY = "data/"


def main():
    print("Barracuda Dataset Identifier JSON Generation Process")
    print("----------------------------------------------------")

    print("Detecting JSON")
    # Detect if JSON exists
    found_json = find_file(JSON_FILE, DATA_DIRECTORY)
    data = {}

    # If JSON doesn't exist, create JSON.
    if not found_json:
        print("JSON not found, creating JSON.")
        json_file = open(DATA_DIRECTORY + JSON_FILE, 'x')
        json_file.close()
        print("JSON created at " + DATA_DIRECTORY + JSON_FILE + ".")
    # Else move on
    else:
        print("JSON found.")

    # Detect if Known Keys file exists
    found_known_keys_file = find_file(KNOWN_KEYS_FILE, DATA_DIRECTORY)
    # If Known Keys file doesn't exist then make it.
    if not found_known_keys_file:
        print("No Known Keys file found, Creating known keys file.")
        known_keys_file = open(DATA_DIRECTORY + KNOWN_KEYS_FILE, 'x')
        known_keys_file.close()
        print("Known Key file created at " + DATA_DIRECTORY + KNOWN_KEYS_FILE + ".")
    else:
        print("Known Keys file found.")

    # Load known keys
    try:
        with open(DATA_DIRECTORY + KNOWN_KEYS_FILE) as known_keys_file:
            known_keys = json.load(known_keys_file)
    except json.JSONDecodeError as error:
        print("Known Keys empty or invalid structure.")
        known_keys = {"temporal": [], "spatial": []}

    # Load JSON
    try:
        with open(DATA_DIRECTORY + JSON_FILE) as json_file:
            data = json.load(json_file)
    except json.JSONDecodeError as error:
        print("JSON empty or invalid structure.")
        data = {}
    print("JSON ready.")

    data = fill_json(data, known_keys)

    #       After each dataset is input, finalize and save JSON.
    with open(DATA_DIRECTORY + JSON_FILE, 'w') as json_file:
        json.dump(data, json_file)
    print("JSON Updated.")


########################################################################################################################


# Helper Functions
########################################################################################################################


# Helper Function to Loop through adding datasets to the JSON.
############
def fill_json(json_data, known_keys):
    print("Adding new Dataset to JSON")
    # Ask user which dataset(s) they want to load into JSON.
    print("Please enter the full file names of the datasets you would like to load (as a comma separated list),")
    print("! Note, filenames cannot have spaces.")
    datasets_list = clean_list_input()
    print(datasets_list)
    #   For each dataset, check if dataset exists in JSON.
    for dataset in datasets_list:
        #       If dataset exists in JSON, ask user if they want to overwrite JSON.
        if dataset in json_data:
            print(dataset + " already exists in the JSON, do you want to overwrite? y/n")
            print("! Note, if yes, you must reenter all values for the dataset fields for it to be valid.")
            overwrite = validate_boolean_input('y', 'n')
            #           If yes, remove dataset from JSON and move to next step.
            if overwrite == 'y':
                print("Overwriting " + dataset)
                del json_data[dataset]
                json_data[dataset] = {}
            #           Else if no, skip dataset.
            else:
                print("Skipping " + dataset)
                datasets_list.remove(dataset)
                continue

        #       Print found fields
        found_fields = []

        splits = dataset.split('.')

        if splits[len(splits)-1] == 'csv':
            try:
                with open(DATA_DIRECTORY + dataset) as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=",")
                    for row in csv_reader:
                        found_fields = row
                        break
                print(found_fields)
            except FileNotFoundError as error:
                print("Couldn't find " + dataset)
                continue
            print("!!! Warning: When requested, field names must be entered exactly as they are in the dataset,"
                  " or they will not work.")

        # Initialize required JSON entries for data.
        json_data[dataset] = {}
        json_data[dataset]['dataset_label'] = ""
        json_data[dataset]['temporal_key'] = ""
        json_data[dataset]['space_type'] = ""
        json_data[dataset]['space_keys'] = []
        json_data[dataset]['fields'] = []

        # Label new Dataset
        print("Please enter the label for '" + dataset + "'.")
        dataset_label = input(">")
        json_data[dataset]['dataset_label'] = dataset_label

        # Inform user of next steps.
        print(dataset_label + " needs new field descriptors.")

        # detect time key
        temporal_key = ""
        for key in found_fields:
            print("looking at " + key)
            if key in known_keys["temporal"]:
                print("Is " + key + " the temporal data key for " + dataset + "? y/n")
                temporal_choice = validate_boolean_input('y', 'n')
                if temporal_choice == 'y':
                    temporal_key = key
                    break
                else:
                    continue
        # If the previous loop doesn't find anything, then we're just gonna have to do it manually.
        if temporal_key == "":
            # Time key manual input
            print("Time key unknown, please enter the field name of the time key:")
            temporal_key = input(">")
            json_data[dataset]['temporal_key'] = temporal_key
            known_keys["temporal"].append(temporal_key)
        json_data[dataset]['temporal_key'] = temporal_key

        # Ask user what type of spatial data is used (county or lat/long)
        print("Does " + dataset + " have county level data or lat and long data? county/latlong")
        spatial_data_type = validate_boolean_input('county', 'latlong')
        json_data[dataset]['space_type'] = spatial_data_type

        # Detect space keys
        spatial_keys = []
        for key in known_keys["spatial"]:
            if key in found_fields:
                print("Is " + key + " a spatial data key for " + dataset + "? y/n")
                spatial_choice = validate_boolean_input('y', 'n')
                if spatial_choice == 'y':
                    spatial_keys.append(key)
                else:
                    continue
        # Once again if we found nothing, we have to get it manually.
        if len(spatial_keys) < 2:
            # Spatial keys manual input
            print("Spatial Keys incomplete or unknown, keys must be entered manually.")
            spatial_keys = []
            print("Please input the field name of the Latitude key:")
            lat_key = input(">")
            spatial_keys.append(lat_key)
            print("Please input the field name of the Longitude key:")
            long_key = input(">")
            spatial_keys.append(long_key)
            if spatial_data_type == 'county':
                print("Please input the field name of the county key:")
                location_key = input(">")
                spatial_keys.append(location_key)
            known_keys["spatial"].append(spatial_keys)
        json_data[dataset]['space_keys'] = spatial_keys

        # Ask for any other id fields.
        id_keys = []
        print("Does your dataset have any other non-spatial or temporal index or ID fields?")
        id_choice = validate_boolean_input('y', 'n')
        if id_choice == 'y':
            json_data[dataset]['id_keys'] = []
            print("Please input any extra id fields as a comma separated list:")
            print("Unused fields: ")
            id_keys = clean_list_input()
            json_data[dataset]['id_keys'] = id_keys

        # Detect data fields
        used_keys = spatial_keys + id_keys
        used_keys.append(temporal_key)
        data_keys = []
        for key in (set(found_fields) - set(used_keys)):
            print("Use " + key + " as a data field? y/n")
            data_choice = validate_boolean_input('y', 'n')
            if data_choice == 'y':
                print("Please enter the un-abbreviated name of " + key + " as you want it to appear on the dashboard:")
                field_description = input(">")
                # Without a field description, default to just calling the field by its name.
                if field_description == "":
                    field_description = key
                data_keys.append({'label': field_description, 'value': key})
        json_data[dataset]['fields'] = data_keys

    with open(DATA_DIRECTORY + KNOWN_KEYS_FILE, 'w') as known_file:
        json.dump(known_keys, known_file)

    #               Add field to JSON as:
    #               "dataset": { "fields": [
    #                               { "value": "field_name",
    #                               "label": "user input description"},
    #                               ...
    #                               ]
    #                          }
    #               Example:
    #               "annual_climateDS": {"fields": [
    #                                       { "value": "tmean",
    #                                       "label": "Average nighttime temperature"},
    #                                       ...
    #                                       ]
    #                                   }

    return json_data


# Walk through a directory and find a particular file
def find_file(file, path):
    result = []
    for root, dirs, files in os.walk(path):
        if file in files:
            result.append(os.path.join(root, file))
    return result


# Clean up list inputs
def clean_list_input():
    user_input_list = input(">")
    user_input_list = user_input_list.replace(" ", "")
    user_input_list = user_input_list.split(",")

    return user_input_list


# Useful Function for when we want to give the user specific choices.
def validate_boolean_input(truthy_choice, falsy_choice):
    overwrite = False
    while not overwrite:
        overwrite_choice = input(">")
        #           If yes, return true.
        if overwrite_choice.lower() == truthy_choice.lower():
            overwrite = True
            return truthy_choice.lower()
        #           Else if no, return false.
        elif overwrite_choice.lower() == falsy_choice.lower():
            overwrite = False
            return falsy_choice.lower()
        #           Otherwise if invalid answer, try again.
        else:
            print("Invalid input, only accepts '" + truthy_choice + "' or '" + falsy_choice + "'.")
            overwrite = False


########################################################################################################################


if __name__ == "__main__":
    main()
