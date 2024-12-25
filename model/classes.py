from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

import gitlab.base


class Status(Enum):
    OPENED = 0
    CLOSED = 1


class Link_Type(Enum):
    RELATES_TO = 0
    BLOCKS = 1
    IS_CHILD_OF = 2


class Link:
    source: int
    target: int
    type: Link_Type

    def __init__(self, source: int, target: int, type: Link_Type):
        if target is None:
            raise ValueError(f"Link in has no target.")
        self.source = source
        self.target = target
        self.type = type

    def __str__(self):
        return "<Link {src}---{typ}--->{tgt}>".format(
            src=self.source,
            tgt=self.target,
            typ=self.type
        )

    def __eq__(self, other):
        if (self.source == other.source and self.target == other.target and self.type == other.type):
            return True
        return (
            self.source == other.target
            and {self.type, other.type} == {Link_Type.RELATES_TO}
        )


@dataclass
class Issue:
    uid: int
    iid: int
    project_id: int
    title: str
    status: Status
    links: list[Link]
    url: str
    has_iteration: bool
    epic_id: Optional[int]
    parent: Optional[int]

    def __str__(self):
        return "{} – {}/{}: {} ({})".format(self.uid, self.project_id, self.iid, self.title, (self.status.name).lower())


class Cluster:
    id: int
    name: str
    epics: List['Epic']

    def __init__(self, name, epics):
        self.name = name
        self.epics = epics

    def __str__(self):
        return f"Cluster: {self.name} ({len(self.epics)}) Epics)"


class Epic:
    uid: int
    title: str
    status: Status
    labels: list[str]
    description: str
    count_closed: int
    count_all_issues: int
    issue_uids: Optional[List[int]]

    def __init__(self, status, uid, title, labels, description, count_closed, count_all_issues, issue_uids=None):
        self.uid = uid
        self.title = title
        self.status = status
        self.labels = labels
        self.description = description
        self.count_closed = count_closed
        self.count_all_issues = count_all_issues
        self.issue_uids = issue_uids

    def __str__(self):
        return "{}: {} ({})".format(self.uid, self.title, self.status.name.lower())

    def __repr__(self):
        return "[Epic]: {}: {} ({})".format(self.uid, self.title, self.status.name.lower())


RelatedList = list[Link]
BlockList = list[Link]
