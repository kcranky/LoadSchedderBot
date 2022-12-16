#!/usr/bin/python3

import db_helpers
import loadshedding_helpers
import os
import matplotlib.pyplot as plt

from datetime import datetime
import time

CHECK = "\U00002713"

def get_stage_dict(area_region):
    """
    Returns a 24 hour dict containing the expected load shedding stage for each hour
    """
    status = loadshedding_helpers.get_status()

    # TODO this isn't exact, it might be a good idea to reach out to se push and determine if there is a better way of doing this.
    # For example, CT region 14, Table View, is city supplied according to the CoCT website, but does not have "Cape town" in the region flag
    # The sepush API lists Western Cape as the region, so this check is invalid. But there is also no means of knowing this is CoCT supplied other
    # than storing that knowledge locally
    # It'd be nice if they had something more direct in the requests to tie area region and area together, for example a prefix on the area id
    if "CAPE TOWN" in area_region.upper():
        # It is possible (though unlikely) that there isn't a CT specific entry
        try:
            area_status = status["capetown"]
        except:
            area_status = status["eskom"]
    else:
        # otherwise, we assume eskom
        area_status = status["eskom"]

    # We just take the current stage, and apply it to all hours
    upcoming_stages = {i: int(area_status["stage"]) for i in range(0, 24)}

    for upcoming_stage in area_status["next_stages"]:
        # then, for each upcoming stage, we update the result accordingly
        # TODO I don't think we can trust that "next_stages" will be in order of time, but we're assuming so until proven otherwise
        if upcoming_stage["stage_start_timestamp"][:10] == str(datetime.now().date()):  # only consider today
            for i in range(int(upcoming_stage["stage_start_timestamp"][11:13]), 24):
                upcoming_stages[i] = int(upcoming_stage["stage"])
    return upcoming_stages


def get_all_stage_dicts():
    res = {}
    res["eskom"] = get_stage_dict("eskom")
    res["capetown"] = get_stage_dict("capetown")
    return res


def get_hours_out(area):
    # TODO make date a parameter?
    current_date = str(datetime.now().date())  # format is YYYY-MM-DD
    area_info = loadshedding_helpers.get_area_schedule(area)
    dates_known = [day["date"] for day in area_info["schedule"]["days"]]

    if current_date not in dates_known:
        # FIXME force an update of the cache and try again
        print("UNIMPLEMENTED day not in schedule")
        return

    # First, we get the particular schedule for the day
    for day in area_info["schedule"]["days"]:
        if day["date"] == current_date:
            schedule = day["stages"]
            break

    # at this point, schedule consists of an array where each element contains the time off for that stage
    # TODO: Note that the array may only contain 4 elements, in which case we may need to mod stage number by 4 when performing lookup
    # We summarise data by representing the lowest stage for load shedding to occur
    stage_hours = {i: 0 for i in range(0, 24)}
    for stage, hours_off_in_stage in enumerate(schedule):
        hours_in_stage = []
        for slot in hours_off_in_stage: # for each loadshedding slot in each stage,
            start = int(slot[:2])
            stop = int(slot[6:8]) if int(slot[6:8]) != 0 else 24 # need to use 24h to represent midnight
            hours_in_stage = hours_in_stage + [i for i in range(start, stop)]
        for i in hours_in_stage:
            # we only want to set a stage if we know we don't have loadshedding at that point
            if stage_hours[i] == 0:
                stage_hours[i] = stage + 1

    # stage_hours - gives the minimum stage required for the power to be off
    # gives the stage number for each
    upcoming_stages = get_stage_dict(area_info["info"]["region"])
    # we can now modify our can_join dict, and return that
    can_join_dict = {}
    for i in range(0, 24):
        can_join_dict[i] = True if (upcoming_stages[i] < stage_hours[i]) or (stage_hours[i] == 0) else False
    return can_join_dict


