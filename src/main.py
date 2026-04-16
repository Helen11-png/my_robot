import sys
import os

# Добавляем родительскую папку в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brain.assistant import AIAssistant
from hardware_mock.mock_robot import MockRobot

def main():
    print("=" * 40)
    print("🤖 JARVIS MINI - Mock Mode (No ESP32)")
    print("=" * 40)

    robot = MockRobot()
    ai = AIAssistant()

    print("\nCommands: press ENTER to talk, type 'exit' to quit.")

    while True:
        cmd = input("\n>> Press ENTER to talk to robot or type 'exit': ")
        if cmd.lower() == 'exit':
            break

        think_thread = robot.think_animation()
        audio_file = robot.listen_for_speech(duration=4)
        think_thread.join()

        if audio_file:
            response_audio = ai.process_audio(audio_file)
            if response_audio:
                robot.speak_response(response_audio)
            else:
                print("🤖 [ROBOT] I have nothing to say...")
        else:
            print("🤖 [ROBOT] I didn't hear anything...")

if __name__ == "__main__":
    main()