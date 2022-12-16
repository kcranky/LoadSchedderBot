#!/usr/bin/python3
"""
Contains helper methods for database use.

TODO: Add some form of scrubbing to nasty sql injection attempts

"""

import sqlite3
from os.path import exists

DB_NAME = "data.sqlite3"


def create_db():
    conn = None
    if not exists(DB_NAME):
        try:
            conn = sqlite3.connect(DB_NAME)
            _create_tables(conn)
        except sqlite3.Error as e:
            return
        finally:
            if conn:
                conn.close()


def _create_tables(conn):
    PRIMARY_TABLES = ["users", "areas", "groups"]
    for table in PRIMARY_TABLES:
        conn.execute("""CREATE TABLE {}(
                    id INTEGER NOT NULL PRIMARY KEY,
                    name TEXT NOT NULL COLLATE NOCASE);""".format(table))
    # create assosciation tables
    conn.execute("""CREATE TABLE user_areas(
                user_id INTEGER,
                area_id INTEGER,
                CONSTRAINT fk_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
                CONSTRAINT fk_areas FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE CASCADE ON UPDATE CASCADE);""")
    conn.execute("""CREATE TABLE user_groups(
                user_id INTEGER,
                group_id INTEGER,
                CONSTRAINT fk_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
                CONSTRAINT fk_groups FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE ON UPDATE CASCADE);""")


def populate_test_data():
    TEST_USERS = ["Matthew", "Mark", "Luke", "John"]
    TEST_GROUPS = ["Dota", "COD-MW", "Diablo"]
    TEST_AREAS = ["capetown-5-claremont", "eskde-10-fourwaysext10cityofjohannesburggauteng",
                  "eskde-4-stellenboschnustellenboschwesterncape"]
    TEST_USERGROUPS = {"Matthew": ["Dota"],
                       "Mark": ["COD-MW", "Dota"],
                       "Luke": ["COD-MW", "Diablo"],
                       "John": ["Dota", "COD-MW"]}
    TEST_USERAREAS = {"Matthew": [TEST_AREAS[0]],
                      "Mark": [TEST_AREAS[1]],
                      "Luke": [TEST_AREAS[2]],
                      "John": [TEST_AREAS[1]]}

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    for p in TEST_USERS:
        cur.execute("INSERT INTO users (name) VALUES (?)", [p])
    conn.commit()
    for g in TEST_GROUPS:
        cur.execute("INSERT INTO groups (name) VALUES (?)", [g])
    conn.commit()
    for z in TEST_AREAS:
        cur.execute("INSERT INTO areas (name) VALUES (?)", [z])
    conn.commit()

    for usr in TEST_USERGROUPS:
        for grp in TEST_USERGROUPS[usr]:
            cur.execute("INSERT INTO user_groups (user_id, group_id) \
                        VALUES ((SELECT id FROM users WHERE name = ?), (SELECT id FROM groups WHERE name = ?));", [usr, grp])
    conn.commit()

    for usr in TEST_USERAREAS:
        for zn in TEST_USERAREAS[usr]:
            cur.execute("INSERT INTO user_areas (user_id, area_id) \
                        VALUES ((SELECT id FROM users WHERE name = ?), (SELECT id FROM areas WHERE name = ?));", [usr, zn])
    conn.commit()
    cur.close()
    conn.close()


def _exec_sql(sql, data_tuple):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(sql, data_tuple)
    conn.commit()
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


def add_name(table, name):
    """
    Adds a name to a table.
    Should work for users, areas and groups.
    """
    sql = "SELECT * FROM {} WHERE name LIKE (?);".format(table)
    items = _exec_sql(sql, (name,))
    if len(items) == 0:
        sql = "INSERT INTO {} (name) VALUES (?);".format(table)
        _exec_sql(sql, [name])


def get_id(table, name):
    """
    Return the ID of a name for a given table
    Returns -1 if the name was not found
    """
    sql = "Select id from {} where name = (?);".format(table)
    try:
        return _exec_sql(sql, (name,))[0][0]
    except:
        return -1


def get_name(table, id):
    """
    Return the name of an ID for a given table
    """
    sql = "Select name from {} where id = (?);".format(table)
    return _exec_sql(sql, (id,))[0][0]


