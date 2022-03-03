from getpass import getpass
from mysql.connector import connect, Error
import sqlite3
import random
from config import *

db_name = "db.db"

def get_votes(msg):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    votes = cur.execute(f"SELECT * FROM votes WHERE `msg` = {msg.id}").fetchall()
    con.close()
    if votes != []:
        return votes[0]
    return None

def new_votes(msg, type):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    votes = cur.execute(f"INSERT INTO votes (msg, type) VALUES ({msg.id}, {type})")
    con.commit()
    con.close()
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    votes = cur.execute(f"SELECT * FROM votes WHERE `msg` = {msg.id}").fetchall()
    con.close()
    if votes != []:
        return votes[0]
    return None

def get_vote(msg, member):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    votes = cur.execute(f"SELECT * FROM vote WHERE `msg` = {msg.id} AND `member` = {member.id}").fetchall()
    con.close()
    if votes != []:
        return votes[0]
    return None

def new_vote(msg, member, vote):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    votes = cur.execute(f"INSERT INTO vote (msg, member, vote) VALUES ({msg.id}, {member.id}, {vote})")
    con.commit()
    con.close()
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    votes = cur.execute(f"SELECT * FROM vote WHERE `msg` = {msg.id} AND `member` = {member.id}").fetchall()
    con.close()
    if votes != []:
        return votes[0]
    return None

def remove_vote(msg, member, vote):
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    votes = cur.execute(f"DELETE FROM vote WHERE `msg` = {msg.id} AND `member` = {member.id} AND `vote` = {vote}")
    con.commit()
    con.close()
    
