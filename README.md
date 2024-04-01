# gitlab-issue-visualizer
Drawing issue- and epic-dependency graphs and some more useful graphs for Gitlab issues in a Gitlab group. 
This tool uses graphviz.

## What can be visualized?

## What is planned?
See https://github.com/Feanya/gitlab-issue-visualizer/labels/%E2%9C%A8%20Feature issues.

## How to use
1. Clone the repo
2. Install dependencies with `requirements.txt`
3. Copy `settings/config.example.toml` to `settings/config.toml` and insert your configuration
4. Run `src/download.py`
5. Run `src/render.py`
6. Look at your graphs in `renders/`
