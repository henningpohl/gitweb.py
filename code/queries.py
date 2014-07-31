import web

def repos_for_owner(owner):
    return web.config.db.query(
        """SELECT repositories.id, repositories.owner, repositories.name
           FROM repo_users INNER JOIN repositories
           ON repo_users.repoid = repositories.id
           WHERE repo_users.userid = $u""", vars=dict(u=owner))

def repos_for_user(user):
    return web.config.db.query(
        """SELECT repositories.id, repositories.owner, repositories.name
           FROM repo_users INNER JOIN repositories
           ON repo_users.repoid = repositories.id
           WHERE repo_users.userid = $u
           OR repo_users.userid IN (
             SELECT groupid FROM group_users WHERE group_users.userid = $u
           )""", vars=dict(u=user))

def viewable_repos_for_user(user, viewer):
    return web.config.db.query(
        """  SELECT id, owner, name
             FROM repositories
             WHERE owner = $u AND access = 'public'
           UNION
             SELECT repositories.id, repositories.owner, repositories.name
             FROM repo_users INNER JOIN repositories
             ON repo_users.repoid = repositories.id
             WHERE repo_users.userid = $v AND repositories.owner = $u
        """,  vars=dict(u=user, v=viewer))

def members_for_group(group):
    return web.config.db.query(
        """SELECT users.id AS id, group_users.role AS role, users.name AS name
           FROM group_users INNER JOIN users
           ON group_users.userid = users.id
           WHERE group_users.groupid = $g""", vars=dict(g=group))

def groups_for_user(user):
    return web.config.db.query(
        """SELECT group_users.groupid AS id, groups.name AS name
           FROM group_users INNER JOIN groups
           ON group_users.groupid = groups.id
           WHERE group_users.userid = $u""", vars=dict(u=user))

def groups_with_membership_for_user(user):
    return web.config.db.query(
        """SELECT a.id AS id, a.name AS name, b.members AS members FROM (
             SELECT group_users.groupid AS id, groups.name AS name
             FROM group_users INNER JOIN groups
             ON group_users.groupid = groups.id
             WHERE group_users.userid = $u
           ) AS a LEFT JOIN (
             SELECT groupid, COUNT(*) AS members
             FROM group_users
             GROUP BY groupid
           ) AS b
           ON a.id = b.groupid""", vars=dict(u=user))
