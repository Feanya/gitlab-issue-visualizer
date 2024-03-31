import collections
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

    #print("Generate from linklist...")

    print("Generate epic overview...")
    render_epics_clustered(epics)
    #from_linklist(issues.values(), links_related, links_blocking)

    print("Done!")


def render_issues_with_links(issues: [Issue], list_related: RelatedList, list_blocks: BlockList):
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




def render_issues_clustered_by_epic(issues: dict[int, Issue], epics: dict[int, Epic]):
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

    # construct empty clusters
    clusters: dict[int, [Epic]] = {c['id']: [] for c in config['clusters']}
    epics_without_cluster: [Epic] = []

    # sort epics in clusters
    for epic in epics.values():
        fillcolor = 'lightcyan'
        fontcolor = 'black'
        if epic.status == Status.CLOSED:
            fillcolor = 'lightgray'

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


    #render all epics by cluster
    cluster_info_by_id = {c['id']: c for c in config['clusters']}
    for c_id, epics in clusters.items():
        print(c_id, epics)
        name = cluster_info_by_id[c_id]['pattern']

        with graph_epics.subgraph(name=f"cluster{name}") as cluster_subgraph:
            cluster_subgraph.attr(label=name)
            for epic in epics:
                fillcolor = 'lightcyan'
                fontcolor = 'black'
                if epic.status == Status.CLOSED:
                    fillcolor = 'lightgray'
                cluster_subgraph.node(f"{epic.uid}",
                       "{} ({}/{})".format(graphviz.escape(wrap_text(epic.title, 30)), epic.count_closed,
                                           epic.count_all_issues), style='filled',
                       color=fontcolor,
                       fontcolor=fontcolor,
                       URL=f"https://git.hs-rw.de/groups/campusapp/-/epics/{epic.uid}",
                       fillcolor=fillcolor, shape='folder')
    for epic in epics_without_cluster:
        graph_epics.node(f"{epic.uid}",
             "{} ({}/{})\n {}".format(graphviz.escape(wrap_text(epic.title, 30)),
                                      epic.count_closed, epic.count_all_issues,
                                      str(epic.labels)), style='filled',
             color=fontcolor,
             fontcolor=fontcolor,
             URL=f"https://git.hs-rw.de/groups/campusapp/-/epics/{epic.uid}",
             fillcolor=fillcolor, shape='folder')

    graph_epics.render('../renders/epics', format='svg', view=False)


