from typing import TypeAlias
from datetime import datetime, timedelta
from random import Random
from dataclasses import dataclass

DurationType: TypeAlias = timedelta | int | float


sim_random: Random = Random()
NEXT_USER_ID: int = 0


def get_user_id() -> int:
    global NEXT_USER_ID
    rv = NEXT_USER_ID
    NEXT_USER_ID += 1
    return rv


def flatten(ls: list[list]) -> list:
    return [x for l in ls for x in l]  # noqa: E741


def generate_times(start: datetime, duration_seconds: int, ct: int) -> list[datetime]:
    return [
        start + timedelta(seconds=sim_random.randint(0, round(duration_seconds)))
        for _ in range(ct)
    ]


def ensuretimedelta(t: DurationType) -> timedelta:
    if isinstance(t, int) or isinstance(t, float):
        return timedelta(seconds=t)
    else:
        return t


@dataclass
class LoginAttempt:
    user: int
    status: int
    time: datetime

    def __repr__(self):
        return f"LoginAttempt({self.user}, {self.status}, {self.time.strftime('%H:%M:%S')})"


class UserAction:
    ...


class Login(UserAction):
    def __call__(self, time: datetime, user: int, **kwargs):
        return [LoginAttempt(user=user, status=200, time=time)]


class LoginFail(UserAction):
    def __call__(self, time: datetime, user: int, **kwargs):
        return [LoginAttempt(user=user, status=401, time=time)]


class User:
    def __init__(
        self,
        duration: DurationType,
        behaviors: list[UserAction] | None = None,
        **kwargs,
    ):
        self._duration_seconds = ensuretimedelta(duration).total_seconds()
        self._behaviors = behaviors or []
        self._passed_kwargs = kwargs
        self._kwargs = {"user": get_user_id(), "ignored": None} | kwargs

    def __call__(self, start: datetime, **kwargs):
        trigger_times = sorted(
            generate_times(start, self._duration_seconds, len(self._behaviors))
        )
        return flatten(
            behavior(trigger, **(self._kwargs | kwargs))
            for behavior, trigger in zip(self._behaviors, trigger_times)
        )

    def __add__(self, other):
        if isinstance(other, UserAction):
            self._behaviors.append(other)
        else:
            raise ValueError("Adding something to a User that is not a UserAction")
        return self


class UserGroup:
    def __init__(self, user: User, count: int, **kwargs):
        self._passed_kwargs = kwargs
        self._users = [
            User(
                user._duration_seconds,
                user._behaviors,
                **(user._passed_kwargs | kwargs),
            )
            for _ in range(count)
        ]

    def __add__(self, other):
        rv = UserGroup(User(duration=0), 0, **self._passed_kwargs)
        rv._users.extend(self._users)
        rv._users.extend(other._users)
        return rv

    def __call__(self, start: datetime, duration_seconds: int, **kwargs):
        starttimes = generate_times(start, duration_seconds, len(self._users))
        return flatten(
            user(start, **kwargs) for user, start in zip(self._users, starttimes)
        )


class SingleMachineAttack:
    def __init__(self, fail_count: int, success_count: int):
        machine_id = get_user_id()
        self._behavior = UserGroup(
            User(duration=0, user=machine_id) + LoginFail(), fail_count
        ) + UserGroup(User(duration=0, user=machine_id) + Login(), success_count)

    def __call__(self, start: datetime, duration_seconds: int, **kwargs):
        return self._behavior(start, duration_seconds, **kwargs)


class Simulation:
    def __init__(self, start: datetime, duration: DurationType, **kwargs):
        self._start = start
        self._duration_seconds = ensuretimedelta(duration).total_seconds()
        self._sims = []
        self._passed_kwargs = kwargs
        self._kwargs = {"duration_seconds": self._duration_seconds} | kwargs

    def __add__(self, other):
        rv = Simulation(self._start, self._duration_seconds, **self._passed_kwargs)
        rv._sims.extend(self._sims)
        rv._sims.append(other)
        return rv

    def __iadd(self, other):
        self._sims.append(other)
        return self

    def __call__(self, **kwargs):
        starttimes = generate_times(
            self._start, self._duration_seconds, len(self._sims)
        )
        return flatten(
            sim(start, **(self._kwargs | kwargs))
            for start, sim in zip(starttimes, self._sims)
        )