def stringify_can_join(availability_dict):
    """
    Takes in a can_join dict and stringifies it into a readable format.
    Only shows the dict from the current hour, as hours prior to the current one may be showing the incorrect stage.
    """
    current_hour = int(datetime.now().hour)
    in_available_slot = False
    availability_list = []
    for k in range(current_hour, 24):
        if availability_dict[k] == True and in_available_slot == False:
            in_available_slot = True
            availability_list.append("{0:02d}:00".format(k))
        elif availability_dict[k] == False and in_available_slot == True:
            in_available_slot = False
            availability_list[len(availability_list) -
                              1] += "-{0:02d}:00".format(k)
    if in_available_slot == True:
        # we got to end of day in an open slot, so we just mark it as closed
        in_available_slot = False
        availability_list[len(availability_list) -
                          1] += "-{0:02d}:59".format(k)
    return str(availability_list)


def combine_schedules(schedule_array):
    all_avail = {i: True for i in range(0, 24)}
    for schedule in schedule_array:
        for hour in schedule:
            all_avail[hour] = schedule[hour] if schedule[hour] == False else all_avail[hour]
    return all_avail


def schedule_group(group):
    area_list = db_helpers.get_group_area_names(group)
    res = [get_hours_out(area) for area in area_list]
    return combine_schedules(res)


def generate_graph(group):
    # So what do we want to acheive?
    """
    Generate a human-readable graph to determine non-optimal schedule times
    """
    # start by removing all previous pngs from the graph location
    graph_dir = "images/generated_graphs/"
    for file in os.listdir(graph_dir):
        if file.endswith(".png"):
            os.remove(os.path.join(graph_dir, file))
    plot_name = "{}{}{}.png".format(graph_dir, group, datetime.now())
    if group == "ALL":
        users = db_helpers.get_all_members()
    else:
        users = db_helpers.get_group_members(db_helpers.get_group_id(group))
    # 2: Get the areas for each user
    area_names = [db_helpers.get_name("areas", area) for area in db_helpers.get_users_areas(users)]
    # 3: Get the stages for each area
    data = {area : get_hours_out(area) for area in area_names}

    # data is now held by area. But we want it to be labelled by user
    data_by_user = {}
    for area in data:
        users_in_area = db_helpers.get_area_users_by_group(area, group)
        user_list = [users[0] for users in users_in_area]
        for user in user_list:
            if user in data_by_user:
                data_by_user[user] = combine_schedules([data_by_user[user], data[area]])
            else:
                data_by_user[user] = data[area]

    # now we need to format the data to just be a 2d array, consisting of rowLabels*24 elements
    formatted_data = {}
    rowLabels = [key for key in data_by_user]
    current_hour = int(datetime.now().hour)
    for key in data_by_user:
        formatted_data[key] = [data_by_user[key][k] for k in range(current_hour, 24)]
    # now replace all trues with ticks, etc
    colors = {}
    for key in formatted_data:
        colors[key] = ["chartreuse" if element == True else "salmon" for element in formatted_data[key]]
        formatted_data[key] = [CHECK if element == True else "X" for element in formatted_data[key]]
    plot_data = [formatted_data[key] for key in rowLabels]
    cell_colors = [colors[key] for key in rowLabels]

    # Set up and plot the timetable
    plt.rcParams["font.family"] = "FreeSerif"
    colLabels = ["{}h".format(i) for i in range(current_hour, 24)]
    fig, ax = plt.subplots()
    ax.set_axis_off() 
    table = ax.table( 
        cellText = plot_data,
        rowLabels = rowLabels,
        colLabels = colLabels, 
        cellColours= cell_colors,
        rowColours =["cadetblue"] * (1 + len(data)),
        colColours =["palegreen"] * 24,
    cellLoc ='center',
    loc ='upper left')
    plt.suptitle('Advanced schedule for {} for {}'.format(group, datetime.now().date()), 
             fontweight ="bold")
    ax.set_title("Generated at {}".format(datetime.now().strftime("%H:%M:%S")), fontweight="bold", fontsize=10)
    plt.savefig("{}".format(plot_name), bbox_inches='tight')

    return plot_name

def isTimeFormat(input):
    if input is None:
        return False
    try:
        time.strptime(input, '%H:%M')
        return True
    except ValueError:
        return False

if __name__ == "__main__":
    print(stringify_can_join(schedule_group("mw2")))