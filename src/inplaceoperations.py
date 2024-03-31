"""
This script aims to
"""
import gitlab


def authenticate() -> gitlab.Gitlab:
    """"  Get the Gitlab object """
    # private token or personal token authentication (GitLab.com)
    hrw_gl = gitlab.Gitlab(url='https://git.hs-rw.de', private_token='Q6ze5txC_gnwg8akx4ne')

    print("Authenticate...")
    hrw_gl.auth()
    print("Successful!")
    return hrw_gl


def assign_labels(issue):
    """ Takes a ticket, checks conditions and sends a request to assign labels """
    changes = False

    # no labels
    if not issue.labels:
        print(f"no labels: {issue.title}")
        issue.labels.append('🕵️missing:Labels')
        changes = True

    # no description
    if not issue.description:
        issue.labels.append('🕵️missing:Description')
        changes = True

    # no epic
    if not issue.epic_iid:
        issue.labels.append('🕵️missing:Epic')
        changes = True

    # bugs without impact
    if 'typ::Bug 🐛' in issue.labels \
            and 'Impact::1' not in issue.labels\
            and 'Impact::2' not in issue.labels\
            and 'Impact::3' not in issue.labels:
        issue.labels.append('Impact::?')
        changes = True

    # ownership/group
    label_list = ['was:CI/CD', 'was:Frontend', 'was:Backend', 'was:UI/UX', 'was:Betrieb', 'was:Orga', 'was:Design', 'was:Rollout', 'was:API', 'was:Betriebskonzept', 'typ::Konzeptionierung 📝', 'was:Doku']
    if not any(item in issue.labels for item in label_list):
        issue.labels.append('🕵️missing:Ownership')
        changes = True

    if changes:
        print(f"Added labels to: {issue.title}")
        issue.save()


gl = authenticate()

for i in range(44,49):  #49
    issues = gl.projects.get(i).all_issues.list(get_all=True, scope='all', state='opened')
    print("** Issues({p}): ({n}) **".format(p=i, n=len(issues)))
    for i in range(0, len(issues)):
        print(i)
        assign_labels(issues[i])
