# src/brain/assistant.py (ФИНАЛЬНАЯ РАБОЧАЯ ВЕРСИЯ)
import os
import whisper
from gtts import gTTS
import numpy as np
import wave
import requests


class AIAssistant:
    def __init__(self, robot_name="Jarvis Mini"):
        self.robot_name = robot_name
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

    def generate_response(self, user_text):
        if not user_text:
            return "I didn't catch that."

        print("🧠 [AI] Thinking...")

        try:
            # 🔥 MISTRAL В LM STUDIO НЕ ЛЮБИТ ROLE="SYSTEM"
            # Используем только user и assistant
            prompt = f"You are {self.robot_name}, a tiny helpful robot. Answer in 1-2 short sentences. Be friendly.\n\nUser: {user_text}\nAssistant:"

            payload = {
                "model": "local-model",  # 🔥 ОБЯЗАТЕЛЬНО для LM Studio
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 80,
                "temperature": 0.7
            }

            resp = requests.post(self.local_url, json=payload, timeout=20)

            print(f"🔍 DEBUG: Status = {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                answer = data["choices"][0]["message"]["content"].strip()

                print(f"🔍 DEBUG: Answer = '{answer}'")

                if answer:
                    print(f"🤖 {self.robot_name}: '{answer}'")
                    return answer
            else:
                # Покажем ошибку для диагностики
                print(f"🔍 DEBUG: Error response = {resp.text[:200]}")

        except Exception as e:
            print(f"⚠️ LLM error: {type(e).__name__} - {e}")


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