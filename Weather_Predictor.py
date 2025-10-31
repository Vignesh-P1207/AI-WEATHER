import tkinter as tk
from tkinter import ttk, messagebox
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pyttsx3
import threading
import os

API_KEY = "2c9f67f58b9a7f3465c2b68b0ce5f413"
BG_IMAGE = "bg.jpg"

def predict_rain(humidity, cloudiness, temp):
    high_hum = humidity > 80
    mod_hum  = 60 <= humidity <= 80
    high_cld = cloudiness > 70
    mod_cld  = 50 <= cloudiness <= 70
    opt_temp = 20 <= temp <= 35
    if high_hum and high_cld and opt_temp:
        pred = "High chance of Rain"
        rain_score = 3
        cld_score = 2
    elif (high_hum or mod_hum) and (high_cld or mod_cld):
        pred = "Moderate chance of Rain"
        rain_score = 2
        cld_score = 1 if high_cld else 0.5
    else:
        pred = "Low chance of Rain"
        rain_score = 1
        cld_score = 0.5 if mod_cld else 0
    return pred, rain_score, cld_score

def fetch_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            hum = data['main']['humidity']
            cld = data['clouds']['all']
            tmp = data['main']['temp'] - 273.15
            return hum, cld, round(tmp, 1)
        else:
            return None
    except Exception as e:
        print("API error:", e)
        return None

def speak(text):
    def run():
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run, daemon=True).start()

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Weather Predictor – Logical Reasoning")
        self.root.geometry("800x700")
        self.root.configure(bg="#0a0a1f")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Orbitron', 12, 'bold'),
                        foreground='#00ffcc', background='#ff00ff')
        style.map('TButton', background=[('active', '#ff33ff')])
        if os.path.exists(BG_IMAGE):
            from PIL import Image, ImageTk
            img = Image.open(BG_IMAGE).resize((800, 700))
            self.bg = ImageTk.PhotoImage(img)
            lbl_bg = tk.Label(root, image=self.bg)
            lbl_bg.place(x=0, y=0, relwidth=1, relheight=1)
        title = tk.Label(root, text="AI Weather Predictor",
                         font=('Orbitron', 26, 'bold'),
                         fg='#00ffcc', bg='#0a0a1f',
                         bd=0, highlightthickness=0)
        title.pack(pady=20)
        sub = tk.Label(root, text="Powered by Logical Reasoning",
                       font=('Orbitron', 14),
                       fg='#ff00ff', bg='#0a0a1f')
        sub.pack(pady=5)
        frm = tk.Frame(root, bg='#0a0a1f')
        frm.pack(pady=20)
        tk.Label(frm, text="City:", font=('Orbitron', 14),
                 fg='#ffffff', bg='#0a0a1f').grid(row=0, column=0, padx=10)
        self.city_var = tk.StringVar()
        entry = tk.Entry(frm, textvariable=self.city_var,
                         font=('Orbitron', 14), width=25,
                         bg='#1c1c3a', fg='#00ffcc', insertbackground='#ff00ff')
        entry.grid(row=0, column=1, padx=10)
        btn = ttk.Button(frm, text="Predict Rain", command=self.start_prediction)
        btn.grid(row=0, column=2, padx=10)
        self.result_frame = tk.Frame(root, bg='#0a0a1f')
        self.result_frame.pack(expand=True, fill='both', padx=40, pady=20)
        self.fig, self.ax = plt.subplots(figsize=(5, 3), facecolor='#0a0a1f')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.result_frame)
        self.canvas.get_tk_widget().pack(side='top', fill='both', expand=True)

    def start_prediction(self):
        city = self.city_var.get().strip()
        if not city:
            messagebox.showwarning("Input", "Please enter a city name.")
            return
        for widget in self.result_frame.winfo_children():
            if widget != self.canvas.get_tk_widget():
                widget.destroy()
        self.ax.clear()
        loading = tk.Label(self.result_frame, text="Fetching data...",
                           font=('Orbitron', 14), fg='#ff00ff', bg='#0a0a1f')
        loading.pack(pady=10)
        threading.Thread(target=self.run_prediction, args=(city, loading),
                         daemon=True).start()

    def run_prediction(self, city, loading_lbl):
        data = fetch_weather(city)
        self.root.after(0, loading_lbl.destroy)
        if not data:
            self.root.after(0, lambda: messagebox.showerror(
                "Error", "Could not fetch weather data.\nCheck city name or API key."))
            return
        hum, cld, temp = data
        prediction, rain_score, cld_score = predict_rain(hum, cld, temp)
        self.root.after(0, self.display_result,
                        city.title(), temp, hum, cld,
                        rain_score, cld_score, prediction)

    def display_result(self, city, temp, hum, cld, rain_score, cld_score, pred):
        self.ax.clear()
        info = f"""
        {city}
        Temperature: {temp} °C
        Humidity: {hum}%
        Cloudiness: {cld}%
        Rain Score: {rain_score} (1=Low, 2=Moderate, 3=High)
        Cloudiness Score: {cld_score}
        Prediction: {pred}
        """
        lbl = tk.Label(self.result_frame, text=info.strip(),
                       font=('Orbitron', 14), fg='#00ffcc',
                       bg='#0a0a1f', justify='left')
        lbl.pack(pady=10)
        self.ax.bar(['Rain Score', 'Cloudiness Score'],
                    [rain_score, cld_score],
                    color=['#00ffcc', '#ff00ff'],
                    edgecolor='white')
        self.ax.set_facecolor('#0a0a1f')
        self.ax.tick_params(colors='white')
        self.ax.set_ylim(0, 3)
        self.ax.set_title("Logical Reasoning Scores", color='#ff00ff', fontsize=14)
        self.canvas.draw()
        speak_btn = ttk.Button(self.result_frame, text="Speak Prediction",
                               command=lambda: speak(
                                   f"In {city}, there is a {pred.lower()} with a rain score of {rain_score}."))
        speak_btn.pack(pady=10)
        again = ttk.Button(self.result_frame, text="Predict Again",
                           command=lambda: [w.destroy() for w in self.result_frame.winfo_children()
                                            if w != self.canvas.get_tk_widget()])
        again.pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    try:
        import tkinter.font as font
        font.nametofont("TkDefaultFont").configure(family="Orbitron")
    except:
        pass
    app = WeatherApp(root)
    root.mainloop()