def from_linklist(issues: [Issue], list_related: RelatedList, list_blocks: BlockList):


    for epic in epics.values():
        fillcolor = 'lightcyan'
        fontcolor = 'black'
        if epic.status == Status.CLOSED:
            fillcolor = 'lightgray'

        # add epic to issue graph
        graph_issues.node(f"{epic.uid}",
                          "{} ({})".format(graphviz.escape(wrap_text(epic.title, 30)), epic.uid),
                          style='filled',
                          color=fontcolor,
                          fontcolor=fontcolor,
                          URL=f"https://git.hs-rw.de/groups/campusapp/-/epics/{epic.uid}",
                          fillcolor=fillcolor, shape='folder')

        # add epic to epics graph
        labels = epic.labels


    # Mapping der Epics auf ihre IDs
    cluster_ids: [(str, [int])] = [(name, list(map(get_uid, epics))) for (name, epics) in clusters_new]

    # epics-Graph:
    for name, cluster in clusters_new:

        with graph_epics.subgraph(name=f"cluster{name}") as c:
            c.attr(label=name)
            for epic in cluster:
                fillcolor = 'lightcyan'
                fontcolor = 'black'
                if epic.status == Status.CLOSED:
                    fillcolor = 'lightgray'
                c.node(f"{epic.uid}",
                       "{} ({}/{})".format(graphviz.escape(wrap_text(epic.title, 30)), epic.count_closed,
                                           epic.count_all_issues), style='filled',
                       color=fontcolor,
                       fontcolor=fontcolor,
                       URL=f"https://git.hs-rw.de/groups/campusapp/-/epics/{epic.uid}",
                       fillcolor=fillcolor, shape='folder')

    issues_by_cluster = collections.defaultdict(list)
    for issue in issues:
        issues_by_cluster[find(cluster_ids, issue.epic_id)].append(issue)

    color = ''

    for name in issues_by_cluster:
        c_issues = issues_by_cluster.get(name)
        c_epics = dict(clusters_new).get(name)

        if name is not None:
            with graph_clusters.subgraph(name=f"cluster_{name}") as c:
                c.node_attr.update(style='filled', shape='tab')
                c.attr(label=name)

                for epic in list(c_epics):
                    if epic.status == Status.CLOSED:
                        fillcolor = 'lightgray'
                    else:
                        fillcolor = 'lightcyan'
                    c.node(f"{epic.uid}", "{}".format(graphviz.escape(wrap_text(epic.title, 30))),
                           style='filled',
                           #            color=fontcolor,
                           #            fontcolor=fontcolor,
                           URL=f"https://git.hs-rw.de/groups/campusapp/-/epics/{epic.uid}",
                           fillcolor=fillcolor,
                           shape='folder')

                for issue in c_issues:
                    if issue.status == Status.OPENED:
                        c.node(f"{issue.uid}",
                               "{}/{}\n{}".format(issue.project_id,
                                                  issue.iid,
                                                  graphviz.escape(wrap_text(issue.title, 30))),
                               fillcolor='lightcyan', URL=issue.url)
                    elif opened_only is False:
                        c.node(f"{issue.uid}",
                               "{}/{}\n{}".format(issue.project_id,
                                                  issue.iid,
                                                  graphviz.escape(wrap_text(issue.title, 30))),
                               fillcolor='lightgray', URL=issue.url)
                    if issue.epic_id:
                        c.edge(f'{issue.uid}', f'{issue.epic_id}', weight=weight_epics,
                               style='dashed',
                               color='gray',
                               # style='invis',
                               URL=f"https://git.hs-rw.de/groups/campusapp/-/epics/{issue.epic_id}"
                               )
                        fillcolor = 'lightcyan'
                        fontcolor = 'black'



        else:
            with graph_clusters.subgraph(name=f"cluster_rest") as c:
                for issue in c_issues:
                    if issue.status == Status.OPENED or opened_only == False:
                        add_issue(issue, c, 'white')

    # Issues einfügen
    for issue in issues:
        if issue.status == Status.CLOSED:
            fillcolor = 'ivory1'
            style = 'filled'
        else:
            fillcolor = color
            if issue.has_iteration:
                style = 'filled'
            else:
                style = 'filled,bold'
        add_issue(issue, graph_issues, fillcolor, style)

    for link in list_related:
        graph_issues.edge(f"{link.source.uid}",
                          f"{link.target.uid}")
        # graph_clusters.edge(f"{link.source.uid}",
        #                  f"{link.target.uid}")

    for link in list_blocks:
        graph_issues.edge(f"{link.source.uid}",
                          f"{link.target.uid}", dir='backward')

    # Postprocessing
    # dot.unflatten(stagger=3)  # funktioniert irgendwie noch nicht

    graph_clusters.edge('HS', 'cluster_Bonn')
    graph_clusters.edge('HS', 'cluster_UDE')
    graph_clusters.edge('HS', 'cluster_HRW')
    graph_clusters.edge('HS', 'cluster_Andere HS')
    graph_clusters.edges([("cluster_Release 04'23", "cluster_Release 09'23"),
                          ("cluster_Release 09'23", "cluster_Release 11'23"),
                          ("cluster_Release 11'23", "cluster_Release 12'23"),
                          ("cluster_Release 12'23", "cluster_Release 02'24"),
                          ("cluster_Release 02'24", "cluster_Zukunft"),
                          ])

    graph_issues.render('../renders/issues', format='svg', view=False)
    graph_clusters.render('../renders/clustered_issues', format='svg', view=False)


def add_issue(issue: Issue, dot: graphviz.Graph, fillcolor: str, style='filled'):
    color = 'black'
    shape = 'tab'
    fillcolor = "white"

    if issue.epic_id is None:
        shape = 'parallelogram'

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

