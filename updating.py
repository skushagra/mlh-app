import datetime
import subprocess
import requests
import sqlite3
import os

class update_assistant:
    
    def check_for_updates():
        conn = sqlite3.connect("webmailserver.db")
        url = 'https://raw.githubusercontent.com/skushagra/pvm/master/latest.json'
        user_version = list(conn.execute("SELECT variable_value FROM localPVMdesc WHERE lid=3"))[0][0]
        response = requests.get(url)
        if response.status_code == 200:
            latest_version = response.json()
            if latest_version['latest_version'] != user_version:
                return [True, latest_version]
            elif latest_version['latest_version'] == user_version:
                return [False, latest_version]
        else:
            print('Failed to retrieve latest version data.')
    
    def update(self, update_details):
        conn = sqlite3.connect("webmailserver.db")
        current_version = list(conn.execute("SELECT variable_value FROM localPVMdesc WHERE lid=3"))[0][0]
        new_config_url = update_details['config-assistant-download-url']
        new_service_url = update_details['config-assistant-download-url']
        new_version = update_details['latest_version']
        new_date = update_details['version-release-date']
        dir = f'./app-version-{new_version}'
        os.mkdir(dir)
        with open(f'{dir}/config-assistant-{new_version}.exe', 'wb') as config_file:
            config_file.write(requests.get(new_config_url).content)
        with open(f'{dir}/webmailprinter-{new_version}.exe', 'wb') as service_file:
            service_file.write(requests.get(new_service_url).content)
        assist_app_path = self.assist_location + f"/{self.assist_file_name}-{current_version}.exe"
        service_app_path = self.assist_location + f"/{self.service_file_name}-{current_version}.exe"
        new_assist_app_path = self.assist_location + f"/{self.assist_file_name}-{new_version}.exe"
        new_service_app_path = self.assist_location + f"/{self.service_file_name}-{new_version}.exe"
        os.rename(assist_app_path, new_assist_app_path)
        os.rename(service_app_path, new_service_app_path)
        subprocess.run(["powershell", f"rm -r ./app-version-{new_version}"], capture_output=True, text=True)
        

        months = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December",
        }

        conn.execute(f"UPDATE localPVMdesc SET variable_value='{new_version}' WHERE lid=3")
        conn.execute(f"UPDATE localPVMdesc SET variable_value='{new_date}' WHERE lid=5")
        cd = list(str(datetime.date.today()).split('-'))
        if cd[0][0] == '0':
            cd[0] = cd[0][1:]
        ud = cd[2] + " " + months[int(cd[1])] + " " + cd[0]
        conn.execute(f"UPDATE localPVMdesc SET variable_value='{ud}' WHERE lid=6")
        conn.commit()

        return "Update Successful"
            

    def principal(self):
        checker = update_assistant.check_for_updates()
        if checker[0]:
            self.update(checker[1])
    
    def __init__(self, assist_location, service_location, assist_file_name ,service_file_name):
        self.assist_location = assist_location
        self.service_location = service_location
        self.assist_file_name = assist_file_name
        self.service_file_name = service_file_name
        self.principal()