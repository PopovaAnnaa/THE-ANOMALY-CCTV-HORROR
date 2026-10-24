from settings import *

INTRO_LINES = [
    ("SUBTERRANEAN CONTAINMENT FACILITY - SECTOR 07", COLOR_GREEN),
    (f"{SHIFT_DATE} / 03:14 / TERMINAL 04", COLOR_GREEN),
    ("", None),
    ("Experiment #88 opened something inside the accelerator core.", COLOR_WHITE),
    ("OBJECT 88 has no stable body. It rewrites matter", COLOR_WHITE),
    ("only when no one is looking.", COLOR_WHITE),
    ("", None),
    ("The facility is sealed. The staff has been evacuated.", COLOR_WHITE),
    (f"The automatic gate seal engages at {SHIFT_END}.", COLOR_WHITE),
    ("Until then, you watch.", COLOR_WHITE),
    ("", None),
    ("PROTOCOL:", COLOR_AMBER),
    ("- Remember how every sector looks.", COLOR_LIGHT_GRAY),
    ("- When something changes, click it to log the anomaly.", COLOR_LIGHT_GRAY),
    ("- A false report blinds the feed for 3 seconds.", COLOR_LIGHT_GRAY),
    (f"- Never let {MAX_ACTIVE_ANOMALIES} anomalies stand unreported at once.", COLOR_LIGHT_GRAY),
    ("", None),
    ("It knows when it is being watched.", COLOR_RED),
]

INTERCOM = [
    ("03:16", "DR. VOSS", "Operator, this is Dr. Voss, surface control. Your feed is live. "
                          "Watch the sectors. Log everything that changes. Do not look away for long.", None, 0.0),
    ("03:42", "DR. VOSS", "It only rewrites what nobody is observing. Remember how the rooms looked. "
                          "Your memory is the containment.", None, 0.0),
    ("04:00", "DR. VOSS", "All personnel were evacuated at 02:50. If you see people on the cameras, "
                          "they are not people. Log them.", None, 0.0),
    ("04:24", "DR. VOSS", "Do not concern yourself with the pods in Cryo 05. "
                          "They are part of the protocol.", None, 0.0),
    ("04:48", "DR. VOSS", "How long have you been on shift, Operator? ...No. Don't answer that. "
                          "It doesn't matter anymore.", None, 0.0),
    ("05:00", "DR. VOSS", "--signal degrading-- keep watching. whatever happens. "
                          "do not let it see you blink.", None, 0.35),
    ("05:21", "AUTOMATED LOG", "Evacuation complete. One operator remains at Terminal 04. "
                               "Observer 03 transferred to stasis. Proceed with cycle 88.", "02:51", 0.08),
    ("05:38", "DR. VOSS", "Observer 04. You are doing better than the three before you.", None, 0.15),
    ("05:52", "DR. VOSS", "When the gate seals, stay at the console. Someone will come for you.", None, 0.2),
]

GLITCH_NAMES = {
    1: "IT IS WATCHING",
    2: "BIRTH-LAB",
    3: "SKIN VAULT",
    4: "NO EXIT",
    5: "YOUR VAULT",
    6: "ITS EYE",
    7: "HEARTBEAT",
    8: "IT IS CLOSE",
}

WINDOW_TITLE = "The Anomaly: CCTV Horror"
WINDOW_TITLE_HAUNTED = "it's behind you"


def ending_lines(result, reason):
    if result == "WIN":
        return [
            (f"{SHIFT_END}. AUTOMATIC SEAL ENGAGED.", COLOR_GREEN),
            ("PROTOCOL SUCCESSFUL. CONTAINMENT GATE 04 SEALED.", COLOR_GREEN),
            ("", None),
            ("DR. VOSS: Thank you, Observer 04.", COLOR_WHITE),
            ("DR. VOSS: Pod 04 has been prepared for you.", COLOR_WHITE),
            ("DR. VOSS: Begin cycle 89.", (190, 70, 60)),
        ]
    cause = (f"REALITY BREACH - {MAX_ACTIVE_ANOMALIES} ANOMALIES LEFT TOO LONG" if reason == "BREACH"
             else "OPERATOR PSYCHOLOGICAL COLLAPSE")
    return [
        ("SUBJECT NOTICED YOU.", COLOR_RED),
        ("SIGNAL LOST.", COLOR_RED),
        ("", None),
        (f"Cause: {cause}.", COLOR_LIGHT_GRAY),
    ]
