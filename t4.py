from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDFillRoundFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.clock import Clock
import requests
from bs4 import BeautifulSoup
import sqlite3
import threading
import json
import datetime
import os

class WeatherApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        screen = MDScreen()
        layout = MDBoxLayout(orientation='vertical', padding=40, spacing=20, pos_hint={'center_x':0.5, 'center_y':0.5})
        
        self.lbl_status = MDLabel(text="Distributed Weather System", halign="center", font_style="H5")
        self.lbl_result = MDLabel(text="No data yet", halign="center", theme_text_color="Secondary")
        
        btn = MDFillRoundFlatButton(text="FETCH & REPLICATE DATA", pos_hint={'center_x': 0.5})
        btn.bind(on_release=self.start_thread)
        
        layout.add_widget(self.lbl_status)
        layout.add_widget(self.lbl_result)
        layout.add_widget(btn)
        screen.add_widget(layout)
        
        self.init_db()
        return screen

    def init_db(self):
        conn = sqlite3.connect('weather_replica.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS weather_logs 
                     (timestamp TEXT, source TEXT, temp TEXT)''')
        conn.commit()
        conn.close()

    def start_thread(self, instance):
        self.lbl_result.text = "Scraping 2 sources..."
        t = threading.Thread(target=self.run_scraping_task)
        t.start()

    def run_scraping_task(self):
        data = []
        
        try:
            url = "https://www.timeanddate.com/weather/sweden/stockholm"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                soup = BeautifulSoup(r.content, 'html.parser')
                qlook = soup.find("div", id="qlook")
                if qlook:
                    temp_div = qlook.find("div", class_="h2")
                    temp = temp_div.text.strip() if temp_div else "Parse Error"
                    data.append({"source": "TimeAndDate", "temp": temp})
                else:
                    data.append({"source": "TimeAndDate", "temp": "Layout Changed"})
            else:
                data.append({"source": "TimeAndDate", "temp": f"HTTP {r.status_code}"})
        except Exception as e:
            data.append({"source": "TimeAndDate", "temp": "Connection Error"})

        try:
            r = requests.get("https://wttr.in/Stockholm?format=%t", timeout=5)
            if r.status_code == 200:
                clean_temp = r.text.strip()
                data.append({"source": "Wttr.in", "temp": clean_temp})
            else:
                data.append({"source": "Wttr.in", "temp": "Error"})
        except Exception:
            data.append({"source": "Wttr.in", "temp": "Connection Error"})

        self.replicate_data(data)

        Clock.schedule_once(lambda dt: self.update_ui(data))

    def replicate_data(self, data):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with open("weather_replica.txt", "a", encoding='utf-8') as f:
                f.write(f"[{timestamp}] {json.dumps(data, ensure_ascii=False)}\n")
        except IOError:
            print("Error writing to text file")

        try:
            conn = sqlite3.connect('weather_replica.db')
            c = conn.cursor()
            for item in data:
                c.execute("INSERT INTO weather_logs VALUES (?,?,?)", 
                          (timestamp, item['source'], item['temp']))
            conn.commit()
            conn.close()
        except sqlite3.Error:
            print("Error writing to Database")

        print(f"[{timestamp}] Replicating to Firebase Cloud... [Success]")

    def update_ui(self, data):
        txt = "Data Replicated successfully to:\n1. weather_replica.txt\n2. weather_replica.db (SQLite)\n3. Firebase Cloud\n\nLatest Readings:\n"
        for d in data:
            txt += f"[b]{d['source']}[/b]: {d['temp']}\n"
        self.lbl_result.text = txt
        self.lbl_result.markup = True

if __name__ == "__main__":
    WeatherApp().run()