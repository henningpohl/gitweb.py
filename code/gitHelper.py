import os
import datetime

def gen_repository_list(rootdir):
    repositories = []
    for root, dirs, files in os.walk(rootdir):
        skipdirs = [d for d in dirs if d.endswith(".git")]
        for d in skipdirs:
            relpath = os.path.relpath(os.path.join(root, d), rootdir)
            repositories.append(unicode(relpath))
            dirs.remove(d)
    return repositories

def get_last_updating_commit(repo, branch, filelist):
    last_commit = None
    outInfo = { fh : None for fh in filelist }
    for c in repo.iter_commits(branch):
        for entry in c.tree.traverse():
            if entry.hexsha in outInfo:
                outInfo[entry.hexsha] = c
    return outInfo

def get_last_commit_time(repo):
    time_list = []
    for h in repo.heads:
        c = repo.commit(h)
        time_list.append(datetime.datetime.fromtimestamp(c.authored_date))
    if len(time_list) == 0:
        return None
    else:
        return max(time_list)
    

