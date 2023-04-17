import os
import sys
import re
from datetime import datetime, date
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import rumps
import openai
from pathlib import Path
from watchdog.events import LoggingEventHandler


import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_openai_api_key():
    api_key_file = os.path.expanduser('~/.ai.key')
    with open(api_key_file, 'r') as f:
        return f.read().strip()

openai.api_key = load_openai_api_key()

class CommandHistory:
    def __init__(self, timestamp, duration, command, description, short_description):
        self.timestamp = timestamp
        self.duration = duration
        self.command = command
        self.description = description
        self.short_description = short_description

    def __str__(self):
        return (f"# {self.short_description}\n\n"
                f"```zsh\n"
                f"{self.command}\n"
                f"```\n\n"
                f"* *Executed on:* {self.timestamp} ({self.duration}s):\n\n"
                f"## Description:\n"
                f"* {self.description}")


def generate_descriptions(command):
    prompt = f"Write a step by step description of this zsh command line input is doing as if explaining it to another developer: {command} \n"


    print(command)

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.5,
    )

    description = response.choices[0].text.strip()

    prompt = f"Write a one sentence description of this command line: {command} \n"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=30,
        n=1,
        stop=None,
        temperature=0.5,
    )

    short_description = response.choices[0].text.strip()

    return description, short_description

class ZshHistoryHandler(PatternMatchingEventHandler):
    def __init__(self, home_dir, file_path):
        super().__init__(patterns=['*.zsh_history'], ignore_directories=True, case_sensitive=False)
        self.file_path = file_path
        self.file_position = os.path.getsize(file_path)
        self.output_file = self.get_daily_output_file()
        logging.info(f"init  file path {self.file_path}")

    def get_daily_output_file(self):
        today = date.today().strftime("%m-%d-%Y")
        output_file = os.path.expanduser(f"~/.history/data/zsh_history_{today}.md")
        if not os.path.exists(output_file):
            self.archive_old_output_files()
        return output_file

    def archive_old_output_files(self):
        for file in Path(os.path.expanduser('~/.history/data')).glob("zhistory_*.md"):
            file_date_str = file.stem.split('_')[1]
            if file_date_str != date.today().strftime("%m-%d-%Y"):
                os.rename(file, os.path.expanduser(f"~/.history/history/zsh_history_{file_date_str}"))

    def on_modified(self, event):
        logging.info(f"on_modified called: {event.src_path}")
        with open(self.file_path, 'r') as f:
            f.seek(self.file_position)
            new_data = f.read()
            self.file_position = f.tell()
            logging.info(f"on_modified file position: {self.file_position}")
            logging.info(f"on_modified new data: {new_data}")

        for line in new_data.strip().split('\n'):
            if line.startswith(':'):
                logging.info(f"line starts with colon")

                fields = line.split(':', 2)  # Split on the first two colons
                fields = [x for x in fields if x and x.strip()]
                logging.info(f"fields {fields} length {len(fields)}")




                if len(fields) >= 2:
                    timestamp = fields[0].strip()
                    command = fields[1].split(';', 1)[1].strip()  # Split on the first semicolon and take the second part
                    duration = fields[1].split(';', 1)[0].strip()

                    timestamp = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                    description, short_description = generate_descriptions(command)
                    cmd_history = CommandHistory(timestamp, duration, command, description, short_description)
                    logging.info(f"New command history entry: {cmd_history}")
                    with open(self.output_file, 'a') as f:
                        f.write(str(cmd_history) + "\n\n")
                        f.flush()



class ZshHistoryTailApp(rumps.App):
    def __init__(self):
        super(ZshHistoryTailApp, self).__init__("Zsh History Tail")
        self.menu = ["Preferences", "Silly button", "Say hi"]

    @rumps.clicked("Preferences")
    def prefs(self, _):
        rumps.alert("jk! no preferences available!")

    @rumps.clicked("Silly button")
    def onoff(self, sender):
        sender.state = not sender.state

    @rumps.clicked("Say hi")
    def sayhi(self, _):
        rumps.notification("Awesome title", "amazing subtitle", "hi!!1")


def main():


    zsh_history_file = os.path.expanduser('~/.history/history/.zsh_history')
    home_dir = os.path.expanduser('~/.history/history/')

    event_handler = ZshHistoryHandler(home_dir, zsh_history_file)
    logging_event_handler = LoggingEventHandler()

    if not os.path.isfile(zsh_history_file):
        print(f"Error: {zsh_history_file} does not exist")
        sys.exit(1)

    observer = Observer()
    observer.schedule(event_handler, path=home_dir, recursive=False)
    observer.schedule(logging_event_handler, path=home_dir, recursive=False)
    observer.start()

    logging.debug("Observer started")

    try:
        app = ZshHistoryTailApp()
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()