def _check_userdatapair_exists(user, table, value):
    """
    Checks if a user-data value paid exists. 
    E.g. Calling with "user, areas, claremont" will check if user has claremont in their areas
    """
    sql = "SELECT * FROM user_{} WHERE \
            user_id in (SELECT id FROM users WHERE name = ?) AND \
            {}_id in (SELECT id FROM {} WHERE name = ?);".format(table, table[:-1], table)
    results = _exec_sql(sql, (user, value))
    return not len(results) == 0


def insert_userdata_pair(user, table, data):
    """
    Creates an entry in an assosciation table.
    """
    # check if both the user and the <table>s data exist in the database, and add them if not
    add_name("users", user)
    add_name(table, data)
    if not _check_userdatapair_exists(user, table, data):
        sql = "INSERT INTO user_{} (user_id, {}_id) \
            VALUES ((SELECT id FROM users WHERE name = ?), (SELECT id FROM {} WHERE name = ?));".format(table, table[:-1], table)
        _exec_sql(sql, (user, data))

def remove_userdata_pair(user, table, data):
    """
    Removes an entry from an assosciation table.
    """
    if _check_userdatapair_exists(user, table, data):
        sql = "DELETE FROM user_{} WHERE (user_id, {}_id) = \
            ((SELECT id FROM users WHERE name = ?), (SELECT id FROM {} WHERE name = ?));".format(table, table[:-1], table)
        _exec_sql(sql, (user, data))

def get_all_members():
    sql = "SELECT DISTINCT id FROM users;"
    results =  _exec_sql(sql, {})
    return [i[0] for i in results]

def get_groups():
    sql = "SELECT name FROM groups;"
    return _exec_sql(sql, ())

def remove_group(group_id):
    sql = "DELETE FROM groups WHERE id = ?;"
    _exec_sql(sql, (group_id,))

def get_user_data(user, req_data):
    """
    Get a user's data
    :param str user: The user's name
    :param str req_data: Requested data, either "areas" or "groups"
    """
    # Given a specific user, get their user_id, then select distinct entries from the aggregation table
    # Select the names from the desired table
    sql = "SELECT name FROM {} WHERE id in ( \
            SELECT {}_id FROM user_{} where user_id = (\
                SELECT id FROM users WHERE name LIKE (?) \
            ) \
        );".format(req_data, req_data[:-1], req_data)
    return _exec_sql(sql, (user, ))


def get_group_id(group_name):
    results = _exec_sql(
        "SELECT id FROM groups WHERE name LIKE (?)", (group_name,))
    if len(results) == 1:
        return results[0][0]
    else:
        return -1


def get_group_members(group_id):
    """
    Get all the user ids in a group given the group ID
    """
    results = _exec_sql(
        "Select user_id from user_groups where group_id = (?)", (group_id,))
    if len(results) != 0:
        return [i[0] for i in results]
    else:
        return -1


def get_users_areas(user_id_array):
    """
    Given an array of user IDs, return all their area IDs
    """
    results = _exec_sql("SELECT DISTINCT area_id FROM user_areas WHERE user_id IN ({})".format(
        ','.join('?'*len(user_id_array))), user_id_array)
    if len(results) != 0:
        return [i[0] for i in results]
    else:
        return -1

def get_area_users_by_group(area, group):
    """
    Return all users in a given area, that are also in a given group
    """
    u_in_a = "Select user_id FROM user_areas WHERE area_id IN (SELECT id FROM areas WHERE areas.name = (?))"  ## with area as a param
    u_in_g = "SELECT user_id FROM user_groups WHERE group_id IN (SELECT id FROM groups WHERE groups.name = (?))"
    sql = "SELECT name FROM users where id in (" + u_in_a + ") AND (" + u_in_g + ")" 
    return _exec_sql(sql, (area, group,))

def get_group_area_names(group_name):
    if group_name.upper() == "ALL":
        sql = "Select name FROM areas WHERE id in( \
            SELECT DISTINCT area_id FROM user_areas \
            WHERE user_id IN ( \
                SELECT DISTINCT id FROM users \
            ) \
        );"
        results = _exec_sql(sql, {})
    else:
        sql = "Select name FROM areas WHERE id in( \
            SELECT DISTINCT area_id FROM user_areas \
            WHERE user_id IN ( \
                SELECT user_id FROM user_groups \
                WHERE group_id = (SELECT id FROM groups WHERE name like (?)) \
            ) \
         );"
        results = _exec_sql(sql, (group_name,))
    if len(results) != 0:
        return [r[0] for r in results]
    else:
        return []


if __name__ == "__main__":
    # create the test DB and populate with test data
    create_db()
    # populate_test_data()
    # TODO: run tests
