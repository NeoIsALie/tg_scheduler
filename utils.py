from datetime import datetime


def convert_to_mins(x):
    return 60 * int(x[:2]) + int(x[-2:])


def current_time():
    now = datetime.now()
    time_now = f"{now.hour:02}:{now.minute:02}"
    return time_now