# -*- coding: utf-8 -*-
"""
This script allows to split a repository in multiple repositories.
In order to have one module per repository.

You can pass --repo to specify a single repository to split
In addition with --module you can extract a single module of this
repository
"""
import argparse
import os

from .github_login import login
import subprocess
from oca_projects import url, get_repositories

ORGNAME = 'OCA'
ORGNAME = 'yvaucher'
URL_MAPPING = 'git@github.com:%s/%s.git'


def extract(modulename, repo):
    """
    Extract one module from a single repository

    Keep all history which is not part of other modules

    :param modulename (str): Module to extract
    :param repo (Repository): repository from which we want to extract the
    module

    :return: a list of path which could be unclean history
    """
    # XXX check if repo exists locally
    if not os.path.exists:
        print("clone {0}".format(repo.git_url))
        cmd = ['git', 'clone', '--quiet', repo.git_url]
        subprocess.check_call(cmd)
    os.chdir(repo.name)
    print("Add a remote to dest repo")
    cmd = ['git', 'remote', 'add',
           'repo_{0}'.format(modulename), URL_MAPPING % (ORGNAME, modulename)]
    try:
        subprocess.check_call(cmd)
    except:
        pass
    print("Create new branch to do things")
    cmd = ['git', 'checkout', '-b', 'migrate_{0}'.format(modulename)]
    try:
        subprocess.check_call(cmd)
    except:
        pass
    for dirname, module in repo.contents('.', ref=8.0).iteritems():
        # check if this is a module
        if module.type != 'dir':
            continue
        if dirname in ['__unported__', modulename]:
            continue
        cmd = ['git', 'filter-branch', '--tree-filter',
               "rm -rf {0}".format(dirname), '-f', 'HEAD']
        print(subprocess.check_call(cmd))
    unported_content = repo.contents('__unported__', ref=8.0) or {}
    for dirname, module in unported_content.iteritems():
        if dirname == modulename:
            continue
        cmd = ['git', 'filter-branch', '--tree-filter',
               "'rm -rf __unported__/{0}'".format(dirname), 'HEAD']
        subprocess.check_call(cmd)
    # Here this should leave us with a pretty elaged tree
    # Now we can try to identify old names of the module
    # so we can display it to the user so he can do the final step
    # We will list all __openerp__.py files that have been moved or deleted
    # list deleted __openerp__.py in history
    cmd = ['git', 'log', '--diff-filter=D', '--summary']
    moved_terps = subprocess.check_output(cmd)

    # push the branch to the new repo
    cmd = ['git', 'push', 'repo_{0}'.format(modulename)]
    subprocess.check_call(cmd)
    os.chdir('..')
    return moved_terps


def main():
    gh = login()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--repo',
        help="Name of the repository you want to split"
    )
    parser.add_argument(
        '--module',
        help="Name of the module you want to split. It must be included "
             "in repo"
    )
    args = parser.parse_args()
    if not args.repo and not args.module:
        reply = raw_input(
            "You haven't specified a repo or a module do you want to split all"
            " repo? [y/N]")
        if reply.lower() != 'y':
            exit()
        repo_list = get_repositories(gh)
    elif not args.repo:
        exit("You must specify the repo in which the module is present")
    else:
        repo_list = [gh.repository(ORGNAME, args.repo)]
    for repo in repo_list:
        contents = repo.contents('.', ref=8.0)

        for modulename, module in contents.iteritems():
            if args.module and modulename != args.module:
                continue
            if modulename == '__unported__':
                continue
            # check if this is a module
            if module.type != 'dir':
                continue
            contents = repo.contents(modulename, ref=8.0)
            if '__openerp__.py' not in contents:
                continue
            newrepo = gh.repository(ORGNAME, modulename)
            if not newrepo:
                description = u'Module {title} is part of {cat_title}'.format(
                    title=modulename,
                    cat_title=repo.description
                )
                newrepo = gh.create_repo(
                    modulename,
                    description=description
                )
            # assign teams
            #for team in repo.iter_teams():
            #    team.add_repo(u'{0}/{1}'.format(ORGNAME, modulename))
            # create an empty branch (use first commit of old branch)
            history_to_clean = extract(modulename, repo)
            if history_to_clean:
                history_to_clean += (
                    "\nTo remove a directory from history use:\n"
                    "git filter-branch --tree-filter 'rm -rf {dirname}' HEAD")
            newrepo.refresh()
            if not newrepo.branch('refs/heads/9.0'):
                # get oldest commit
                init_commit = None
                for init_commit in newrepo.iter_commits():
                    pass
                newrepo.create_ref(
                    "refs/heads/9.0", init_commit.sha)
            if not newrepo.default_branch == '9.0':
                newrepo.edit("{0}/{1}".format(ORGNAME, modulename),
                             default_branch='9.0')
            import pdb; pdb.set_trace()
            newrepo.create_pull(
                "Migration to 9.0 [fork me]", "9.0",
                '{0}:migrate_{1}'.format(ORGNAME, modulename),
                body="Migration of {0}\n{1}".format(modulename,
                                                    history_to_clean))
            # call set_repo_with_labels

            # add to web site page ??

if __name__ == '__main__':
    main()
