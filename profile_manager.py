"""profile_manager.py

   Manages the profile handling between the json file and the GUI
   
   @file profile_manager.py
   @author Lukas Gerstlauer
   @email lukas.gerstlauer@de.bosch.com
   @date 21.06.24
   @version 1.0
"""

import json
from collections import OrderedDict
import meas_conversion_tool

PROFILE_DATA = {}

def load_profiles() -> list:
    """Loads the profile.json file and stores all profiles

    Returns:
        list: list of orofiles
    """
    global PROFILE_DATA
    with open(meas_conversion_tool.JSON_PATH, 'r') as file:
        PROFILE_DATA = json.load(file, object_pairs_hook=OrderedDict)
        return PROFILE_DATA


def new_profile(name: str, labels: list):
    """Creates a new profile

    Args:
        name (str): name of the profile
        labels (list): labels of the profile
    """
    global PROFILE_DATA
    neues_profile = {
        "name": name,
        "labels": labels
    }
    PROFILE_DATA[name] = neues_profile

    write_json()


def edit_profile(name: str, new_name: str, labels: list, profile_list: list):
    """Updates the profile and saves it in the same place in the list

    Args:
        name (str): old name of the profile
        new_name (str): new name of the profile
        labels (list): labels of the profile
        profile_list (list): list of all profiles
    """
    global PROFILE_DATA

    PROFILE_DATA[name]["name"] = new_name
    PROFILE_DATA[name]["labels"] = labels
    PROFILE_DATA[new_name] = PROFILE_DATA.pop(name)

    start_index = profile_list.index(name)

    for element in profile_list[start_index+1:]:
        PROFILE_DATA.move_to_end(element)

    write_json()


def del_profile(name: str):
    """Deletes a profile

    Args:
        name (str): name of the profile
    """
    global PROFILE_DATA
    del PROFILE_DATA[name]

    write_json()


def write_json():
    """Writes all profiles to the .json file and update the profile variable of the MeasurementGUI object
    """
    global PROFILE_DATA
    meas_conversion_tool.MeasurementGUI.profiles_json = PROFILE_DATA
    meas_conversion_tool.MeasurementGUI.profile_names = meas_conversion_tool.MeasurementGUI.extract_profile_names(
        meas_conversion_tool.MeasurementGUI, meas_conversion_tool.MeasurementGUI.profiles_json)

    with open(meas_conversion_tool.JSON_PATH, 'w') as file:
        json.dump(PROFILE_DATA, file, indent=4)


def str_2_list(input_str: str) -> list:
    """Converts a string, separated with \n into a list

    Args:
        input (str): input string

    Returns:
        list: output list
    """
    mylist = input_str.replace('\t', '').split("\n")
    while "" in mylist:
        mylist.remove("")
    mylist = [s.strip() for s in mylist]
    return mylist


def list_2_str(mylist: list) -> str:
    """Converts a list into a string in which the elements are separated by a comma.

    Args:
        mylist (list): input list

    Returns:
        str: output string
    """
    result_string = ",".join(mylist)
    return result_string


def str_comma_2_newLine(input_str: str) -> str:
    """replaces all "," to \\n in a string

    Args:
        input (str): input string

    Returns:
        str: output string
    """
    return input_str.replace(" ", "").replace(",", "\n")



