import tomllib
import graphviz
import pickle
from pathlib import Path
import time

import mock.data
from model.classes import Issue, RelatedList, BlockList, Status, Epic
from src.utils import time_string
from src.graph import EpicGraph

weight_epics = '30'
weight_relations = '10'
weight_cluster = '1'
opened_only = False

test = False

if not test:
    with open("../settings/config.toml", mode="rb") as filehandle:
        config = tomllib.load(filehandle)
else:
    with open("../settings/config.example.toml", mode="rb") as filehandle:
        config = tomllib.load(filehandle)


def main():
    if not test:
        print("Read the pickles...")
        issues: dict[int, Issue] = pickle.load(open("../pickles/issues_conv.p", 'rb'))
        epics: dict[int, Epic] = pickle.load(open("../pickles/epics_conv.p", 'rb'))
        links_related: RelatedList = pickle.load(open("../pickles/links_related.p", 'rb'))
        links_blocking: BlockList = pickle.load(open("../pickles/links_blocking.p", 'rb'))
    else:
        issues = mock.data.get_issues()
        epics = mock.data.get_epics()

    Path("../renders").mkdir(parents=True, exist_ok=True)

    # print("Generate epic overview...")
    # render_epics_clustered(epics)

    print("Generate epic relationship overview...")
    render_epic_relationships(epics)

    # print("Generate issue overview, clustered by epics...")
    # render_issues_clustered_by_epic(issues, epics)
    # render_issues_clustered_by_epic(issues, epics, True)

    # print("Generate issue overview...")
    # render_issues_with_links(issues, epics, links_related, links_blocking)
    # render_issues_with_links(issues, epics, links_related, links_blocking, True)

    print("Done!")


def cluster_epics(epics: dict[int, Epic]) -> (dict[int, [Epic]], [Epic]):
    # construct empty clusters
    clusters: dict[int, [Epic]] = {c['id']: [] for c in config['clusters']}
    epics_without_cluster: [Epic] = []

    # sort epics in clusters
    for epic in epics.values():
        # determine the cluster
        labels = epic.labels
        cluster = None
        for l in labels:
            for c in config['clusters']:
                pattern = c['pattern']
                if pattern in l:
                    cluster = c['id']
        if cluster:
            clusters.update({cluster: clusters.get(cluster) + [epic]})
        else:
            epics_without_cluster.append(epic)

    return clusters, epics_without_cluster


def render_issues_with_links(issues: dict[int, Issue], epics: dict[int, Epic], list_related: RelatedList,
                             list_blocks: BlockList, exclude_closed_issues=False):
    """Render issues.svg: all issues with their epics and dependencies between the issues"""
    graph_issues = graphviz.Digraph(engine='neato',
                                    graph_attr=dict(
                                        # overlap='vpsc',
                                        # overlap_scaling='-20',
                                        # overlap_shrink='false',
                                        sep='+15',
                                        # scale='5',
                                        pack='true',
                                        fontsize='10pt',
                                        # ratio='5',
                                        defaultdist='15',
                                        overlap='prism', overlap_scaling='3', ratio='0.9'
                                    ),
                                    node_attr=dict(shape='circle', fontsize='10pt', margin='0.02,0.02', height='0.3'),
                                    edge_attr=dict(weight=weight_relations, len='0.2', dir='none'))

    # render all epics first
    for epic in epics.values():
        add_epic(epic, graph_issues)

    color = ''

    # Issues einfügen
    for issue in issues.values():
        if issue.status == Status.CLOSED:
            fillcolor = 'ivory1'
            style = 'filled'
        else:
            fillcolor = color
            if issue.has_iteration:
                style = 'filled'
            else:
                style = 'filled,bold'

        if not (issue.status == Status.CLOSED and exclude_closed_issues):
            add_issue(issue, graph_issues, fillcolor, style)
        else:
            add_issue(issue, graph_issues, fillcolor, style, True)

        if not issue.epic_id and issue.has_no_links:
            graph_issues.edge(f"{issue.uid}",
                              f"Kein Link oder Epic",
                              style='invis', )

    for link in list_related:
        graph_issues.edge(f"{link.source.uid}",
                          f"{link.target.uid}")

    for link in list_blocks:
        graph_issues.edge(f"{link.source.uid}",
                          f"{link.target.uid}", dir='backward')

    if exclude_closed_issues:
        graph_issues.render('../renders/issues_slim', format='svg', view=False)
    else:
        graph_issues.render('../renders/issues', format='svg', view=False)


