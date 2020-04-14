"""
Raceroom Commander
Created by Koen van Hove - koenvh.nl
"""

import json
import time

import requests
import stringdist
import unidecode


def get_data(url):
    data = requests.get("http://localhost:8088/" + url, headers={"X-Requested-With": "XmlHttpRequest"})
    return data.json()


def post_data(url, params):
    print(url, params)
    data = requests.post("http://localhost:8088/" + url, json=params, headers={"X-Requested-With": "XmlHttpRequest"})


def normalise_string(string):
    return unidecode.unidecode(string).lower()


cached_players = {}


def get_id_by_name(process, name):
    players = [x["UserId"] for x in process["ProcessState"]["Players"]]
    players_info = []
    for player in players:
        if player in cached_players:
            players_info.append(cached_players[player])
        else:
            player_data = requests.get("http://game.raceroom.com/utils/user-info/" + str(player)).json()
            cached_players[player] = player_data
            players_info.append(player_data)
        # print(player_data)

    user_distance = 99999999
    user_id = 0
    for player in players_info:
        distance = stringdist.levenshtein_norm(normalise_string(name),
                                               normalise_string(player["name"]))
        # print(player["name"] + ": " + str(distance))
        if distance < user_distance:
            user_distance = distance
            user_id = player["id"]
    return user_id


if __name__ == "__main__":
    print("Raceroom Commander")
    print("Created by Koen van Hove - koenvh.nl")
    print("--------")
    print("Commands:")
    print("/kick <NAME> - Kicks a player from the server")
    print("/ban <NAME> - Bans a player from the server")
    print("/penalty <NAME> <TYPE> - Penalise a player, either slowdown, drivethrough, stopandgo, or disqualify")
    print("/next - Continue to the next session")
    print("/restart - Restart the current session")
    print("")
    server_data = get_data("dedi")

    config = json.load(open("server.json", "r"))

    process_ids = [x["GameSetting"]["Id"] for x in server_data]
    admin_ids = config["admin_ids"]
    last_created_at = int(time.time())

    while True:
        try:
            for process_id in process_ids:
                process_data = get_data("dedi/" + str(process_id))

                chat_messages = get_data("chat/" + str(process_id))
                if "messages" not in chat_messages:
                    continue
                for message in chat_messages["messages"]:
                    if message["CreatedAt"] <= last_created_at:
                        continue
                    last_created_at = message["CreatedAt"]

                    if not message["UserId"] in admin_ids:
                        continue

                    text = message["Message"]
                    if str(text).startswith("/"):
                        print(text)

                    text_parts = text.split(" ", 1)
                    command = str(text_parts[0]).lower()

                    if command == "/kick":
                        if len(text_parts) < 2:
                            continue
                        user_id = get_id_by_name(process_data, text_parts[1])
                        post_data("user/kick", {"ProcessId": int(process_id), "UserId": user_id})

                    elif command == "/ban":
                        if len(text_parts) < 2:
                            continue
                        user_id = get_id_by_name(process_data, text_parts[1])
                        post_data("user/ban", {"ProcessId": int(process_id), "UserId": user_id})

                    elif command == "/penalty":
                        if len(text_parts) < 2:
                            continue
                        if " " not in text_parts[1]:
                            continue
                        name, penalty = text_parts[1].rsplit(" ", 1)
                        user_id = get_id_by_name(process_data, name)

                        penalties = ["Slowdown", "Drivethrough", "StopAndGo", "Disqualify"]
                        penalty_distance = 99999999
                        penalty_name = ""
                        for p in penalties:
                            distance = stringdist.levenshtein_norm(normalise_string(p),
                                                                   normalise_string(penalty))
                            if distance < penalty_distance:
                                penalty_distance = distance
                                penalty_name = p

                        post_data("user/penalty", {"ProcessId": int(process_id), "UserId": user_id,
                                                   "PenaltyType": penalty_name, "Duration": 3})

                    elif command == "/restart":
                        post_data("session/" + str(process_id), params={"Command": "Restart"})

                    elif command == "/next":
                        post_data("session/" + str(process_id), params={"Command": "ProceedNext"})

        except Exception as e:
            print(e)

        time.sleep(1)

