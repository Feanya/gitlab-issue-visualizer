import logging
import sys
from typing import Mapping, Sequence

import gitlab.v4
import gitlab.v4.objects
sys.path.append("..")

import gitlab
import pickle
import tomllib
from pathlib import Path
import time

from model.classes import *
from src.utils import time_string

_log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

projects_raw = []

with open("../settings/config.toml", mode="rb") as filehandle:
    config = tomllib.load(filehandle)


def main():
    (epics_raw, issues_raw, work_items) = download()
    epics: dict[int, Epic] = parse_epics(epics_raw)
    #print(epics)
    issues: dict[int, Issue] = parse_issues(issues_raw)
    #print(issues)
    links_related, links_blocking, links_parent = parse_links(issues_raw, issues, work_items)

    # dump
    print("***")
    print("Dump parsed stuff")
    Path("../pickles").mkdir(parents=True, exist_ok=True)
    pickle.dump(issues, open("../pickles/issues_conv.p", "wb"))
    pickle.dump(links_related, open("../pickles/links_related.p", "wb"))
    pickle.dump(links_blocking, open("../pickles/links_blocking.p", "wb"))
    pickle.dump(links_parent, open("../pickles/links_parent.p", "wb"))
    pickle.dump(epics, open("../pickles/epics_conv.p", "wb"))
    print("***")


def download():
    # private token or personal token authentication (GitLab.com)

    url = config['server']['url']

    gl = gitlab.Gitlab(url, config['server']['private_token'])
    gq = gitlab.GraphQL(url, token=config['server']['private_token'])

    print("Authenticate...")
    gl.auth()
    print("Successful!")

    group_no = config['server']['group_no']
    project_group = gl.groups.get(group_no)
    print(f"Downloading things from {url}, group {group_no} \"{project_group.name}\"...")

    projects = project_group.projects.list()
    print("** Projects in group: ({n}) **".format(n=len(projects)))

    try:
        epics_raw = [e for e in project_group.epics.list(get_all=True, scope='all')]
    except gitlab.exceptions.GitlabListError:
        epics_raw = []
    print("** Epics in group: ({n}) **".format(n=len(epics_raw)))


    projects_conf = config['projects']
    print(f"** Requesting Issues in {len(projects_conf)} projects...**")

    issues_raw = []
    work_items: dict[int, WorkItem] = {}
    for p in projects_conf:
        name = p['name']
        number = p['project_no']

        issues_project = gl.projects.get(number).issues.list(get_all=True, scope='all')
        issues_raw += issues_project
        for iss in issues_project:
            work_items[iss.id] = query_workitem(iss.id, gq)

        print(f"** Issues {name}: ({len(issues_project)}) **")

    return epics_raw, issues_raw, work_items


def query_workitem(iid: int, client: gitlab.GraphQL) -> WorkItem:
    q = """
    query workItem {
    workItem(id: "gid://gitlab/WorkItem/%i") {
        id
        iid
        title
        state
        webUrl
        widgets {
        ... on WorkItemWidgetLabels {
            labels {
            nodes {
                id
                title
                description
                color
                textColor
                __typename
            }
            __typename
            }
            __typename
        }
        ... on WorkItemWidgetTimeTracking {
            timeEstimate
            totalTimeSpent
            __typename
        }
        ... on WorkItemWidgetHierarchy {
            hasParent
            parent {
            id
            iid
            title
            }
            __typename
        }
        __typename
        }
        __typename
    }
    __typename
    }
    """ % (iid,)
    res = client.execute(q)
    parent = None
    for widget in res["workItem"]["widgets"]:
        if widget["__typename"] != "WorkItemWidgetHierarchy":
            continue
        if widget["hasParent"]:
            parent = int(widget["parent"]["id"].split("/")[-1])
    wi = WorkItem(
        iid=iid,
        title=res["workItem"]["title"],
        status={
            "CLOSED": Status.CLOSED,
            "OPEN": Status.OPENED,
        }[res["workItem"]["state"]],
        url=res["workItem"]["webUrl"],
        parent=parent,
    )
    return wi


def parse_issues(issues_from_gl) -> dict[int, Issue]:
    issue_dict = {}
    print(f"Parsing {len(issues_from_gl)} issues...")
    i = 0
    for issue in issues_from_gl:
        if issue.state == 'opened':
            s = Status.OPENED
        else:
            s = Status.CLOSED

        issue_conv = Issue(s,
                           issue.id,
                           issue.iid,
                           issue.project_id,
                           getattr(issue, "epic_iid", None),
                           issue.title,
                           issue.web_url,
                           bool(getattr(issue, "iteration", [])))

        if not issue.links.list():
            setattr(issue_conv, 'has_no_links', True)

        issue_dict[issue.id] = issue_conv
        i = i + 1
        if i == 20:
            print('.', end='')
            i = 0
    print('')

    return issue_dict


def parse_epics(epics_from_gl) -> dict[int, Epic]:
    print("Parsing epics...")
    epics_parsed: list[Epic] = []
    for epic in epics_from_gl:
        if epic.state == 'opened':
            s = Status.OPENED
        else:
            s = Status.CLOSED

        def count_closed(issue_list) -> int:
            c = 0
            for issue in issue_list:
                if issue.state == 'closed':
                    c = c + 1
            return c

        epic_issues = epic.issues.list(get_all=True)

        n = count_closed(epic_issues)
        m = len(epic_issues)

        #print(s, epic.iid, epic.title, n, '/', m)

        # if there are issues attached, get their uids
        if n > 0:
            issue_uids = {issue.id for issue in epic_issues}
        else:
            issue_uids = None

        epics_parsed.append(Epic(s, epic.iid, epic.title, epic.labels, epic.description, n, m, issue_uids))
    return {item.uid: item for item in epics_parsed}


def parse_links(
    issues_raw: Sequence[gitlab.v4.objects.ProjectIssue],
    issues: Mapping[int, Issue],
    work_items: Mapping[int, WorkItem],
) -> tuple[list[Link], list[Link], list[Link]]:
    print("'************\n\n************\nLinking...")
    verbose = False
    links_blocking: list[Link] = []
    links_related: list[Link] = []
    links_parent: list[Link] = []

    for issue in issues_raw:
        src = issues.get(issue.id)
        links = issue.links.list()
        for link in links:
            dst = issues.get(link.id)
            if dst is None:
                _log.warning("Can't find target %s of link in %i/%i (%s).", link.id, issue.project_id, issue.id, issue.title)
                continue

            if link.link_type == 'is_blocked_by':
                print("skip\n" if verbose else "s", end='')
                break
            elif link.link_type == 'blocks':
                # here we have a blocker
                link_conv = Link(src, dst, Link_Type.BLOCKS)
                links_blocking.append(link_conv)
                print(f"Added: {link_conv}\n" if verbose else ".", end="")

            elif link.link_type == 'relates_to':
                # check for duplication
                dub = False
                for l in links_related:
                    if l.target is None:
                        dub = True
                    if l.target.uid == issue.id:
                        dub = True

                if not dub:
                    link_conv = Link(src, dst, Link_Type.RELATES_TO)
                    links_related.append(link_conv)

                print(f"Added: {link_conv}\n" if verbose else ".", end="")

        # Get parent issue information from GraphQL
        wi = work_items[int(issue.id)]
        if wi.parent:
            links_parent.append(Link(src, issues.get(wi.parent), Link_Type.IS_CHILD_OF))

    return links_related, links_blocking, links_parent


if __name__ == "__main__":
    start = time.time()
    main()
    finish = time.time()
    time_taken = finish - start
    print(f"download.py took {time_string(time_taken)}")
