from abc import ABC, abstractmethod
from typing import TypeAlias, TypeVar, Tuple
from collections.abc import Iterable, Callable
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


T = TypeVar("T")


def flatten(ls: Iterable[Iterable[T]]) -> list[T]:
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

    def __repr__(self) -> str:
        return f"LoginAttempt({self.user}, {self.status}, {self.time.strftime('%H:%M:%S')})"


class UserAction(ABC):
    @abstractmethod
    def __call__(
        self, time: datetime, user: int
    ) -> Tuple[list[LoginAttempt], datetime]:
        ...


class Login(UserAction):
    def __call__(
        self, time: datetime, user: int
    ) -> Tuple[list[LoginAttempt], datetime]:
        return [LoginAttempt(user=user, status=200, time=time)], time


class LoginFail(UserAction):
    def __call__(
        self, time: datetime, user: int
    ) -> Tuple[list[LoginAttempt], datetime]:
        return [LoginAttempt(user=user, status=401, time=time)], time


class Pause(UserAction):
    def __init__(self, duration: timedelta | int):
        self.duration = ensuretimedelta(duration)

    def __call__(
        self, time: datetime, user: int
    ) -> Tuple[list[LoginAttempt], datetime]:
        return [], time + self.duration


class PauseBetween(UserAction):
    def __init__(self, lower: timedelta | int, upper: timedelta | int):
        self.lower = ensuretimedelta(lower)
        self.upper = ensuretimedelta(upper)

    def __call__(
        self, time: datetime, user: int
    ) -> Tuple[list[LoginAttempt], datetime]:
        return [], time + timedelta(
            seconds=sim_random.randint(
                round(self.lower.total_seconds()), round(self.upper.total_seconds())
            )
        )


class User:
    def __init__(
        self, behaviors: list[UserAction] | None = None, user: int | None = None
    ):
        self._behaviors = behaviors or []
        self._passed_user: int | None = user
        self._user: int = user or get_user_id()

    def __call__(
        self, start: datetime, duration_seconds: int = 0
    ) -> list[LoginAttempt]:
        rv = []
        for behavior in self._behaviors:
            act, start = behavior(start, user=self._user)
            rv.extend(act)
        return rv

    def __add__(self, other: UserAction) -> "User":
        if isinstance(other, UserAction):
            self._behaviors.append(other)
        else:
            raise ValueError("Adding something to a User that is not a UserAction")
        return self


class UserGroup:
    def __init__(self, user: User, count: int):
        self._users = [
            User(user._behaviors, user=user._passed_user) for _ in range(count)
        ]

    def __add__(self, other: "UserGroup") -> "UserGroup":
        rv = UserGroup(User(), 0)
        rv._users.extend(self._users)
        rv._users.extend(other._users)
        return rv

    def __call__(self, start: datetime, duration_seconds: int) -> list[LoginAttempt]:
        starttimes = generate_times(start, duration_seconds, len(self._users))
        return flatten(user(start) for user, start in zip(self._users, starttimes))


class SingleMachineAttack:
    def __init__(self, fail_count: int, success_count: int):
        machine_id = get_user_id()
        self._behavior = UserGroup(
            User(user=machine_id) + LoginFail(), fail_count
        ) + UserGroup(User(user=machine_id) + Login(), success_count)

    def __call__(self, start: datetime, duration_seconds: int) -> list[LoginAttempt]:
        return self._behavior(start, duration_seconds)


class Simulation:
    def __init__(self, start: datetime, duration: DurationType):
        self._start = start
        self._duration_seconds = round(ensuretimedelta(duration).total_seconds())
        self._sims: list[Callable[[datetime, int], list[LoginAttempt]]] = []

    def __add__(self, other: "Simulation") -> "Simulation":
        rv = Simulation(self._start, self._duration_seconds)
        rv._sims.extend(self._sims)
        rv._sims.append(other)
        return rv

    def __iadd(self, other: "Simulation") -> "Simulation":
        self._sims.append(other)
        return self

    def __call__(
        self, start: datetime | None = None, duration_seconds: int | None = None
    ) -> list[LoginAttempt]:
        starttimes = generate_times(
            self._start, self._duration_seconds, len(self._sims)
        )
        return flatten(
            sim(start, self._duration_seconds)
            for start, sim in zip(starttimes, self._sims)
        )
