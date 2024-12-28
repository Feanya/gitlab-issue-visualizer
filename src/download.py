import json
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
logging.basicConfig(level=logging.INFO)

projects_raw = []

with open("../settings/config.toml", mode="rb") as filehandle:
    config = tomllib.load(filehandle)


def main():
    (epics_raw, issues) = download(pickle_folder=Path(__file__).parent.parent / "pickles")
    epics: dict[int, Epic] = parse_epics(epics_raw)
    #print(epics)
    links_related, links_blocking, links_parent = aggregate_links(issues)

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


def iter_projects(gl: gitlab.Gitlab, group_no: int):
    grp = gl.groups.get(group_no)
    _log.info("Listing projects in %s", grp.full_path)
    for p in grp.projects.list(all=True):
        yield p
    for dg in grp.descendant_groups.list(all=True):
        for p in iter_projects(gl, dg.get_id()):
            yield p
    return


def download(pickle_folder: Path) -> tuple[list[gitlab.base.RESTObject], dict[int, Issue]]:
    # private token or personal token authentication (GitLab.com)

    url = config['server']['url']

    gl = gitlab.Gitlab(url, config['server']['private_token'])
    gq = gitlab.GraphQL(url, token=config['server']['private_token'])

    print("Authenticate...")
    gl.auth()
    print("Successful!")

    group_no = config['server']['group_no']
    projects = list(iter_projects(gl, group_no))
    with open(pickle_folder / "projects.json", "w") as jfile:
        json.dump({p.id : p.name for p in projects}, jfile, indent=4)
    _log.info("Found %i projects.", len(projects))

    # try:
    #     epics_raw = [e for e in project_group.epics.list(get_all=True, scope='all')]
    # except gitlab.exceptions.GitlabListError:
    epics_raw = []
    print("** Epics in group: ({n}) **".format(n=len(epics_raw)))


    projects_conf = config['projects']
    if not projects_conf:
        projects_take = [p.id for p in projects]
    else:
        projects_take = [p['project_no'] for p in projects_conf]
    print(f"** Requesting Issues in {len(projects_take)} projects...**")

    issues: dict[int, Issue] = {}
    for pid in projects_take:
        fp_savefile = pickle_folder / f"issues_{pid}.p"
        if fp_savefile.exists():
            with open(fp_savefile, "rb") as pfile:
                pissues = pickle.load(pfile)
            _log.info("Loaded %i issues from %s.", len(pissues), fp_savefile)
        else:
            pissues = download_project_issues(gl, gq, pid)
            with open(fp_savefile, "wb") as pfile:
                pickle.dump(pissues, pfile)
            _log.info("Cached %i issues in %s.", len(pissues), fp_savefile)
        issues.update(pissues)

    return epics_raw, issues


def download_project_issues(gl: gitlab.Gitlab, gq: gitlab.GraphQL, project_id: int) -> dict[int, Issue]:
    issues = {}
    for riss in gl.projects.get(project_id).issues.list(all=True):
        issues[riss.id] = to_issue(riss, gq)

    print(f"** Issues in project {project_id}: ({len(issues)}) **")
    return issues


def to_issue(iss: gitlab.v4.objects.ProjectIssue, client: gitlab.GraphQL) -> Issue:
    q = """
    query workItem {
    workItem(id: "gid://gitlab/WorkItem/%i") {
        #id
        #iid
        #title
        #state
        #webUrl
        widgets {
        #... on WorkItemWidgetLabels {
        #    labels {
        #    nodes {
        #        id
        #        title
        #        description
        #        color
        #        textColor
        #        __typename
        #    }
        #    __typename
        #    }
        #    __typename
        #}
        #... on WorkItemWidgetTimeTracking {
        #    timeEstimate
        #    totalTimeSpent
        #    __typename
        #}
        ... on WorkItemWidgetHierarchy {
            hasParent
            parent {
                id
                #iid
                #title
            }
            __typename
        }
        __typename
        }
        __typename
    }
    __typename
    }
    """ % (iss.id,)
    res = client.execute(q)
    # Extract parent issues from the corresponding entry in the widget list
    parent = None
    for widget in res["workItem"]["widgets"]:
        if widget["__typename"] != "WorkItemWidgetHierarchy":
            continue
        if widget["hasParent"]:
            parent = int(widget["parent"]["id"].split("/")[-1])

    # Parse links into serializable objects already (to facilitate caching)
    links: list[Link] = []
    for link in iss.links.list():
        if link.link_type == 'is_blocked_by':
            links.append(Link(link.id, iss.id, Link_Type.BLOCKS))
        elif link.link_type == 'blocks':
            link = Link(iss.id, link.id, Link_Type.BLOCKS)
        elif link.link_type == 'relates_to':
                link = Link(iss.id, link.id, Link_Type.RELATES_TO)
        links.append(link)
    if parent is not None:
        links.append(Link(iss.id, parent, Link_Type.IS_CHILD_OF))

    wi = Issue(
        uid=iss.id,
        iid=iss.iid,
        project_id=iss.project_id,
        title=iss.title,
        status={
            "closed": Status.CLOSED,
            "opened": Status.OPENED,
        }[iss.state],
        links=links,
        url=iss.web_url,
        has_iteration=bool(getattr(iss, "iteration", [])),
        epic_id=getattr(iss, "epic_iid", None),
        parent=parent,
    )
    return wi


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


def aggregate_links(issues: Mapping[int, Issue]) -> tuple[list[Link], list[Link], list[Link]]:
    print("'************\n\n************\nLinking...")
    links = {
        Link_Type.BLOCKS: [],
        Link_Type.RELATES_TO: [],
        Link_Type.IS_CHILD_OF: [],
    }

    for src in issues.values():
        for link in src.links:
            dst = issues.get(link.target)
            if dst is None:
                _log.warning("Can't find target %s of link in %i/%i (%s).", link.target, src.project_id, src.iid, src.title)
                continue
            links[link.type].append(link)

    rel = links[Link_Type.RELATES_TO]
    blo = links[Link_Type.BLOCKS]
    chi = links[Link_Type.IS_CHILD_OF]
    _log.info("Found %i relations, %i blocking and %i parent relationships.", len(rel), len(blo), len(chi))
    return rel, blo, chi


if __name__ == "__main__":
    start = time.time()
    main()
    finish = time.time()
    time_taken = finish - start
    print(f"download.py took {time_string(time_taken)}")