def render_issues_clustered_by_epic(issues: dict[int, Issue], epics: dict[int, Epic],
                                    exclude_closed_epics: bool = False):
    graph_clusters = graphviz.Digraph(engine='fdp',
                                      graph_attr=dict(
                                          sep='+5',
                                          # scale='5',
                                          pack='true',
                                          fontsize='10pt',
                                          # ratio='5',
                                          defaultdist='10',
                                          overlap='prism', overlap_scaling='3', ratio='0.9',
                                          compound='true'
                                      ),
                                      node_attr=dict(shape='circle', fontsize='10pt', margin='0.02,0.02', height='0.3'),
                                      edge_attr=dict(weight=weight_relations, len='0.2', dir='none'))

    # first all issues without epics
    with graph_clusters.subgraph(name=f"cluster_no_epic") as no_epic:
        no_epic.attr(label='No epic')
        for project in config['projects']:
            with no_epic.subgraph(name=f"cluster_no_epic{project['name']}") as d:
                for uid, issue in issues.items():
                    d.attr(label=project['name'].capitalize())
                    # add the issues that don't have an epic
                    if not issue.epic_id and issue.project_id == project['project_no']:
                        add_issue(issue, d, 'lightgray')

    clusters, epics_without_clusters = cluster_epics(epics)
    cluster_info_by_id = {c['id']: c for c in config['clusters']}

    # now subgraphs for the clusters
    for c_id, epics in clusters.items():
        with graph_clusters.subgraph(name=f"cluster_{c_id}") as c:
            c.attr(label=cluster_info_by_id[c_id]['name'],
                   style='filled',
                   color=cluster_info_by_id[c_id]['color'])
            for epic in epics:
                add_epic(epic, c)

                # add the issues that have epics
                if epic.issue_uids:
                    if not (exclude_closed_epics and epic.status == Status.CLOSED):
                        for issue_uid in epic.issue_uids:
                            try:
                                issue = issues[issue_uid]
                                add_issue(issue, c, 'white')
                            except KeyError:
                                print("KeyError!\n" + str(issue) + str(epic))

    # and the epics without a cluster
    with graph_clusters.subgraph(name=f"cluster_no_cluster") as no_cluster:
        no_cluster.attr(label='No Cluster')
        with no_cluster.subgraph(name=f"cluster_no_cluster_closed") as d:
            d.attr(label='Closed epics')
            for epic in epics_without_clusters:
                if epic.status == Status.OPENED:
                    add_epic(epic, no_cluster)
                else:
                    add_epic(epic, d)

                # as well as their issues
                if epic.issue_uids:
                    if not (exclude_closed_epics and epic.status == Status.CLOSED):
                        for issue_uid in epic.issue_uids:
                            add_issue(issues[issue_uid], no_cluster, 'white')
                    else:
                        for issue_uid in epic.issue_uids:
                            add_issue(issues[issue_uid], d, 'white')

    if exclude_closed_epics:
        graph_clusters.render('../renders/clustered_issues_by_epic_slim', format='svg', view=False)
    else:
        graph_clusters.render('../renders/clustered_issues_by_epic', format='svg', view=False)


