#! python3
import datetime
import functools
import hashlib
import os
import time

import model
import utils.log
import utils.telegram

LINK_KEY = os.environ["LINK_KEY"]
MY_ID = utils.telegram.MY_ID
BOT_ID = utils.telegram.BOT_ID
URL = f"https://{utils.telegram.APPNAME}.herokuapp.com/"
TELEGRAM_HELP = """Help:
    `.register username password role`: Use role 0 to delete
    `.gettoken path`

    `.sleep HH:MM [dd[/mm[/yyyy]]]`: Use 99:99 to delete
    `.awake HH:MM [dd[/mm[/yyyy]]]`: Use 99:99 to set to 0

    `.out HH:MM [dd[/mm[/yyyy]]]`: Use 99:99 to delete
    `.home HH:MM [dd[/mm[/yyyy]]]`: Use 99:99 to set to 0

    `.birthday NAME dd/mm`: Write 'delete' as name to delete
    `.period NAME COLOR WEEKEND dd/mm/yyyy [dd/mm/yyyy]`: ^ 'delete' as name

    Use the alias 'yesterday' and 'preyesterday'
"""
DAY = datetime.timedelta(days=1)
TODAY = datetime.datetime.today()  # Only used as a placeholder

logger = utils.log.get("handle")
bot = utils.telegram.Bot()


def report(s):
    try:
        bot.report(s)
    except Exception as e:
        logger.exception(e)


@functools.lru_cache(maxsize=None)
def generate_link_token(path):
    return hashlib.sha512((LINK_KEY + path.lstrip("/")).encode()).hexdigest()


def hash_password(password):
    return hashlib.sha512(password.encode()).hexdigest()


def pregenerate_calendar(weeks):
    kw = {"iDay_": time.strftime("%d/%m/%Y"),
          "weeks_": weeks, "smoothFactor_": 205}
    birthdays = []
    for bday in model.Birthday.select():
        month, day = divmod(bday.date, 100)
        birthdays.append(f"{day}/{month}-{bday.text}")
    kw["birthdays_"] = tuple(birthdays)
    periods = []
    for period in model.Period.select():
        color = period.text[:3]
        weekend = period.text[3:6]
        name = period.text[6:]
        periods.append({
            "iDay": period.idate.strftime("%d/%m/%Y"),
            "fDay": period.fdate.strftime("%d/%m/%Y"),
            "name": name,
            "color": color,
            "weekend": weekend
        })
    kw["periods_"] = tuple(periods)
    return kw


def pregenerate_sleep(weeks):
    data = [(sleep.date.toordinal() - 1, sleep.amount)
            for sleep in model.Sleep.select()]
    return {"weeks_": weeks, "data_": tuple(data)}


def pregenerate_out(weeks):
    data = [(out.date.toordinal() - 1, out.amount)
            for out in model.Out.select()]
    return {"weeks_": weeks, "data_": tuple(data)}


def handle_register(cmd, username, password, role):
    """
    `.register username password role`: Use role 0 to delete the entry
    """
    user, created = model.User.get_or_create(
        username=username,
        defaults={
            "password": "",
            "role": 0
        }
    )
    if role != "0":
        user.password = hash_password(password)
        user.role = role
        user.save()
        report(f"User created ({username})")
    else:
        user.delete_instance()
        report(f"User deleted ({username})")


def handle_gettoken(cmd, path):
    """
    `.gettoken path`
    """
    token = generate_link_token(path.split("?")[0])
    sep = "&" if "?" in path else "?"
    report(f"{URL}{path.lstrip('/')}{sep}token={token}")


def handle_birthday(cmd, name, date_str):
    """
    `.birthday NAME dd/mm`: Write 'delete' as name to delete
    """
    day, month = date_str.split("/")
    date = int(day) + int(month) * 100

    bday, created = model.Birthday.get_or_create(
        date=date,
        defaults={"text": ""}
    )
    if name == "delete":
        bday.delete_instance()
        report(f"Birthday deleted ({date_str})")
    else:
        bday.text = name
        bday.save()
        report(f"Birthday set ({name} {date_str})")


def handle_period(cmd, name, color, weekend, idate_str, *args):
    """
    `.period NAME COLOR WEEKEND dd/mm/yyyy [dd/mm/yyyy]`: ^ 'delete' as name
    """
    idate = datetime.date(*map(int, idate_str.split("/")[::-1]))
    if idate.year < 1000:
        idate = idate.replace(year=idate.year + 2000)
    fdate_str = args[0] if args else idate_str  # Final date
    fdate = datetime.date(*map(int, fdate_str.split("/")[::-1]))
    if fdate.year < 1000:
        fdate = fdate.replace(year=fdate.year + 2000)

    period, created = model.Period.get_or_create(
        idate=idate,
        fdate=fdate,
        defaults={"text": ""}
    )
    if name == "delete":
        period.delete_instance()
        report(f"Period deleted ({period.text} {idate_str}-{fdate_str})")
    else:
        period.text = name
        period.save()
        report(f"Birthday set ({name} {idate_str}-{fdate_str})")


