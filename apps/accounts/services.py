from django.contrib.auth import get_user_model

User = get_user_model()


def next_officer_badge(station):
    officer_count = User.objects.filter(station=station, role=User.Role.OFFICER).count() + 1
    while True:
        badge = f"CST-{station.code}-{officer_count:04d}"
        if not User.objects.filter(username=badge).exists():
            return badge
        officer_count += 1


def next_commander_badge():
    commander_count = User.objects.filter(role=User.Role.COMMANDER).count() + 1
    while True:
        badge = f"CST-CMD-{commander_count:04d}"
        if not User.objects.filter(username=badge).exists():
            return badge
        commander_count += 1


def provision_personnel_account(*, role, first_name, last_name, password, station=None, email=None, must_change_password=True):
    if role == User.Role.OFFICER:
        if station is None:
            raise ValueError("Station is required for officer accounts.")
        badge_number = next_officer_badge(station)
        username = badge_number
    elif role == User.Role.COMMANDER:
        badge_number = next_commander_badge()
        username = badge_number
        station = None
    else:
        raise ValueError(f"Unsupported personnel role: {role!r}")

    user = User.objects.create(
        username=username,
        badge_number=badge_number,
        email=email or f"{badge_number.lower()}@lexguard.local",
        first_name=first_name,
        last_name=last_name,
        role=role,
        station=station,
        must_change_password=must_change_password,
        is_active=True,
    )
    user.set_password(password)
    user.save()
    return user


def provision_officer_account(*, station, first_name, last_name, password, email=None, must_change_password=True):
    return provision_personnel_account(
        role=User.Role.OFFICER,
        station=station,
        first_name=first_name,
        last_name=last_name,
        password=password,
        email=email,
        must_change_password=must_change_password,
    )


def provision_commander_account(*, first_name, last_name, password, email=None, must_change_password=True):
    return provision_personnel_account(
        role=User.Role.COMMANDER,
        first_name=first_name,
        last_name=last_name,
        password=password,
        email=email,
        must_change_password=must_change_password,
    )


def lock_account(user):
    user.is_active = False
    user.set_unusable_password()
    user.save(update_fields=["is_active", "password"])
    return user


def unlock_account(user, *, password=None, must_change_password=True):
    user.is_active = True
    user.must_change_password = must_change_password
    if password:
        user.set_password(password)
    user.save()
    return user