def render_epics_clustered(epics: dict[int, Epic]):
    graph_epics = graphviz.Digraph(engine='fdp',
                                   graph_attr=dict(
                                       sep='+15',
                                       # scale='5',
                                       pack='true',
                                       fontsize='10pt',
                                       # ratio='5',
                                       defaultdist='15',
                                       overlap='prism', overlap_scaling='3', ratio='0.9'
                                   ),
                                   node_attr=dict(shape='circle', fontsize='10pt', margin='0.02,0.02', height='0.3'),
                                   edge_attr=dict(weight=weight_relations, len='0.2', dir='none'))

    clusters, epics_without_cluster = cluster_epics(epics)

    # render all epics by cluster
    cluster_info_by_id = {c['id']: c for c in config['clusters']}
    for c_id, epics in clusters.items():
        name = cluster_info_by_id[c_id]['id']

        with graph_epics.subgraph(name=f"cluster{name}") as cluster_subgraph:
            cluster_subgraph.attr(label=cluster_info_by_id[c_id]['name'],
                                  style='filled',
                                  color=cluster_info_by_id[c_id]['color'])
            for epic in epics:
                add_epic(epic, cluster_subgraph)
    with graph_epics.subgraph(name=f"cluster_no_cluster") as c:
        c.attr(label="No cluster",
               style='filled',
               color='white')

        with c.subgraph(name=f"cluster_no_cluster_closed") as d:
            d.attr(label="  ",
                   style='filled',
                   color='white')
            for epic in epics_without_cluster:
                if epic.status == Status.CLOSED:
                    add_epic(epic, d)
                else:
                    add_epic(epic, c)

    graph_epics.render('../renders/epics', format='svg', view=False)


def render_epic_relationships(epics: dict[int, Epic], horizontal=True):
    """This rendering only makes sense if you use Gitlab Premium (but not Ultimate), because Premium does not support
    relationships between epics.
    It shows the relationship between epics based on some notation in the description.

    The syntax supports the following elements:
     - next: url
     - previous: url
     - includes: url
     - related: url

     Arguments:
         horizontal - Determines whether the "trees" in the graph will grow from left to right or bottom to top.
     """
    dot_graph = graphviz.Digraph(engine='fdp',
                                 graph_attr=dict(
                                     sep='+15',
                                     # scale='5',
                                     # pack='true',
                                     fontsize='10pt',
                                     # ratio='5',
                                     defaultdist='15',
                                     overlap='false', overlap_scaling='1',
                                 ),
                                 node_attr=dict(shape='circle', fontsize='10pt', margin='0.02,0.02', height='0.3'),
                                 edge_attr=dict(weight=weight_relations, len='0.2', dir='none'))

    # Analyze epics and their relationships
    epic_graph = EpicGraph(epics)
    orphans: list[int] = epic_graph.get_orphans()
    non_orphans: list[int] = [i for i in range(len(epic_graph)) if i not in orphans]

    # Cluster orphaned epics separately
    with dot_graph.subgraph(name='cluster_0') as c:
        c.attr(style='filled', color='lightgrey')
        c.node_attr.update(style='filled', color='white')
        c.attr(label='Orphaned Epics')

        for orphan in orphans:
            add_epic(epic_graph.epics[orphan], c, graph_id=orphan + 1)

    # Cluster all other epics
    with dot_graph.subgraph(name='cluster_1') as c:
        c.attr(style='filled', color='white')
        c.node_attr.update(style='filled', color='white')
        c.attr(label='Epics')

        positions: dict[tuple[int, int]] = {}
        height = 0
        cumulative_root_width = 0
        while len(positions.keys()) != len(non_orphans):
            # This while loop builds up the graph's nodes in layers starting from the roots.
            for i in non_orphans:
                if epic_graph.node_heights[i] == height and height == 0:
                    position = (cumulative_root_width, height * 2) if not horizontal \
                        else (height * 2, cumulative_root_width)
                    positions[i] = position
                    add_epic(epic_graph.epics[i], c, positions[i], i + 1)
                    # To prevent roots from being placed to close to each other the width of their tree is added.
                    cumulative_root_width += epic_graph.tree_widths[i]
                elif epic_graph.node_heights[i] == height:
                    if not horizontal:
                        position = (positions[epic_graph.node_parents[i]][0], height * 2)
                        while position in positions.values():
                            # If a position is taken by another node, the node will be placed next to it
                            position = (position[0] + 1, position[1])
                    else:
                        position = (height * 2, positions[epic_graph.node_parents[i]][1])
                        while position in positions.values():
                            # If a position is taken by another node, the node will be placed next to it
                            position = (position[0], position[1] + 1)
                    positions[i] = position
                    add_epic(epic_graph.epics[i], c, position, i + 1)
            height += 1

        # Adding the edges between nodes
        added_related_edges = []
        for i in range(len(epic_graph)):
            for j in epic_graph.next[i]:
                arrowhead = 'vee'
                direction = 'backward'
                dot_graph.edge(str(i + 1), str(j + 1), arrowhead=arrowhead, color='gray', dir=direction)
            for j in epic_graph.includes[i]:
                arrowhead = 'dot'
                direction = 'backward'
                dot_graph.edge(str(i + 1), str(j + 1), arrowhead=arrowhead, color='gray', dir=direction)
            for j in epic_graph.related[i]:
                if (i, j) not in added_related_edges:
                    arrowhead = 'vee'
                    direction = 'none'
                    dot_graph.edge(str(i + 1), str(j + 1), arrowhead=arrowhead, color='gray', dir=direction)
                    added_related_edges.append((i, j))
                    added_related_edges.append((j, i))

    dot_graph.render('../renders/epic_relationships', format='svg', view=False)


