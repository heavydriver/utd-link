import re
from datetime import datetime, date


def validate_email(email: str):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)


def validate_password(password: str) -> bool:
    return len(password) >= 6


def validate_not_empty(*fields) -> bool:
    for f in fields:
        if len(f) == 0:
            return False

    return True


def validate_net_id(net_id: str) -> bool:
    return len(net_id) == 9 and net_id.isalnum()


def validate_role(role: str) -> bool:
    return role in ["student", "faculty"]


def validate_description(description: str) -> bool:
    return description != "<p><br></p>"


def validate_dates(start_date: str, end_date: str) -> bool:
    try:
        date_format = "%Y-%m-%d"
        s_date = datetime.strptime(start_date, date_format)
        e_date = datetime.strptime(end_date, date_format)

        if s_date.date() > e_date.date():
            return False
    except ValueError:
        return False

    return True


def validate_date(the_date: str) -> bool:
    try:
        date_format = "%Y-%m-%d"
        datetime.strptime(the_date, date_format)
    except ValueError:
        return False

    return True


def compare_date_with_today(the_date: str) -> bool:
    try:
        date_format = "%Y-%m-%d"
        t_date = datetime.strptime(the_date, date_format).date()

        if t_date < date.today():
            return False

    except ValueError:
        return False

    return True


def validate_start_end_dates(start_date: str, end_date: str) -> bool:
    try:
        date_format = "%Y-%m-%d"
        s_date = datetime.strptime(start_date, date_format)
        e_date = datetime.strptime(end_date, date_format)

        if s_date.date() > e_date.date():
            return False
    except ValueError:
        return False

    return True


def validate_max_signups(max_signups: str) -> bool:
    try:
        int_max_signups = int(max_signups)

        if int_max_signups <= 0:
            return False
    except ValueError:
        return False

    return True
