import os
import whisper
from gtts import gTTS
import numpy as np
import wave
import requests
import datetime


class AIAssistant:
    def __init__(self, robot_name="Jarvis Mini"):
        self.robot_name = robot_name
        self.local_url = "http://127.0.0.1:1234/v1/chat/completions"

        # 🔥 ИСТОРИЯ ДИАЛОГА (максимум 4 сообщения = 2 вопроса-ответа)
        self.conversation_history = []
        self.max_history = 4

        print("🧠 Loading Whisper model 'tiny.en'...")
        self.whisper_model = whisper.load_model("tiny.en")

    def transcribe(self, audio_path):
        # ... БЕЗ ИЗМЕНЕНИЙ (ваш рабочий код) ...
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

        # 🔥 СПЕЦИАЛЬНЫЕ КОМАНДЫ
        user_lower = user_text.lower()

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
            # 🔥 СОБИРАЕМ СООБЩЕНИЯ С ИСТОРИЕЙ
            messages = []

            # Системная инструкция
            system_prompt = f"You are {self.robot_name}, a tiny helpful robot. Answer in 1-3 sentences. Be friendly and conversational. Remember the context of our conversation."

            # Если история пустая — просто инструкция + вопрос
            if not self.conversation_history:
                prompt = f"{system_prompt}\n\nUser: {user_text}\nAssistant:"
                messages = [{"role": "user", "content": prompt}]
            else:
                # С историей — формируем диалог
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

                    # 🔥 СОХРАНЯЕМ В ИСТОРИЮ
                    self.conversation_history.append({"role": "user", "content": user_text})
                    self.conversation_history.append({"role": "assistant", "content": answer})

                    # Обрезаем историю если слишком длинная
                    if len(self.conversation_history) > self.max_history:
                        self.conversation_history = self.conversation_history[-self.max_history:]

                    return answer

        except Exception as e:
            print(f"⚠️ LLM error: {type(e).__name__} - {e}")
            # При ошибке пробуем без истории
            return self._fallback_response(user_text)

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