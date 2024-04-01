# gitlab-issue-visualizer
Drawing issue- and epic-dependency graphs and some more useful graphs for Gitlab issues in a Gitlab group. 
This tool uses graphviz.

I wrote this tool to help with project management.

## What can be visualized?
### issues & issues_slim: The big issue graph
Here we see all issues and their dependencies (blocked and related links).
Also all epics are rendered, and the issues are connected to their epic. 
The graph is modeled with the `neato` spring model, so issues that are related are next to each other and issues are next to their epic.

Comes in a slim version that cleans up the visuals by shrinking closed issue nodes to only their ids (instead of including their title).

#### Usecases
- Identify and get an overview of issues that are not connected to anything (no epic or cluster)
- Find issues that might belong to an epic but are not yet added to one yet.
- Identify big groups of issues that are connected to each other
- Identify connections between epics (they are next to each other if their issues are connected)

### epics
Based on the configured epic-clusters (see Configuration options) the epics are shown using the `fdp` algorithm.
The epic rendering includes how many issues are closed out of all issues and groups the issues into clusters based on their labels.

#### Usecases
- Look at the progress of epics that are sorted into releases.
- Look at the progress of epics that are sorted by team, or feature, ...


### clustered_issues_by_epic
Based on the configured epic-clusters, but the issues are also rendered into the clusters. 
Issues without an epic (and therefore without a cluster) are shown divided by project.

Comes in a slim version that cleans up the visuals by shrinking closed issue nodes to only their ids (instead of including their title).

#### Usecases
- Identify which issues are blocking a release
- Identify which project has the most issues without an epic (for cleanup purposes)


## What is planned?
See https://github.com/Feanya/gitlab-issue-visualizer/labels/%E2%9C%A8%20Feature issues.

## How to use
1. Clone the repo
2. Install dependencies with `requirements.txt`
3. Copy `settings/config.example.toml` to `settings/config.toml` and insert your configuration
4. Run `src/download.py`
5. Run `src/render.py`
6. Look at your beautiful graphs in `renders/`. It is advised to use a browser to look at the svgs 
   - a) because they tend to be big and
   - b) because every epic and issue is neatly hyperlinked to the original Gitlab so you can easily read up more there.

## Configuration options
- The Gitlab `group` to look at. At the moment there is only single-group-support.
- Which projects to use from the group
- `Clusters`: Used in the epics-rendering: Group epics together in colored clusters.