def add_permission(id, nick):
    with connect(
        host = sql_data["host"],
        port = sql_data["port"],
        user = sql_data["user"],
        password = sql_data["password"],
        database = sql_data["database"]
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM accounts WHERE `nick` = '{nick}'")
            # Fetch rows from last executed query
            result = cursor.fetchall()
            uuid = result[0][1]
            cursor.execute(f"SELECT * FROM luckperms_user_permissions WHERE `uuid` = '{uuid}' AND `permission`= 'group.{permissions[id]}'")
            result = cursor.fetchall()
            if len(result) >= 1:
                user = result[0]
                print(user)
            else:
                cursor.execute(f"INSERT INTO luckperms_user_permissions (uuid, permission, value, server, world, expiry, contexts) VALUES ('{uuid}', 'group.{permissions[id]}', 1, '{server}', '{world}', 0, '" + "{}" + "')")
            connection.commit()

def remove_permission(id, nick):
    with connect(
        host = sql_data["host"],
        port = sql_data["port"],
        user = sql_data["user"],
        password = sql_data["password"],
        database = sql_data["database"]
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM accounts WHERE `nick` = '{nick}'")
            # Fetch rows from last executed query
            result = cursor.fetchall()
            uuid = result[0][1]
            cursor.execute(f"SELECT * FROM luckperms_user_permissions WHERE `uuid` = '{uuid}' AND `permission`= 'group.{permissions[id]}'")
            result = cursor.fetchall()
            cursor.execute(f"DELETE FROM luckperms_user_permissions WHERE `uuid` = '{uuid}' AND `permission`= 'group.{permissions[id]}'")
            connection.commit()

def check_user(id):
    with connect(
        host = sql_data["host"],
        port = sql_data["port"],
        user = sql_data["user"],
        password = sql_data["password"],
        database = sql_data["database"]
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM accounts WHERE `discord` = {id}")
            # Fetch rows from last executed query
            result = cursor.fetchall()
            if len(result) == 0:
                return False
            elif len(result) == 1:
                return result[0]
            elif len(result) >= 1:
                for i in result:
                    if i[11] == 1:
                        return i

def check_user_prik(id):
    us = check_user(id)
    with connect(
        host = sql_data["host"],
        port = sql_data["port"],
        user = sql_data["user"],
        password = sql_data["password"],
        database = sql_data["database"]
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM accounts")
            # Fetch rows from last executed query
            result = cursor.fetchall()
            if len(result) == 0:
                return False
            elif len(result) == 1:
                return result[0]
            elif len(result) >= 1:
                id = us[0]
                print(id)
                if id + 50 < result[-1][0] and id - 50 > result[0][0]:
                    c = random.randint(-50, 50)
                    try:
                        res = result[id + c]
                        return res
                    except:
                        return result[id + c - 2]
                elif id + 50 < result[-1][0]:
                    c = random.randint(5, 50)
                    try:
                        res = result[id + c]
                        return res
                    except:
                        return result[id + c - 2]
                elif id - 50 > result[0][0]:
                    c = random.randint(-50, -5)
                    try:
                        res = result[id + c]
                        return res
                    except:
                        return result[id + c - 2]

def check_online_user(nick):
    with connect(
        host = sql_data["host"],
        port = sql_data["port"],
        user = sql_data["user"],
        password = sql_data["password"],
        database = sql_data["database"]
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM hours WHERE `nick` = '{nick}'")
            result = cursor.fetchall()
            if len(result) == 1:
                return result[0]

def get_city(id):
    user = check_user(id)
    if user:
        city_id = user[6]
        if city_id != 0:
            with connect(
                host = sql_data["host"],
                port = sql_data["port"],
                user = sql_data["user"],
                password = sql_data["password"],
                database = sql_data["database"]
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM cities WHERE `id` = {city_id}")
                    # Fetch rows from last executed query
                    result = cursor.fetchall()
                    if len(result) == 0:
                        return False
                    elif len(result) == 1:
                        return result[0]
        else:
            return False

def get_city_role(id):
    user = check_user(id)
    if user:
        user_id = user[0]
        with connect(
            host = sql_data["host"],
            port = sql_data["port"],
            user = sql_data["user"],
            password = sql_data["password"],
            database = sql_data["database"]
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM city_roles WHERE `account` = {user_id}")
                # Fetch rows from last executed query
                result = cursor.fetchall()
                if len(result) == 0:
                    return False
                elif len(result) == 1:
                    return result[0]

def get_sinking():
    with connect(
        host = sql_data["host"],
        port = sql_data["port"],
        user = sql_data["user"],
        password = sql_data["password"],
        database = sql_data["database"]
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM orders_new")
            # Fetch rows from last executed query
            result = cursor.fetchall()
            if result[-1][3]:
                con = sqlite3.connect(db_name)
                cur = con.cursor()
                votes = cur.execute(f"SELECT * FROM new_order WHERE `nick` = '{result[-1][3]}'").fetchall()
                con.close()
                if votes != []:
                    return False
                else:
                    con = sqlite3.connect(db_name)
                    cur = con.cursor()
                    votes = cur.execute(f"INSERT INTO new_order (nick) VALUES ('{result[-1][3]}')")
                    con.commit()
                    con.close()
                    con = sqlite3.connect(db_name)
                    return result[-1]
            else:
                return False

def get_mute(member):
    with connect(
        host = sql_data["host"],
        port = sql_data["port"],
        user = sql_data["user"],
        password = sql_data["password"],
        database = sql_data["database"]
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM discord_mutes WHERE `discord` = {member.id}")
            result = cursor.fetchall()
            if result != []:
                return result[0]
            return None

def new_valentine(member):
    print(member.display_name)
    with connect(
        host = sql_data["host"],
        port = sql_data["port"],
        user = sql_data["user"],
        password = sql_data["password"],
        database = sql_data["database"]
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM discord_valentine WHERE `discord` = {member.id}")
            result = cursor.fetchall()
            if result != []:
                cursor.execute(f"UPDATE discord_valentine SET count = {result[0][1] + 1}")
                connection.commit()
                return
            cursor.execute(f"INSERT INTO discord_valentine (discord, count) VALUES ({member.id}, 1)")
            connection.commit()

def new_mute(member, duration, end_time, reason, moder):
    with connect(
        host = sql_data["host"],
        port = sql_data["port"],
        user = sql_data["user"],
        password = sql_data["password"],
        database = sql_data["database"]
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"INSERT INTO discord_mutes (discord, duration, end_time, reason, moder_discord) VALUES ({member.id}, '{duration}', {end_time}, '{reason}', {moder.id})")
            connection.commit()

def remove_mute(member):
    with connect(
        host = sql_data["host"],
        port = sql_data["port"],
        user = sql_data["user"],
        password = sql_data["password"],
        database = sql_data["database"]
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM discord_mutes WHERE `discord` = {member.id}")
            connection.commit()

def get_courts():
    with connect(
        host = sql_data["host"],
        port = sql_data["port"],
        user = sql_data["user"],
        password = sql_data["password"],
        database = sql_data["database"]
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM courts_cases")
            # Fetch rows from last executed query
            result = cursor.fetchall()
            if result[-1][3]:
                con = sqlite3.connect(db_name)
                cur = con.cursor()
                votes = cur.execute(f"SELECT * FROM new_courts WHERE `id` = '{result[-1][0]}'").fetchall()
                con.close()
                if votes != []:
                    return False
                else:
                    con = sqlite3.connect(db_name)
                    cur = con.cursor()
                    votes = cur.execute(f"INSERT INTO new_courts (id) VALUES ('{result[-1][0]}')")
                    con.commit()
                    con.close()
                    con = sqlite3.connect(db_name)
                    return result[-1]
            else:
                return False