"""
Raceroom Commander
Created by Koen van Hove - koenvh.nl
"""

import json
import sqlite3
import time

import commentjson
import requests
import stringdist
import text_unidecode


class Server:
    database = None
    database_last_update = 0

    accepted_ids = set([])
    # TODO Remove once RaceRoom fixes their banning system to work before a restart
    banned_ids = set([])
    points = {}

    def __init__(self):
        self.database = sqlite3.connect("rrcommander.db")
        self.update_database()

    def update_database(self):
        players = requests.get("http://game.raceroom.com/multiplayer-rating/ratings.json").json()
        if not len(players) > 100:
            # Something went wrong with retrieving the data (less than 100 entries is unlikely), so abort.
            return

        self.database_last_update = int(time.time())
        c = self.database.cursor()
        c.execute("DROP TABLE IF EXISTS players")
        c.execute("""
                CREATE TABLE players (UserId INTEGER, 
                Username TEXT, 
                Fullname TEXT, 
                Rating REAL, 
                RacesCompleted INTEGER, 
                Reputation REAL)""")
        c.execute("CREATE INDEX idx_UserId ON players(UserId)")
        c.execute("CREATE INDEX idx_Username ON players(Username)")
        c.execute("CREATE INDEX idx_Fullname ON players(Fullname)")
        players_db = [(x["UserId"],
                       x["Username"],
                       x["Fullname"],
                       x["Rating"],
                       x["RacesCompleted"],
                       x["Reputation"]) for x in players]
        c.executemany("INSERT INTO players VALUES (?, ?, ?, ?, ?, ?)", players_db)
        self.database.commit()

    def get_data(self, url):
        data = requests.get("http://localhost:8088/" + url, headers={"X-Requested-With": "XmlHttpRequest"})
        return data.json()

    def post_data(self, url, params):
        print(url, params)
        data = requests.post("http://localhost:8088/" + url, json=params, headers={"X-Requested-With": "XmlHttpRequest"})

    def normalise_string(self, string):
        return text_unidecode.unidecode(string).lower()

    def get_id_by_name(self, process, name):
        players = [x["UserId"] for x in process["ProcessState"]["Players"]]
        players_info = []

        c = self.database.cursor()

        for player in players:
            c.execute("SELECT Fullname FROM players WHERE UserId = ?", (player,))
            entry = c.fetchone()
            if entry:
                players_info.append({"id": player, "name": entry[0]})
            else:
                player_data = requests.get("http://game.raceroom.com/utils/user-info/" + str(player)).json()
                players_info.append({"id": player, "name": player_data["name"]})

        user_distance = 99999999
        user_id = 0
        for player in players_info:
            distance = stringdist.levenshtein_norm(self.normalise_string(name),
                                                   self.normalise_string(player["name"]))
            # print(player["name"] + ": " + str(distance))
            if distance < user_distance:
                user_distance = distance
                user_id = player["id"]
        return user_id

    def get_name_by_id(self, user_id):
        c = self.database.cursor()
        c.execute("SELECT Fullname FROM players WHERE UserId = ?", (user_id,))
        entry = c.fetchone()
        if entry:
            return entry[0]
        else:
            try:
                player_data = requests.get("http://game.raceroom.com/utils/user-info/" + str(user_id)).json()
                return player_data["name"]
            except requests.exceptions.ConnectionError:
                return "player"

    def main(self):
        print("Raceroom Commander")
        print("Created by Koen van Hove - koenvh.nl")
        print("See README for the available commands")
        print("--------")
        print("")
        server_data = self.get_data("dedi")

        config = commentjson.loads(open("rrcommander.json", "r").read())

        process_ids = [x["GameSetting"]["Id"] for x in server_data]

        last_created_at = int(time.time())

        while True:
            try:
                new_last_created_at = last_created_at

                for server_no, process_id in enumerate(process_ids):
                    admin_ids = set(config["servers"][server_no]["admin_ids"])
                    minimum_rating = config["servers"][server_no]["minimum_rating"]
                    minimum_reputation = config["servers"][server_no]["minimum_reputation"]
                    incident_intervals = set(config["servers"][server_no]["incident_intervals"])
                    incident_types = set(config["servers"][server_no]["incident_types"])
                    whitelisted_ids = set(config["servers"][server_no]["whitelisted_ids"])

                    process_data = self.get_data("dedi/" + str(process_id))
                    chat_messages = self.get_data("chat/" + str(process_id))
                    if "messages" not in chat_messages:
                        continue
                    for message in chat_messages["messages"]:
                        if message["CreatedAt"] <= last_created_at:
                            continue
                        new_last_created_at = max(message["CreatedAt"], new_last_created_at)

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
                            user_id = self.get_id_by_name(process_data, text_parts[1])
                            self.post_data("user/kick", {"ProcessId": int(process_id), "UserId": user_id})

                        elif command == "/ban":
                            if len(text_parts) < 2:
                                continue
                            user_id = self.get_id_by_name(process_data, text_parts[1])
                            self.banned_ids.add(user_id)
                            self.post_data("user/ban", {"ProcessId": int(process_id), "UserId": user_id})

                        elif command == "/penalty":
                            if len(text_parts) < 2:
                                continue
                            if " " not in text_parts[1]:
                                continue
                            name, penalty = text_parts[1].rsplit(" ", 1)
                            user_id = self.get_id_by_name(process_data, name)

                            penalties = ["Slowdown", "Drivethrough", "StopAndGo", "Disqualify"]
                            penalty_distance = 99999999
                            penalty_name = ""
                            for p in penalties:
                                distance = stringdist.levenshtein_norm(self.normalise_string(p),
                                                                       self.normalise_string(penalty))
                                if distance < penalty_distance:
                                    penalty_distance = distance
                                    penalty_name = p

                            self.post_data("user/penalty", {"ProcessId": int(process_id), "UserId": user_id,
                                                            "PenaltyType": penalty_name, "Duration": 3})

                        elif command == "/slowdown" or command == "/sd":
                            if len(text_parts) < 2:
                                continue
                            duration = 3
                            if " " in text_parts[1]:
                                name, duration_text = text_parts[1].rsplit(" ", 1)
                                if str(duration_text).isdigit():
                                    duration = int(duration_text)
                                else:
                                    name = text_parts[1]
                            else:
                                name = text_parts[1]
                            user_id = self.get_id_by_name(process_data, name)
                            self.post_data("user/penalty", {"ProcessId": int(process_id), "UserId": user_id,
                                                            "PenaltyType": "Slowdown", "Duration": int(duration)})

                        elif command == "/drivethrough" or command == "/drive-through" or command == "/dt":
                            if len(text_parts) < 2:
                                continue
                            user_id = self.get_id_by_name(process_data, text_parts[1])
                            self.post_data("user/penalty", {"ProcessId": int(process_id), "UserId": user_id,
                                                            "PenaltyType": "Drivethrough", "Duration": 10})

                        elif command == "/stopandgo" or command == "/stop-and-go" or command == "/sg":
                            if len(text_parts) < 2:
                                continue
                            duration = 3
                            if " " in text_parts[1]:
                                name, duration_text = text_parts[1].rsplit(" ", 1)
                                if str(duration_text).isdigit():
                                    duration = int(duration_text)
                                else:
                                    name = text_parts[1]
                            else:
                                name = text_parts[1]
                            user_id = self.get_id_by_name(process_data, name)
                            self.post_data("user/penalty", {"ProcessId": int(process_id), "UserId": user_id,
                                                            "PenaltyType": "StopAndGo", "Duration": duration})

                        elif command == "/disqualify" or command == "/dq":
                            if len(text_parts) < 2:
                                continue
                            user_id = self.get_id_by_name(process_data, text_parts[1])
                            self.post_data("user/penalty", {"ProcessId": int(process_id), "UserId": user_id,
                                                            "PenaltyType": "Disqualify", "Duration": 10})

                        elif command == "/restart":
                            self.post_data("session/" + str(process_id), params={"Command": "Restart"})

                        elif command == "/next":
                            self.post_data("session/" + str(process_id), params={"Command": "ProceedNext"})

                        elif command == "/help":
                            help_text = [
                                "/kick NAME",
                                "/ban NAME",
                                "/slowdown NAME DURATION",
                                "/drivethrough NAME",
                                "/stopandgo NAME DURATION",
                                "/disqualify NAME",
                                "/next",
                                "/restart"
                            ]
                            self.post_data("chat/" + str(process_id) + "/admin",
                                           params={"Message": "; ".join(help_text)})

                    # end chat messages
                    for player in process_data["ProcessState"]["Players"]:
                        if player["UserId"] in self.banned_ids:
                            # TODO Remove once RaceRoom fixes their banning system to work before a restart
                            # Player was banned, so don't come back please
                            self.post_data("user/kick", {"ProcessId": int(process_id), "UserId": player["UserId"]})
                            continue
                        if player["UserId"] in self.accepted_ids:
                            # Player was already accepted, so don't check again
                            continue
                        if player["UserId"] in whitelisted_ids:
                            # Player is whitelisted, and gets access anyway
                            self.accepted_ids.add(player["UserId"])
                            continue
                        c = self.database.cursor()
                        c.execute("SELECT UserId, Rating, Reputation, Fullname FROM players WHERE UserId = ?",
                                  (player["UserId"],))
                        entry = c.fetchone()
                        if entry is None:
                            # Player has never driven ranked, and has no entry in the database
                            # Create a dummy with rating/reputation 0
                            name = self.get_name_by_id(player["UserId"])
                            entry = (player["UserId"], 0, 0, name)
                        if entry[1] >= minimum_rating and entry[2] >= minimum_reputation:
                            # Player meets the requirements to join
                            self.accepted_ids.add(player["UserId"])
                            continue

                        if entry[1] < minimum_rating:
                            # Player kicked due to not meeting minimum rating requirement
                            # Only determines the chat message shown
                            msg = "Kicked " + entry[3] + " due to insufficient rating (" + \
                                  str(entry[1]) + "/" + str(minimum_rating) + ")."
                            self.post_data("chat/" + str(process_id) + "/admin", params={"Message": msg})
                        elif entry[2] < minimum_reputation:
                            # Player kicked due to not meeting minimum reputation requirement
                            # Only determines the chat message shown
                            msg = "Kicked " + entry[3] + " due to insufficient reputation (" + \
                                  str(entry[2]) + "/" + str(minimum_reputation) + ")."
                            self.post_data("chat/" + str(process_id) + "/admin", params={"Message": msg})

                        self.post_data("user/kick", {"ProcessId": int(process_id), "UserId": player["UserId"]})
                        # Kick player, and wait five seconds to prevent chat message spam
                        time.sleep(5)
                        # TODO: Fix kick post request firing multiple times

                    # end reputation/rating check

                    for player in process_data["ProcessState"]["Players"]:
                        points = sum([x["Points"] for x in player["Incidents"] if x["Type"] in incident_types])
                        if player["UserId"] not in self.points:
                            self.points[player["UserId"]] = points
                        else:
                            for i in range(self.points[player["UserId"]] + 1, points + 1):
                                if i in incident_intervals:
                                    name = self.get_name_by_id(player["UserId"])
                                    msg = "Awarded a drive-through penalty to " + name + " for getting "\
                                          + str(i) + " incident points."
                                    self.post_data("chat/" + str(process_id) + "/admin", params={"Message": msg})
                                    self.post_data("user/penalty", {
                                        "ProcessId": int(process_id),
                                        "UserId": player["UserId"],
                                        "PenaltyType": "Drivethrough",
                                        "Duration": 10
                                    })
                        self.points[player["UserId"]] = points
                    # end points check

                last_created_at = new_last_created_at

                if int(time.time()) - self.database_last_update > 15 * 60:
                    print("Updating database...")
                    self.update_database()
            except Exception as e:
                import traceback
                traceback.print_exc()

            time.sleep(0.5)


if __name__ == "__main__":
    s = Server()
    s.main()
