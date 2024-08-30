import base64
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import credentials
from google.auth.transport.requests import Request
import tkinter as tk
from tkinter import ttk
import smtplib
import ssl
import requests
import os
import pickle
import schedule
import time


def get_weather_data(city):
    api_key = "6f72b40cd5af9ba5f7920b977bb788b7"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()

    city_name = data["name"]
    temperature = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    weather_description = data["weather"][0]["description"]
    wind = data["wind"]["speed"]
    pressure = data["main"]["pressure"]
    # uv = data["uv"]
    uv_url = f"http://api.openweathermap.org/data/2.5/uvi?lat={data['coord']['lat']}&lon={data['coord']['lon']}&appid={api_key}"
    uv_response = requests.get(uv_url)
    uv_data = uv_response.json()
    uv = uv_data["value"]
    # Determine if an umbrella is required based on weather description
    umbrella_keywords = ['Rain', 'Showers', 'Drizzle', 'Light rain', 'Heavy rain', 'Thunderstorm', 'Storm', 'Precipitation', 'Pouring rain', 'Drenching rain', 'Downpour', 'Mist', 'Sprinkle', 'Scattered showers', 'Overcast', 'Cloudy', 'Gloomy', 'Hail', 'Sleet', 'Snow']


    is_umbrella_required = any(keyword in weather_description.lower() for keyword in umbrella_keywords)


    return city_name, temperature, humidity, weather_description, wind, pressure ,uv, is_umbrella_required



def send_email(city_name, temperature, humidity, weather_description, wind, pressure,uv, email , is_umbrella_required):
    email = email
    subject = f"Daily Weather Update for {city_name}"
    message = f"Temperature: {temperature}°C\nWind: {wind} m/s\nHumidity: {humidity}%\nPressure: {pressure} hPa\nUV: {uv}\nWeather: {weather_description}"
    
    if is_umbrella_required:
      message += "\nDon't forget to carry an umbrella!"
    else:
     message += "\nNo need to carry an umbrella."

    if uv >= 6:
     message += "\nRemember to protect yourself from UV radiation."
    else:
        message += "\nUV protection is not necessary at the moment."


    # Rest of the function remains the same

    # Set up Gmail API credentials
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/credentials.json', ['https://www.googleapis.com/auth/gmail.send'])

            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    try:
        service = build('gmail', 'v1', credentials=creds)

        message = MIMEText(message)
        message['to'] = email
        message['subject'] = subject
        create_message = {'raw': base64.urlsafe_b64encode(
            message.as_bytes()).decode()}
        send_message = service.users().messages().send(
            userId="me", body=create_message).execute()

        print(
            f'sent message to {email} Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f'An error occurred: {error}')
        send_message = None
    return send_message


def main():
    root = tk.Tk()
    root.title("Weather App")

    city_label = ttk.Label(root, text="City:")
    city_label.grid(column=0, row=0)
    city_entry = ttk.Entry(root)
    city_entry.grid(column=1, row=0)

    email_label = ttk.Label(root, text="Email:")
    email_label.grid(column=0, row=1)
    email_entry = ttk.Entry(root)
    email_entry.grid(column=1, row=1)

    daily_update_var = tk.BooleanVar()
    daily_update_check = ttk.Checkbutton(
        root, text="Daily Weather Updates", variable=daily_update_var)
    daily_update_check.grid(column=0, row=2)

    submit_button = ttk.Button(root, text="Submit", command=lambda: submit_weather_data(
        city_entry, email_entry, daily_update_var))
    submit_button.grid(column=1, row=2)

    root.mainloop()


def submit_weather_data(city_entry, email_entry, daily_update_var):
    city = city_entry.get()
    email = email_entry.get()
    daily_update = daily_update_var.get()

    weather_data = get_weather_data(city)
    if weather_data:
        wind = weather_data[4]
        pressure = weather_data[5]
        uv = weather_data[6]
        is_umbrella_required = weather_data[7]
        send_email(weather_data[0], weather_data[1], weather_data[2], weather_data[3], wind, pressure,uv, email , is_umbrella_required)

        tk.messagebox.showinfo(
            "Weather Update", f"Weather data sent to {email}")
    else:
        tk.messagebox.showerror("Error", "City not found")


if __name__ == "__main__":
    main()


