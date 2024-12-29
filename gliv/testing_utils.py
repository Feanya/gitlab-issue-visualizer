from gliv.classes import *


def get_epics() -> dict[int, Epic]:
    epics = {}
    epics[1] = Epic(Status.CLOSED,
                    1,
                    "Feature 1 MVP",
                    ["release::11'23"],
                    description="next: https:example.com/2",
                    count_closed=2,
                    count_all_issues=2,
                    issue_uids=[1001, 1002])
    epics[2] = Epic(Status.OPENED,
                    2,
                    "Feature 1 V2",
                    ["release::12'23"],
                    description="next: https:example.com/3",
                    count_closed=1,
                    count_all_issues=2,
                    issue_uids=[1003, 1004])
    epics[3] = Epic(Status.OPENED,
                    3,
                    "Feature 1 V3",
                    ["release::12'23"],
                    description="previous: https:example.com/1",
                    count_closed=7,
                    count_all_issues=15,
                    issue_uids=None)
    epics[4] = Epic(Status.OPENED,
                    4,
                    "Another feature MVP",
                    ["release::12'23"],
                    description="next: https:example.com/5",
                    count_closed=3,
                    count_all_issues=5,
                    issue_uids=None)
    epics[5] = Epic(Status.OPENED,
                    5,
                    "Another feature V2",
                    ["release::02'24", "feature"],
                    description="next: https:example.com/6",
                    count_closed=0,
                    count_all_issues=9,
                    issue_uids=None)
    epics[6] = Epic(Status.OPENED,
                    6,
                    "Another feature V3",
                    [],
                    description="",
                    count_closed=0,
                    count_all_issues=7,
                    issue_uids=None)
    epics[7] = Epic(Status.CLOSED,
                    7,
                    "Rollout Release 12'23",
                    ["release::12'23"],
                    description="include: https:example.com/1",
                    count_closed=0,
                    count_all_issues=0,
                    issue_uids=None)
    epics[8] = Epic(Status.OPENED,
                    8,
                    "New website",
                    ["homepage"],
                    description="related: https:example.com/7",
                    count_closed=0,
                    count_all_issues=0,
                    issue_uids=None)
    epics[9] = Epic(Status.CLOSED,
                    9,
                    "Migrate to Python 3",
                    ["technical debt", "09'23"],
                    description="",
                    count_closed=1,
                    count_all_issues=1,
                    issue_uids=None)
    return epics


def get_issues() -> dict[int, Issue]:
    issues = {}
    issues[1001] = Issue(Status.CLOSED,
                      1001,
                      1,
                      44,
                      1,
                      "F1: Add touch support",
                      "url",
                      False)
    issues[1002] = Issue(Status.CLOSED,
                      1002,
                      1,
                      44,
                      1,
                      "F1: Add touch support",
                      "url",
                      False)
    issues[1003] = Issue(Status.CLOSED,
                      1003,
                      1,
                      44,
                      2,
                      "F1: Add touch support",
                      "url",
                      False)
    issues[1004] = Issue(Status.OPENED,
                      1004,
                      1,
                      44,
                      2,
                      "F1: Add touch support",
                      "url",
                      False)
    issues[1005] = Issue(Status.OPENED,
                      1005,
                      1,
                      46,
                      None,
                      "Give code tour to new team member",
                      "url",
                      False)
    issues[1006] = Issue(Status.CLOSED,
                      1006,
                      1,
                      44,
                      None,
                      "Bug: Race condition in core routing",
                      "url",
                      False)
    issues[1007] = Issue(Status.CLOSED,
                      1007,
                      1,
                      44,
                      None,
                      "Bug: Feature",
                      "url",
                      False)
    issues[1008] = Issue(Status.CLOSED,
                      1008,
                      1,
                      44,
                      None,
                      "Bug: Race condition in core routing",
                      "url",
                      False)


    return issues


def get_links():
    pass
