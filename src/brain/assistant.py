import os
import whisper
from gtts import gTTS
import numpy as np
import wave
import requests
import json
import re
from user_info import MY_INFO
from datetime import datetime, date
from config import ROBOT_NAME, SYSTEM_PROMPT

class AIAssistant:
    def __init__(self):
        self.robot_name = ROBOT_NAME
        self.system_prompt = SYSTEM_PROMPT
        self.local_url = "http://127.0.0.1:1234/v1/chat/completions"
        self.conversation_history = []
        self.max_history = 6
        print("🧠 Loading Whisper model 'tiny.en'...")
        self.whisper_model = whisper.load_model("tiny.en")

    def transcribe(self, audio_path):
        if not audio_path or not os.path.exists(audio_path):
            return None
        print("🧠 [AI] Transcribing...")
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                n_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                n_frames = wav_file.getnframes()
                audio_data = wav_file.readframes(n_frames)
                if sample_width == 2:
                    audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                elif sample_width == 4:
                    audio = np.frombuffer(audio_data, dtype=np.int32).astype(np.float32) / 2147483648.0
                else:
                    audio = np.frombuffer(audio_data, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0
                if n_channels == 2:
                    audio = audio[::2]
        except Exception as e:
            print(f"❌ Error reading WAV: {e}")
            return None
        result = self.whisper_model.transcribe(audio, fp16=False, language='en')
        text = result["text"].strip()
        print(f"🗣️ Human: '{text}'")
        return text

    def _calculate_birthday_info(self, user_text):
        """Рассчитывает информацию о дне рождения"""
        user_lower = user_text.lower()
        birthday_str = MY_INFO.get('birthday', '')
        age = MY_INFO.get('age', 0)
        if not birthday_str:
            return None
        try:
            for fmt in ["%B %d, %Y", "%d %B %Y", "%Y-%m-%d"]:
                try:
                    bday = datetime.strptime(birthday_str, fmt).date()
                    break
                except:
                    continue
            else:
                return None
        except:
            return None
        today = date.today()
        next_bday = date(today.year, bday.month, bday.day)
        if next_bday < today:
            next_bday = date(today.year + 1, bday.month, bday.day)
        days_until = (next_bday - today).days
        future_age = next_bday.year - bday.year
        if "how many days" in user_lower and "birthday" in user_lower:
            if days_until == 0:
                return "Today is your birthday! Happy birthday! 🎉"
            elif days_until == 1:
                return "Your birthday is tomorrow!"
            else:
                return f"Your next birthday is in {days_until} days, on {next_bday.strftime('%B %d')}."
        age_match = re.search(r'when will i be (\d+)', user_lower)
        if age_match:
            target_age = int(age_match.group(1))
            target_year = bday.year + target_age
            target_date = date(target_year, bday.month, bday.day)

            if target_date < today:
                return f"You already turned {target_age} on {target_date.strftime('%B %d, %Y')}."

            days_to_target = (target_date - today).days
            years_to_target = target_date.year - today.year
            months_to_target = target_date.month - today.month
            if months_to_target < 0:
                years_to_target -= 1
                months_to_target += 12

            return f"You will turn {target_age} on {target_date.strftime('%B %d, %Y')}, which is in {days_to_target} days (about {years_to_target} years and {months_to_target} months)."

        year_match = re.search(r'how old will i be in (\d+) years?', user_lower)
        if year_match:
            years_ahead = int(year_match.group(1))
            future_year = today.year + years_ahead
            # Проверяем, прошёл ли уже день рождения в этом году
            this_year_bday = date(today.year, bday.month, bday.day)
            if today >= this_year_bday:
                future_age = age + years_ahead
            else:
                future_age = age + years_ahead
            return f"In {years_ahead} years, you will be {future_age} years old."

        return None
    def _get_weather(self, city="Moscow"):
        try:
            API_KEY = "b64bfa614f121b4dac226d1f350b4ab8"
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": API_KEY,
                "units": "metric",
                "lang": "en"
            }
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                temp = data["main"]["temp"]
                desc = data["weather"][0]["description"]
                return f"In {city}, it's {temp:.0f}°C and {desc}."
        except Exception as e:
            print(f"Weather error: {e}")
        return None
    def _extract_city(self, text):
        """Извлекает город из текста"""
        text_lower = text.lower()
        patterns = [
            r"weather (?:in|at) ([a-z\s\-']+?)(?:\?|$|\.|,)",
            r"(?:in|at) ([a-z\s\-']+?)(?:\?|$|\.|,).*weather",
            r"what(?:'s| is) the weather (?:in|at) ([a-z\s\-']+?)(?:\?|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                city = match.group(1).strip()
                return " ".join(word.capitalize() for word in city.split())

        return None

    def generate_response(self, user_text):
        if not user_text:
            return "I didn't catch that."
        user_lower = user_text.lower()

        birthday_calc = self._calculate_birthday_info(user_text)
        if birthday_calc:
            return birthday_calc
        if "weather" in user_lower:
            city = self._extract_city(user_text)
            if not city:
                return "Which city would you like the weather for?"
            weather = self._get_weather(city)
            if weather:
                return weather
            else:
                return f"Sorry, I couldn't get the weather for {city}."

        if "my name" in user_lower or "who am i" in user_lower:
            return f"Your name is {MY_INFO['name']}."
        if "my birthday" in user_lower:
            return f"Your birthday is {MY_INFO['birthday']}."
        if "my age" in user_lower or "how old am i" in user_lower:
            return f"You are {MY_INFO['age']} years old."
        if "profession" in user_lower or "career" in user_lower:
            return f"You are {MY_INFO.get('profession', 'a developer')}."

        if "my schedule" in user_lower or "plan" in user_lower or "my classes" in user_lower:
            today = datetime.now().strftime("%A").lower()
            schedule = MY_INFO['schedule'].get(today, "No classes today!")
            return f"Today ({today}) you have: {schedule}"

        if "my dreams" in user_lower:
            dreams = ", ".join(MY_INFO['dreams'][:3])
            return f"Your dreams include: {dreams}."

        if "what do i study" in user_lower or "my specialty" in user_lower:
            return f"You study {MY_INFO['specialty']} at {MY_INFO['university']}."

        if "make a note" in user_lower or "recall me" in user_lower or "dont' forget" in user_lower or "should remember" in user_lower:
            output_file = '../to_not_to_forget/have_to_remember.txt'
            user_text.to_txt(output_file, index=False)
            print(" Information was written in txt")
            #сделать переход строк для txt файла
            # теперь json:
            print("Can I ask few questions?") # как сделать считывание по каждому вопросу?
            print("What date is it?")
            date=int(user_text) #уточнить дату
# ДОБАВИТЬ ВОЗМОЖНОСТЬ ОБЩАТЬСЯ ПЕРЕПИСЫВАЯСЬ!!!!!
# ДОП ИДЕЯ: СДЕЛАТЬ ПАРСИНГ ДАННЫХ (ТИПО КОЛВО ЗАДАЧ С ЛИТКОДА)
# ЕЩЕ ДОП ИДЕЯ: ДОДЕЛАТЬ ФАЙЛ gpa_for_now.json
# Доделать прослушивание и добавление доп музыки
# 🍓🥥🌸🍁🍂
            notes={
                "text": len(user_text),
                "date": int(user_text),
                "importance": int(importance),
            }
            with open('../to_not_to_forget/have_to_remember.json', 'w', encoding='utf-8') as f:
                json.dump(notes, f, indent=2, ensure_ascii=False)
            return "I will not forget about it"




        if "clear history" in user_lower or "forget everything" in user_lower:
            self.conversation_history = []
            print("🧹 History cleared!")
            return "Memory cleared. What would you like to talk about?"

        if "what time" in user_lower or "current time" in user_lower:
            now = datetime.now()
            return f"It's {now.strftime('%H:%M')}."

        if "what day" in user_lower or "today's date" in user_lower:
            now = datetime.now()
            return f"Today is {now.strftime('%A, %B %d, %Y')}."


        print("🧠 [AI] Thinking...")

        try:
            messages = []
            system_prompt = f"You are {self.robot_name}, a tiny helpful robot. Answer in 1-3 sentences. Be friendly and conversational. Remember the context of our conversation."

            if not self.conversation_history:
                prompt = f"{system_prompt}\n\nUser: {user_text}\nAssistant:"
                messages = [{"role": "user", "content": prompt}]
            else:
                conversation_text = system_prompt + "\n\n"
                for entry in self.conversation_history:
                    conversation_text += f"{entry['role'].capitalize()}: {entry['content']}\n"
                conversation_text += f"User: {user_text}\nAssistant:"
                messages = [{"role": "user", "content": conversation_text}]

            payload = {
                "model": "local-model",
                "messages": messages,
                "max_tokens": 100,
                "temperature": 0.7
            }

            resp = requests.post(self.local_url, json=payload, timeout=20)

            if resp.status_code == 200:
                data = resp.json()
                answer = data["choices"][0]["message"]["content"].strip()

                if answer:
                    print(f"🤖 {self.robot_name}: '{answer}'")
                    self.conversation_history.append({"role": "user", "content": user_text})
                    self.conversation_history.append({"role": "assistant", "content": answer})
                    if len(self.conversation_history) > self.max_history:
                        self.conversation_history = self.conversation_history[-self.max_history:]
                    return answer

        except Exception as e:
            print(f"⚠️ LLM error: {type(e).__name__} - {e}")

        return self._fallback_response(user_text)

    def _fallback_response(self, user_text):
        """Запасной ответ без LLM"""
        user_lower = user_text.lower()

        if "hello" in user_lower or "hi" in user_lower:
            return "Hello! How can I help you?"
        elif "how are you" in user_lower:
            return "I'm doing great, thank you!"
        elif "your name" in user_lower:
            return f"I'm {self.robot_name}!"
        else:
            return f"I heard: '{user_text}'. Tell me more!"

    def synthesize_speech(self, text):
        print("🧠 [AI] Generating voice...")
        os.makedirs("sounds", exist_ok=True)
        import time
        filename = f"sounds/response_{int(time.time() * 1000)}.mp3"
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filename)
        return filename

    def process_audio(self, audio_path):
        text = self.transcribe(audio_path)
        if text:
            response_text = self.generate_response(text)
            if response_text:
                audio_response = self.synthesize_speech(response_text)
                return audio_response
        return None