from simulation import (
    flatten,
    User,
    LoginFail,
    Login,
    UserGroup,
    SingleMachineAttack,
    Simulation,
)
from datetime import datetime, timedelta
from collections import Counter

dt = datetime(year=2023, month=12, day=20, hour=5, minute=10)


def test_util_fns():
    assert flatten([[1, 2], [3, 4]]) == [1, 2, 3, 4]


def test_user():
    # times are randomly chosen in the interval [start, start+duration]
    user = User(duration=5) + LoginFail() + Login()
    for _ in range(20):
        las = user(dt)
        assert [la.status for la in las] == [401, 200]
        assert dt <= las[0].time <= las[1].time <= dt + timedelta(seconds=5)
        assert las[0].user == las[1].user

    # if duration=0, all actions happen at the same time, the start time
    user = User(duration=0) + LoginFail() + Login()
    las = user(dt)
    assert [la.status for la in las] == [401, 200]
    assert dt == las[0].time == las[1].time
    assert las[0].user == las[1].user


def test_user_group():
    ug = UserGroup(User(duration=2) + LoginFail() + Login(), 5)
    las = sorted(ug(dt, duration_seconds=20), key=lambda la: la.time.timestamp())
    # Note the 22 in the next assertion, the duration_seconds=20 of
    # the usergroup is about start times, than add the duration of the
    # user actions to it.
    assert all(dt <= la.time <= dt + timedelta(seconds=22) for la in las)
    user_ids = set(la.user for la in las)
    assert len(user_ids) == 5
    assert all(
        [la.status for la in las if la.user == id] == [401, 200] for id in user_ids
    )


def test_single_machine_attack():
    sma = SingleMachineAttack(10, 2)
    las = sma(dt, duration_seconds=20)
    assert all(dt <= la.time <= dt + timedelta(20) for la in las)
    cts = Counter(la.status for la in las)
    assert cts[401] == 10
    assert cts[200] == 2


def test_simulation():
    s = Simulation(start=dt, duration=20)
    su = s + (User(duration=0) + Login())
    las = su()
    assert [la.status for la in las] == [200]
    assert all(dt <= la.time <= dt + timedelta(20) for la in las)

    su = s + UserGroup(User(duration=0) + Login(), 10)
    las = su()
    assert [la.status for la in las] == [200] * 10
    assert all(dt <= la.time <= dt + timedelta(20) for la in las)

    s += User(duration=0) + Login()  # Change of simulation s
    las = s()
    assert [la.status for la in las] == [200]
    assert all(dt <= la.time <= dt + timedelta(20) for la in las)

    su = s + UserGroup(User(duration=0) + Login(), 10)
    las = su()
    assert [la.status for la in las] == [200] * 11
    assert all(dt <= la.time <= dt + timedelta(20) for la in las)
