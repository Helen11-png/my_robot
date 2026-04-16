import os
import whisper
from gtts import gTTS
from openai import OpenAI
import numpy as np
import wave


class AIAssistant:
    def __init__(self, robot_name="Jarvis Mini"):
        self.robot_name = robot_name

        self.client = OpenAI(
            base_url="http://localhost:1234/v1",
            api_key="not-needed"
        )

        print("🧠 Loading Whisper model 'tiny.en'... (first run downloads ~70MB)")
        self.whisper_model = whisper.load_model("tiny.en")

        self.messages = [
            {"role": "system",
             "content": f"You are {robot_name}, a tiny desktop robot. Keep answers under 15 words. Be helpful and slightly witty. Respond in English only."}
        ]

    def transcribe(self, audio_path):
        """Перевод аудио в текст БЕЗ ffmpeg"""
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

        self.messages.append({"role": "user", "content": user_text})

        if len(self.messages) > 6:
            self.messages = [self.messages[0]] + self.messages[-5:]

        try:
            print("🧠 [AI] Thinking with local LLM...")
            response = self.client.chat.completions.create(
                model="local-model",
                messages=self.messages,
                max_tokens=50,
                temperature=0.7
            )
            answer = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": answer})
            print(f"🤖 {self.robot_name}: '{answer}'")
            return answer
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return "Sorry, my brain is lagging."

    def synthesize_speech(self, text):
        print("🧠 [AI] Generating voice...")
        os.makedirs("sounds", exist_ok=True)
        tts = gTTS(text=text, lang='en', slow=False)
        filepath = "sounds/response.mp3"
        tts.save(filepath)
        return filepath

    def process_audio(self, audio_path):
        text = self.transcribe(audio_path)
        if text:
            response_text = self.generate_response(text)
            audio_response = self.synthesize_speech(response_text)
            return audio_response
        return None