import time
import threading
import os

class MockRobot:
    """
    Эмуляция будущего ESP32 робота.
    Позволяет отлаживать логику ИИ без паяльника.
    """
    def __init__(self):
        try:
            import pygame
            pygame.mixer.init()
        except:
            print("⚠️ Pygame not installed. Audio playback may not work.")
        self.is_speaking = False
        print("🤖 Mock Robot initialized. I'm ready for conversation!")

    def think_animation(self):
        """Робот показывает, что он думает"""
        def spin():
            print("💭 [ROBOT] Thinking...")
            time.sleep(1.5)
            print("💡 [ROBOT] Got it!")
        thread = threading.Thread(target=spin)
        thread.start()
        return thread

    def listen_for_speech(self, duration=4):
        """Запись речи с микрофона ноутбука"""
        print(f"🎤 [ROBOT] Listening for {duration} seconds... Speak now!")

        try:
            import pyaudio
            import wave

            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000

            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

            frames = []
            for _ in range(0, int(RATE / CHUNK * duration)):
                data = stream.read(CHUNK)
                frames.append(data)

            stream.stop_stream()
            stream.close()
            p.terminate()

            # Сохраняем в папку sounds
            os.makedirs("sounds", exist_ok=True)
            filepath = "sounds/last_recording.wav"
            wf = wave.open(filepath, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()

            print(f"✅ [ROBOT] Recording saved to {filepath}")
            return filepath

        except Exception as e:
            print(f"❌ [ROBOT] Recording failed: {e}")
            return None

    # src/hardware_mock/mock_robot.py — в метод speak_response
    def speak_response(self, audio_filepath):
        if not audio_filepath or not os.path.exists(audio_filepath):
            print("❌ [ROBOT] Audio file not found!")
            return

        print(f"🔊 [ROBOT] Speaking...")
        try:
            import pygame
            pygame.mixer.music.load(audio_filepath)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()  # Важно: выгрузить файл
        except:
            os.system(f'start {audio_filepath}')
            time.sleep(3)

        # Удаляем временный файл
        try:
            os.remove(audio_filepath)
        except:
            pass

        print("🤖 [ROBOT] Done speaking.")