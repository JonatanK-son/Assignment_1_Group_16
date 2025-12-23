from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDFillRoundFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, TwoLineListItem
from kivy.clock import Clock
import requests
from bs4 import BeautifulSoup
import sqlite3
import threading
import json
import datetime

FIREBASE_URL = "https://assignment1-cd4b1-default-rtdb.europe-west1.firebasedatabase.app/weather.json"

#define the UI for kivy
class WeatherApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        screen = MDScreen()
        layout = MDBoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.lbl_title = MDLabel(
            text="Distributed Weather System", 
            halign="center", 
            font_style="H5",
            size_hint_y=None, 
            height=50
        )
        
        self.lbl_status = MDLabel(
            text="System Ready", 
            halign="center", 
            theme_text_color="Hint",
            size_hint_y=None, 
            height=30
        )

        scroll = MDScrollView()
        self.result_list = MDList()
        scroll.add_widget(self.result_list)
        
        btn_box = MDBoxLayout(padding=[0, 20, 0, 20], size_hint_y=None, height=80)
        btn = MDFillRoundFlatButton(
            text="FETCH & REPLICATE DATA", 
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        btn.bind(on_release=self.start_thread)
        btn_box.add_widget(btn)
        
        layout.add_widget(self.lbl_title)
        layout.add_widget(self.lbl_status)
        layout.add_widget(scroll)
        layout.add_widget(btn_box)
        screen.add_widget(layout)
        
        self.init_db()
        return screen


    #create Local DB if it doesnt exist.
    def init_db(self):
        try:
            conn = sqlite3.connect('weather_replica.db')
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS weather_logs 
                         (timestamp TEXT, source TEXT, location TEXT, 
                          temp TEXT, humidity TEXT)''')
            conn.commit()
            conn.close()
        except Exception as e:
            self.lbl_status.text = f"DB Init Error: {e}"

    def start_thread(self, instance):
        self.lbl_status.text = "Scraping Stockholm weather..."
        self.result_list.clear_widgets()
        t = threading.Thread(target=self.run_scraping_task)
        t.start()

    #Scrape the data from timeanddate and wttr, if fail default to error handling.
    def run_scraping_task(self):
        results = []
        target_city = "Stockholm"
        
        try:
            url = "https://www.timeanddate.com/weather/sweden/stockholm"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.content, 'html.parser')
                
                temp_div = soup.find("div", class_="h2")
                temp = temp_div.text.strip() if temp_div else "N/A"
                
                hum = "N/A"
                th = soup.find("th", string=lambda text: text and "Humidity" in text)
                if th:
                    td = th.find_next_sibling("td")
                    hum = td.text.strip() if td else "N/A"
                
                results.append({
                    "source": "TimeAndDate",
                    "location": target_city,
                    "temp": temp,
                    "humidity": hum
                })
            else:
                results.append(self.create_error("TimeAndDate", "HTTP Error"))
        except Exception:
            results.append(self.create_error("TimeAndDate", "Connection Error"))

        try:
            url = f"https://wttr.in/{target_city}?format=%l|%t|%h"
            r = requests.get(url, timeout=10)
            
            if r.status_code == 200:
                parts = r.text.strip().split('|')
                
                if len(parts) >= 3:
                    results.append({
                        "source": "Wttr.in",
                        "location": parts[0].strip(),
                        "temp": parts[1].strip(),
                        "humidity": parts[2].strip()
                    })
                else:
                    results.append(self.create_error("Wttr.in", "Parse Error (Unexpected Format)"))
            else:
                results.append(self.create_error("Wttr.in", f"HTTP {r.status_code}"))
        except Exception as e:
            results.append(self.create_error("Wttr.in", f"Connection Error"))

        self.replicate_data(results)
        Clock.schedule_once(lambda dt: self.update_ui(results))

    def create_error(self, source, msg):
        return {"source": source, "location": "Unknown", "temp": msg, "humidity": "-"}


    #Save the data that is scraped to a .txt, local DB and firebase DB
    def replicate_data(self, data):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with open("weather_replica.txt", "a", encoding='utf-8') as f:
                f.write(f"[{timestamp}] {json.dumps(data, ensure_ascii=False)}\n")
        except IOError:
            print("Text File Error")

        try:
            conn = sqlite3.connect('weather_replica.db')
            c = conn.cursor()
            for item in data:
                c.execute("INSERT INTO weather_logs VALUES (?,?,?,?,?)", 
                          (timestamp, item['source'], item['location'], 
                           item['temp'], item['humidity']))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"DB Error: {e}")

        try:
            firebase_payload = {
                "timestamp": timestamp,
                "readings": data
            }
            requests.post(FIREBASE_URL, json=firebase_payload)
            print("Firebase Success")
        except Exception as e:
            print(f"Firebase Failed: {e}")


    #update the UI after task is complete.
    def update_ui(self, data):
        self.lbl_status.text = "Replication Complete"
        
        for item in data:
            details = f"Loc: {item['location']} | Temp: {item['temp']} | Hum: {item['humidity']}"
            
            list_item = TwoLineListItem(
                text=f"[b]{item['source']}[/b]",
                secondary_text=details,
                theme_text_color="Primary"
            )
            self.result_list.add_widget(list_item)

if __name__ == "__main__":
    WeatherApp().run()