def add_epic(epic: Epic, dot: graphviz.Graph, pos: tuple[int, int] = None, graph_id=None):
    fillcolor = 'lightcyan'
    fontcolor = 'black'
    if epic.status == Status.CLOSED:
        fillcolor = 'lightgray'
    pos = f"{pos[0]},{pos[1]}!" if pos else ""

    dot.node(f"{graph_id if graph_id else epic.uid}",
             "{} ({}/{})".format(graphviz.escape(wrap_text(epic.title, 30)), epic.count_closed,
                                 epic.count_all_issues), style='filled',
             color=fontcolor,
             fontcolor=fontcolor,
             URL=f"https://git.hs-rw.de/groups/campusapp/-/epics/{epic.uid}",
             fillcolor=fillcolor, shape='folder', pos=pos)


def add_issue(issue: Issue, dot: graphviz.Graph, fillcolor: str, style='filled', slim_style=False):
    color = 'black'
    shape = 'tab'
    fillcolor = "white"

    if issue.epic_id is None:
        shape = 'component'

    if issue.status == Status.CLOSED:
        color = 'gray'
        shape = 'tab'
        style = 'filled'
    else:
        if issue.project_id == 46:
            color = 'darkgreen'
        if issue.project_id == 47:
            color = 'blue'

    # Node für das Issue anlegen
    if not slim_style:
        dot.node(f"{issue.uid}",
                 "{}/{}\n{}".format(issue.project_id,
                                    issue.iid,
                                    graphviz.escape(wrap_text(issue.title, 30))),
                 style=style,
                 color=color,
                 fontcolor=color,
                 shape=shape,
                 URL=issue.url,
                 fillcolor=fillcolor, )
    else:
        dot.node(f"{issue.uid}",
                 "{}/{}".format(issue.project_id, issue.iid),
                 style=style,
                 color=color,
                 fontcolor=color,
                 # shape=shape,
                 URL=issue.url,
                 fillcolor=fillcolor, )

    # Edges zum Epic
    if issue.epic_id:
        dot.edge(f'{issue.uid}', f'{issue.epic_id}', weight=weight_epics,
                 style='dashed',
                 color='gray',
                 # style='invis',
                 URL=f"https://git.hs-rw.de/groups/campusapp/-/epics/{issue.epic_id}"
                 )


def get_uid(epic: Epic) -> int:
    return epic.uid


def find(clusters, epic_id: int) -> str:
    for (name, ids) in clusters:
        if epic_id in ids:
            return name


def wrap_text(text: str, min_length: int) -> str:
    pos = min_length
    while pos < len(text):
        whitespace = text.find(' ', pos)
        if whitespace > 0:
            text = text[:whitespace] + '\n' + text[whitespace + 1:]
        else:
            break
        pos = whitespace + min_length
    return text


if __name__ == "__main__":
    start = time.time()
    main()
    finish = time.time()
    time_taken = finish-start
    print(f"render.py took {time_string(time_taken)}")
