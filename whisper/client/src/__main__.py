import subprocess
import os
import keyboard
import requests
import time
import pyperclip
import wave
import contextlib
from dataclasses import dataclass
from typing import Optional


@dataclass
class RecordingConfig:
    """Configuration for audio recording."""

    output_file: str = "output.wav"
    min_duration: float = 1.0
    ffmpeg_command: list[str] = None
    server_url: str = "http://localhost:8000/transcribe/"

    def __post_init__(self):
        self.ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-f",
            "alsa",
            "-i",
            "plughw:0,0",
            self.output_file,
        ]


class AudioRecorder:
    """Handles audio recording, processing, and transcription."""

    def __init__(self, config: RecordingConfig):
        self.config = config
        self.recording_process = None
        self.is_recording = False
        self.is_sending = False
        self.start_time = 0

    def start_recording(self) -> None:
        """Starts audio recording if not already recording or sending."""
        if self.is_recording or self.is_sending:
            return

        try:
            self.recording_process = subprocess.Popen(
                self.config.ffmpeg_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.is_recording = True
            self.start_time = time.time()
            print("Recording started...")
        except Exception as e:
            print(f"Failed to start recording: {e}")
            self.is_recording = False

    def stop_recording(self) -> None:
        """Stops recording and processes the audio if duration is sufficient."""
        if not self.is_recording or not self.recording_process:
            return

        try:
            self.recording_process.terminate()
            self.recording_process.wait()
            self.is_recording = False
            print("Recording stopped.")

            duration = self._get_recording_duration()
            print(f"Duration: {duration:.2f}s")

            if duration and duration >= self.config.min_duration:
                self._send_recording()
            else:
                print(
                    f"Recording too short (<{self.config.min_duration}s), cancelling send."
                )
                self._cleanup()
        except Exception as e:
            print(f"Error stopping recording: {e}")
            self._cleanup()

    def _get_recording_duration(self) -> Optional[float]:
        """Returns the duration of the recorded audio file."""
        try:
            with contextlib.closing(
                wave.open(self.config.output_file, "r")
            ) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                return frames / float(rate)
        except Exception as e:
            print(f"Error reading audio duration: {e}")
            return None

    def _send_recording(self) -> None:
        """Sends the recorded audio to the transcription server."""
        self.is_sending = True
        try:
            with open(self.config.output_file, "rb") as f:
                response = requests.post(
                    self.config.server_url, files={"file": f}
                )
                response.raise_for_status()

            data = response.json()
            transcribed_text = data.get("text", "No text returned")
            print(f"Server response: {transcribed_text}")

            self._handle_clipboard(transcribed_text)
        except requests.RequestException as e:
            print(f"Failed to send recording. Error: {e}")
        except Exception as e:
            print(f"Unexpected error sending recording: {e}")
        finally:
            self._cleanup()
            self.is_sending = False

    def _handle_clipboard(self, text: str) -> None:
        """Handles clipboard operations for pasting transcribed text."""
        try:
            original_clipboard = pyperclip.paste()
        except Exception as e:
            print(f"Error reading clipboard: {e}")
            original_clipboard = ""

        try:
            pyperclip.copy(text)
            keyboard.send("ctrl+shift+v")
            if original_clipboard:
                pyperclip.copy(original_clipboard)
        except Exception as e:
            print(f"Error handling clipboard: {e}")

    def _cleanup(self) -> None:
        """Removes the temporary audio file if it exists."""
        if os.path.exists(self.config.output_file):
            try:
                os.remove(self.config.output_file)
            except Exception as e:
                print(f"Error cleaning up file: {e}")

    def run(self) -> None:
        """Main loop to handle keyboard events."""
        print(
            "Press and hold F1 to record, release to stop and send. Press Ctrl+Shift+Esc to exit."
        )
        keyboard.on_press_key("F1", lambda _: self.start_recording())
        keyboard.on_release_key("F1", lambda _: self.stop_recording())

        try:
            keyboard.wait("ctrl+shift+esc")
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self._cleanup()
            keyboard.unhook_all()


def main():
    config = RecordingConfig()
    recorder = AudioRecorder(config)
    recorder.run()


if __name__ == "__main__":
    main()
