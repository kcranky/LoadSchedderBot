#!/usr/bin/python3

import db_helpers
import loadshedding_helpers

from datetime import date, datetime


def get_stage_dict(area_region):
    """
    Returns a 24 hour dict containing the expected load shedding stage for each hour
    """
    status = loadshedding_helpers.get_status()

    # TODO this isn't exact, it might be a good idea to reach out to se push and determine if there is a better way of doing this.
    # It'd be nice if they had something more direct in the requests to tie area region and area together, for example a prefix on the area id
    if "CAPE TOWN" in area_region.upper():
        area_status = status["capetown"]
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


def get_hours_out(area):
    # TODO make date a parameter?
    current_date = str(datetime.now().date())  # format is YYYY-MM-DD
    current_hour = int(datetime.now().hour)

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
    for i in range(current_hour, 24):
        can_join_dict[i] = True if (upcoming_stages[i] < stage_hours[i]) or (stage_hours[i] == 0) else False
    return can_join_dict


def stringify_can_join(availability_dict):
    """
    Takes in a dict of keys ending in 23.
    The dict can start at any point
    """
    in_available_slot = False
    availability_list = []
    for k in availability_dict:
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
    current_hour = int(datetime.now().hour)
    all_avail = {i: True for i in range(current_hour, 24)}
    for schedule in schedule_array:
        for hour in schedule:
            all_avail[hour] = schedule[hour] if schedule[hour] == False else all_avail[hour]
    return all_avail


def schedule_group(group):
    area_list = db_helpers.get_group_area_names(group)
    res = [get_hours_out(area) for area in area_list]
    return combine_schedules(res)


if __name__ == "__main__":
    print(stringify_can_join(schedule_group("mw2")))