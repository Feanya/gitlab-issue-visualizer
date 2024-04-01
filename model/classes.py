from enum import Enum
from typing import Optional, List


class Status(Enum):
    OPENED = 0
    CLOSED = 1


class Link_Type(Enum):
    RELATES_TO = 0
    BLOCKS = 1
    IS_BLOCKED_BY = 2



class Issue:
    uid: int
    iid: int
    project_id: int
    title: str
    status: Status
    epic_id: int
    has_no_links: bool
    url: str
    has_iteration: bool
    epic_no: int

    def __init__(self, status, uid, iid, project_id, epic_id, title, url, has_iteration):
        self.uid = uid
        self.iid = iid
        self.project_id = project_id
        self.title = title
        self.status = status
        self.epic_id = epic_id
        self.url = url
        self.has_no_links = False
        self.has_iteration = has_iteration

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
    labels: [str]
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




class Link:
    source: Issue
    target: Issue
    type: Link_Type

    def __init__(self, source, target, type):
        self.source = source
        self.target = target
        self.type = type
    def __str__(self):

        if self.target is None:
            print(self.source)
        return "({u1}) {p1}/{id1} {t} ({u2}) {p2}/{id2}".format(
            p1=self.source.project_id,
            id1=self.source.iid,
            p2=self.target.project_id,
            id2=self.target.iid,
            u1=self.source.uid,
            u2=self.target.uid,
            t=self.type
        )

    def __eq__(self, other):
        if self.source.uid == other.target.uid:
            return True
        return False


RelatedList = [Link]
BlockList = [Link]
