"""
Raceroom Commander
Created by Koen van Hove - koenvh.nl
"""

import json
import sqlite3
import time

import requests
import stringdist
import text_unidecode


class Server:
    database = None
    database_last_update = 0
    accepted_ids = []

    def __init__(self):
        self.database = sqlite3.connect("server.db")
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

    def main(self):
        print("Raceroom Commander")
        print("Created by Koen van Hove - koenvh.nl")
        print("See README for the available commands")
        print("--------")
        print("")
        server_data = self.get_data("dedi")

        config = json.load(open("server.json", "r"))

        process_ids = [x["GameSetting"]["Id"] for x in server_data]
        admin_ids = config["admin_ids"]
        minimum_rating = config["minimum_rating"]
        minimum_reputation = config["minimum_reputation"]
        whitelisted_ids = config["whitelisted_ids"]

        last_created_at = int(time.time())

        while True:
            try:
                new_last_created_at = last_created_at
                for process_id in process_ids:
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

                        elif command == "/slowdown":
                            if len(text_parts) < 2:
                                continue
                            if " " not in text_parts[1]:
                                continue
                            name, duration = text_parts[1].rsplit(" ", 1)
                            user_id = self.get_id_by_name(process_data, name)
                            self.post_data("user/penalty", {"ProcessId": int(process_id), "UserId": user_id,
                                                            "PenaltyType": "Slowdown", "Duration": int(duration)})

                        elif command == "/drivethrough" or command == "/drive-through":
                            if len(text_parts) < 2:
                                continue
                            user_id = self.get_id_by_name(process_data, text_parts[1])
                            self.post_data("user/penalty", {"ProcessId": int(process_id), "UserId": user_id,
                                                            "PenaltyType": "Drivethrough", "Duration": 10})

                        elif command == "/stopandgo" or command == "/stop-and-go":
                            if len(text_parts) < 2:
                                continue
                            user_id = self.get_id_by_name(process_data, text_parts[1])
                            self.post_data("user/penalty", {"ProcessId": int(process_id), "UserId": user_id,
                                                            "PenaltyType": "StopAndGo", "Duration": 10})

                        elif command == "/disqualify":
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
                                "/stopandgo NAME",
                                "/disqualify NAME",
                                "/next",
                                "/restart"
                            ]
                            self.post_data("chat/" + str(process_id) + "/admin",
                                           params={"Message": "; ".join(help_text)})

                    # end chat messages
                    for player in process_data["ProcessState"]["Players"]:
                        if player["UserId"] in self.accepted_ids:
                            continue
                        if player["UserId"] in whitelisted_ids:
                            self.accepted_ids.append(player["UserId"])
                            continue
                        c = self.database.cursor()
                        c.execute("SELECT UserId, Rating, Reputation, Fullname FROM players WHERE UserId = ?",
                                  (player["UserId"],))
                        entry = c.fetchone()
                        if entry is None:
                            entry = (player["UserId"], 0, 0, "player")
                        if entry[1] >= minimum_rating and entry[2] >= minimum_reputation:
                            self.accepted_ids.append(player["UserId"])
                            continue
                        msg = "Kicked " + entry[3] + " due to insufficient rating/reputation."
                        self.post_data("chat/" + str(process_id) + "/admin", params={"Message": msg})
                        self.post_data("user/kick", {"ProcessId": int(process_id), "UserId": player["UserId"]})
                        time.sleep(3)
                        self.get_data("dedi/" + str(process_id))
                        # TODO: Fix kick post request firing multiple times

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
