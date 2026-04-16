# src/brain/assistant.py
import os
import whisper
from gtts import gTTS
import numpy as np
import wave
import requests


class AIAssistant:
    def __init__(self, robot_name="Jarvis Mini"):
        self.robot_name = robot_name

        # Настройка Gemini
        try:
            import google.generativeai as genai
            genai.configure(api_key="AQ.Ab8RN6I3m6nR18200OQWAjj5bzPgLVIDfdR_Rakxyfm4EseQMA")
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            self.has_gemini = True
            print("✅ Gemini API configured")
        except Exception as e:
            print(f"⚠️ Gemini not available: {e}")
            self.has_gemini = False

        # Локальный fallback (LM Studio)
        self.local_url = "http://127.0.0.1:1234/v1/chat/completions"

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

    def _try_gemini(self, user_text):
        if not self.has_gemini:
            return None
        try:
            import google.generativeai as genai

            # Пробуем несколько имён моделей
            for model_name in ['gemini-1.5-flash', 'gemini-pro', 'gemini-2.0-flash-exp']:
                try:
                    model = genai.GenerativeModel(model_name)
                    prompt = f"You are {self.robot_name}, a tiny robot. Answer in 1 short sentence. English only.\n\nUser: {user_text}\nAssistant:"
                    response = model.generate_content(prompt)
                    answer = response.text.strip()
                    if answer:
                        return answer
                except:
                    continue

        except Exception as e:
            print(f"⚠️ Gemini failed: {type(e).__name__}")
        return None

    def _try_local_llm(self, user_text):
        """Попытка использовать локальную LM Studio"""
        try:
            payload = {
                "messages": [
                    {"role": "user",
                     "content": f"Answer in one short sentence. Be direct. Do not show your thinking process.\n\nUser: {user_text}\nAnswer:"}
                ],
                "max_tokens": 80,
                "temperature": 0.7
            }
            resp = requests.post("http://127.0.0.1:1234/v1/chat/completions", json=payload, timeout=30)

            if resp.status_code == 200:
                data = resp.json()
                msg = data["choices"][0]["message"]
                raw = msg.get("content", "") or msg.get("reasoning_content", "")

                # 🔥 ВЫТАСКИВАЕМ ТОЛЬКО ОТВЕТ
                if "Thinking Process:" in raw:
                    # Ищем строку, которая не является частью размышлений
                    lines = raw.split('\n')
                    for line in lines:
                        line = line.strip()
                        # Пропускаем шаги мышления
                        if line and not line[
                            0].isdigit() and "Thinking" not in line and "Analyze" not in line and "Persona" not in line:
                            # Это похоже на реальный ответ
                            if len(line) > 3 and line[0].isalpha():
                                return line
                    # Если не нашли — берём последнюю строку
                    return lines[-1].strip() if lines[-1].strip() else "Hello! How can I help?"

                return raw.strip() if raw else "Hello! How can I help?"

        except Exception as e:
            print(f"⚠️ Local LLM error: {type(e).__name__}")


    def generate_response(self, user_text):
        """Гибридный генератор ответа"""
        if not user_text:
            return "I didn't catch that."

        print("🧠 [AI] Generating response...")

        # 1. Пробуем Gemini (если есть интернет)
        answer = self._try_gemini(user_text)
        if answer:
            print(f"🤖 {self.robot_name} (Gemini): '{answer}'")
            return answer

        # 2. Fallback на локальную модель
        print("🔄 Falling back to local LLM...")
        answer = self._try_local_llm(user_text)
        if answer:
            print(f"🤖 {self.robot_name} (Local): '{answer}'")
            return answer

        # 3. Совсем ничего не работает
        return "Hello! I'm here and ready to help."

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