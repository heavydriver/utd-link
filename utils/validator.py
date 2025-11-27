import re


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
