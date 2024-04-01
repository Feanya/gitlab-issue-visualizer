import tomllib
import graphviz
import pickle

from model.classes import Issue, RelatedList, BlockList, Status, Epic

weight_epics = '30'
weight_relations = '10'
weight_cluster = '1'
opened_only = False

with open("../settings/config.toml", mode="rb") as filehandle:
    config = tomllib.load(filehandle)


def main():
    print("Read the pickles...")
    issues: [Issue] = pickle.load(open("../pickles/issues_conv.p", 'rb'))
    epics: [Epic] = pickle.load(open("../pickles/epics_conv.p", 'rb'))
    links_related: RelatedList = pickle.load(open("../pickles/links_related.p", 'rb'))
    links_blocking: BlockList = pickle.load(open("../pickles/links_blocking.p", 'rb'))

    print("Generate epic overview...")
    render_epics_clustered(epics)

    print("Generate issue overview, clustered by epics...")
    render_issues_clustered_by_epic(issues, epics)
    render_issues_clustered_by_epic(issues, epics, True)

    print("Generate issue overview...")
    render_issues_with_links(issues, epics, links_related, links_blocking)
    render_issues_with_links(issues, epics, links_related, links_blocking, True)

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
            print(issue)
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
        no_epic.attr(label='Ohne Epic')
        for project in config['projects']:
            print(project)
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
                            issue = issues[issue_uid]
                            add_issue(issue, c, 'white')

    # and the epics without a cluster
    with graph_clusters.subgraph(name=f"cluster_no_cluster") as no_cluster:
        no_cluster.attr(label='Ohne Cluster')
        with no_cluster.subgraph(name=f"cluster_no_cluster_closed") as d:
            no_cluster.attr(label='')
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
        c.attr(label="Kein Cluster",
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


def add_epic(epic: Epic, dot: graphviz.Graph):
    fillcolor = 'lightcyan'
    fontcolor = 'black'
    if epic.status == Status.CLOSED:
        fillcolor = 'lightgray'
    dot.node(f"{epic.uid}",
             "{} ({}/{})".format(graphviz.escape(wrap_text(epic.title, 30)), epic.count_closed,
                                 epic.count_all_issues), style='filled',
             color=fontcolor,
             fontcolor=fontcolor,
             URL=f"https://git.hs-rw.de/groups/campusapp/-/epics/{epic.uid}",
             fillcolor=fillcolor, shape='folder')


def add_issue(issue: Issue, dot: graphviz.Graph, fillcolor: str, style='filled', slim_style=False):
    color = 'black'
    shape = 'tab'
    fillcolor = "white"

    if issue.epic_id is None:
        shape = 'component'

    if issue.status == Status.CLOSED and issue.has_no_links:
        return
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
                 "{}/{}".format(issue.project_id,
                                issue.iid),
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
    main()