def handle_sleep_and_out(cmd_unstripped, hour_str, *args):
    """
    `.sleep HH:MM [dd[/mm[/yyyy]]]`: Use 99:99 to delete
    `.awake HH:MM [dd[/mm[/yyyy]]]`: Use 99:99 to set to 0

    `.out HH:MM [dd[/mm[/yyyy]]]`: Use 99:99 to delete
    `.home HH:MM [dd[/mm[/yyyy]]]`: Use 99:99 to set to 0
    """
    cmd = cmd_unstripped[1:]
    cmd_table = {
        "sleep": "sleep", "awake": "sleep",
        "out": "out", "home": "out"
    }
    try:
        hour, minute = map(int, hour_str.replace(".", ":").split(":"))
    except ValueError as ex:
        hour = int(hour_str)
        minute = 0
        logger.exception(ex)

    date = datetime.datetime.today()
    try:
        date = date.replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
    except ValueError as ex:
        logger.exception(ex)

    date_str = args[0] if args else ""
    if date_str == "today" or not date_str:
        pass
    elif date_str == "yesterday":
        date -= DAY
    elif date_str == "preyesterday":
        date -= DAY * 2
    else:
        date_split = map(int, date_str.split("/"))
        kw = dict(((i, j) for i, j in
                   zip(("day", "month", "year"), date_split)))
        logger.debug(kw)
        date = date.replace(**kw)  # y/m/d
        if date.year < 1000:
            date = date.replace(year=date.year + 2000)

    instance, created = model.State.get_or_create(
        name=cmd_table[cmd],
        defaults={"date": TODAY, "state": "null"}
    )
    backup, created = model.State.get_or_create(
        name="back" + cmd_table[cmd],
        defaults={"date": TODAY, "state": "null"}
    )
    if hour > 23 or minute > 59:  # "Delete"
        instance.date = backup.date
        instance.state = backup.state
        instance.save()
        report(f"'Deleted' {cmd} ({date})")
        if cmd == "awake" or cmd == "home":
            correct_model = model.Sleep if cmd == "awake" else model.Out
            subinst, created = correct_model.get_or_create(
                date=date,
                defaults={"amount": 0}
            )
            subinst.amount = 0
            subinst.save()
            report(f"Set to 0 {cmd} ({date})")
        return
    # Create backup
    backup.date = instance.date
    backup.state = instance.state
    backup.save()
    if cmd == "sleep" or cmd == "out":
        # Start
        instance.date = date
        instance.state = "start"
        instance.save()
        report(f"Started {cmd} ({date})")
    elif cmd == "awake" or cmd == "home":
        if instance.state != "start":
            report(f"Doing nothing about {cmd} ({instance.state})")
            return
        idate = instance.date
        delta = date - idate
        # Stop
        instance.date = date
        instance.state = "stop"
        instance.save()
        report(f"Stopped {cmd} ({date})")
        add_amount(cmd_table[cmd], delta, date)


def add_amount(cmd, delta, date):
    # TODO: Add to google
    amount = int(delta.total_seconds()) // 60  # Minutes
    if amount < 10:
        report(f"Amount was so little I ignored it {cmd} ({amount})")
        return

    final_amount = int(amount / 60 * 10)  # Amount added to database
    correct_model = model.Sleep if cmd == "sleep" else model.Out
    instance, created = correct_model.get_or_create(
        date=date,
        defaults={"amount": 0}
    )
    instance.amount += final_amount
    instance.save()
    report(f"Added amount {cmd} ({amount}->{final_amount} {date})")


def ifttt(data):
    handle_sleep_and_out(data["cmd"], "-1:-1")


HANDLE_COMMAND = {
    "register": handle_register,
    "gettoken": handle_gettoken,
    "birthday": handle_birthday,
    "period": handle_period,
    "sleep": handle_sleep_and_out,
    "awake": handle_sleep_and_out,
    "out": handle_sleep_and_out,
    "home": handle_sleep_and_out
}


def handle(data):
    try:
        message = data["message"]
    except KeyError:  # Message has been edited
        message = data["edited_message"]

    chat_id = message["chat"]["id"]
    if chat_id != MY_ID:
        bot.forward_message(MY_ID, chat_id, message["message_id"])
        bot.forward_message(chat_id, MY_ID, 1856)  # MSG: I do not reply
        return

    text = message.get("text", "")
    try:
        rmessage = message["reply_to_message"]
    except KeyError:
        pass  # It is not a reply
    else:
        try:
            rfrom = rmessage["forward_from"]["id"]
        except KeyError:
            rfrom = BOT_ID
        if rfrom == MY_ID:  # Forward message to person being replied to
            bot.forward_message(rfrom, MY_ID, message["message_id"])
            report(f"Message forwarded to {rfrom}")
            return

    if not text.startswith((".", "-")):
        bot.send_message(MY_ID, "commands start with . or -",
                         reply_to_message_id=message["message_id"])
        return

    command = text[1:].split(" ", 1)[0]  # from first char to first space
    if command == "help":
        report(TELEGRAM_HELP)
        return

    try:
        HANDLE_COMMAND[command](*text.split(" "))
    except ValueError:
        report("Check out `.help`, you are probably missing the right params")
    except KeyError:
        report(f"Unrecognized command '{text}'")
