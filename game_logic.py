import json
import os
import random
import pygame
from settings import *

ARCHIVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive.json")


def _minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


SHIFT_GAME_MINUTES = _minutes(SHIFT_END) - _minutes(SHIFT_START)


def clock_to_real(hhmm):
    return (_minutes(hhmm) - _minutes(SHIFT_START)) * SHIFT_DURATION_S / SHIFT_GAME_MINUTES


def fmt_clock(real_s):
    total = _minutes(SHIFT_START) + min(real_s, SHIFT_DURATION_S) * SHIFT_GAME_MINUTES / SHIFT_DURATION_S
    total = int(total)
    return f"{total // 60 % 24:02d}:{total % 60:02d}"


ACT_STARTS = [clock_to_real(a["start"]) for a in ACTS]


def act_at(real_s):
    act = 0
    for i, start in enumerate(ACT_STARTS):
        if real_s >= start:
            act = i
    return act


def load_archive():
    try:
        with open(ARCHIVE_PATH) as f:
            return set(json.load(f))
    except (OSError, ValueError):
        return set()


def save_archive(found):
    archive = load_archive() | set(found)
    try:
        with open(ARCHIVE_PATH, "w") as f:
            json.dump(sorted(archive), f)
    except OSError:
        pass
    return archive


def rating(stats, survived):
    if not survived:
        return "F", "SIGNAL LOST"
    accuracy = stats["logged"] / max(1, stats["spawned"])
    score = accuracy * 100 - stats["false_alarms"] * 6 - stats["missed"] * 10
    for threshold, grade, label in ((90, "S", "UNBLINKING"), (75, "A", "VIGILANT"),
                                    (55, "B", "ATTENTIVE"), (35, "C", "DISTRACTED")):
        if score >= threshold:
            return grade, label
    return "D", "COMPROMISED"


class AnomalyManager:
    def __init__(self, rooms):
        self.rooms = rooms
        self.anomalies = []
        for cam, room in rooms.items():
            for a in room.anomalies:
                self.anomalies.append({**a, "cam": cam, "uid": f"{cam}:{a['key']}", "rect": pygame.Rect(a["hitbox"]),
                                       "active": False, "hover": False, "evaded": False, "since": 0})
        self.total = len(self.anomalies)
        self.reset(0)

    def reset(self, now):
        self.start = now
        self.sanity = INITIAL_SANITY
        self.locked_until = 0
        self.next_spawn = now + FIRST_SPAWN_DELAY_MS
        self.act = 0
        self.result = None
        self.reason = None
        self.logged = 0
        self.false_alarms = 0
        self.spawned = 0
        self.seen = set()
        self.found = set()
        self.end_elapsed = None
        for a in self.anomalies:
            a["active"] = a["hover"] = a["evaded"] = False


    def elapsed(self, now):
        if self.end_elapsed is not None:
            return self.end_elapsed
        return (now - self.start) / 1000

    def is_locked(self, now):
        return now < self.locked_until

    @property
    def active_count(self):
        return sum(1 for a in self.anomalies if a["active"])

    def breach_count(self, now):
        return sum(1 for a in self.anomalies if a["active"] and now - a["since"] >= BREACH_GRACE_MS)

    def state_for(self, cam):
        state = dict(self.rooms[cam].base_state)
        for a in self.anomalies:
            if a["active"] and a["cam"] == cam:
                state.update(a["changes"])
        return state

    def stats(self):
        s = {
            "survived": fmt_clock(self.end_elapsed or 0),
            "logged": self.logged,
            "unique": len(self.found),
            "total": self.total,
            "false_alarms": self.false_alarms,
            "missed": self.active_count,
            "spawned": self.spawned,
            "found": set(self.found),
        }
        s["grade"], s["label"] = rating(s, self.result == "WIN")
        return s

    def shift_time(self, ms):
        self.start += ms
        self.next_spawn += ms
        if self.locked_until:
            self.locked_until += ms
        for a in self.anomalies:
            if a["active"]:
                a["since"] += ms


    def _finish(self, result, reason, now):
        self.result, self.reason = result, reason
        self.end_elapsed = (now - self.start) / 1000

    def update(self, now, observed_cam):
        events = []
        if self.result:
            return events
        el = self.elapsed(now)

        act = act_at(el)
        if act != self.act:
            self.act = act
            events.append("act")

        if el >= SHIFT_DURATION_S:
            self._finish("WIN", None, now)
            events.append("win")
            return events

        if now >= self.next_spawn:
            if self._activate(observed_cam, now):
                self.spawned += 1
                events.append("spawn")
            lo, hi = ACTS[self.act]["spawn"]
            self.next_spawn = now + int(random.uniform(lo, hi) * 1000)

        if self.breach_count(now) >= MAX_ACTIVE_ANOMALIES:
            self._finish("LOSE", "BREACH", now)
            events.append("lose")
        return events

    def _activate(self, exclude_cam, now, evaded=False, since=None):
        busy = {a["cam"] for a in self.anomalies if a["active"]}
        max_tier = ACTS[self.act]["tier"]
        pool = [a for a in self.anomalies
                if not a["active"] and a["cam"] not in busy and a["cam"] != exclude_cam and a["tier"] <= max_tier]
        if not pool:
            return None
        unseen = [a for a in pool if a["uid"] not in self.seen]
        if unseen:
            top = max(a["tier"] for a in unseen)
            fresh = [a for a in unseen if a["tier"] == top]
            pool = fresh if random.random() < 0.7 else unseen
        chosen = random.choice(pool)
        chosen["active"] = True
        chosen["hover"] = False
        chosen["evaded"] = evaded
        chosen["since"] = now if since is None else since
        self.seen.add(chosen["uid"])
        return chosen

    def hover(self, cam, pos, now):
        for a in self.anomalies:
            if a["cam"] != cam or not a["active"]:
                continue
            inside = a["rect"].collidepoint(pos)
            if inside and not a["hover"]:
                a["hover"] = True
                if not a["evaded"] and random.random() < EVADE_CHANCE:
                    if self._activate(cam, now, evaded=True, since=a["since"]):
                        a["active"] = False
                        return "evade"
            elif not inside:
                a["hover"] = False
        return None

    def report(self, cam, pos, now):
        if self.result or self.is_locked(now):
            return None, None
        for a in self.anomalies:
            if a["cam"] == cam and a["active"] and a["rect"].collidepoint(pos):
                a["active"] = False
                self.logged += 1
                self.found.add(a["uid"])
                return "hit", a

        self.false_alarms += 1
        self.sanity = max(0, self.sanity - SANITY_PENALTY)
        self.locked_until = now + LOCKOUT_DURATION_MS
        if self.sanity <= 0:
            self._finish("LOSE", "SANITY", now)
        return "miss", None
