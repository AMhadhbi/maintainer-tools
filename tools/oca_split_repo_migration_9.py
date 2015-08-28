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
    print("clone {0}".format(repo.git_url))
    cmd = ['git', 'clone', '--quiet', repo.git_url]
    # IT WORKS
    try:
        subprocess.check_call(cmd)
    except:
        pass
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
#    for dirname, module in repo.contents('.', ref=8.0).iteritems():
#        # check if this is a module
#        if module.type != 'dir':
#            continue
#        if dirname in ['__unported__', modulename]:
#            continue
#        cmd = ['git', 'filter-branch', '--tree-filter',
#               "rm -rf {0}".format(dirname), '-f', 'HEAD']
#        print(subprocess.check_call(cmd))
#    unported_content = repo.contents('__unported__', ref=8.0) or {}
#    for dirname, module in unported_content.iteritems():
#        if dirname == modulename:
#            continue
#        cmd = ['git', 'filter-branch', '--tree-filter',
#               "'rm -rf __unported__/{0}'".format(dirname), 'HEAD']
#        subprocess.check_call(cmd)
    # Here this should leave us with a pretty elaged tree
    # Now we can try to identify old names of the module
    # so we can display it to the user so he can do the final step
    # We will list all __openerp__.py files that have been moved or deleted
    # list deleted __openerp__.py in history
    cmd = ['git', 'log', '--diff-filter=D', '--summary']
    cmd2 = ['grep', '-E', '^delete.*__openerp__.py|^commit']
    cmd3 = ['grep', 'delete', '-B', '1']
    git_log = subprocess.check_output(cmd)

    # push the branch to the new repo
    cmd = ['git', 'push', 'repo_{0}'.format(modulename)]
    subprocess.check_call(cmd)
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
            description = u'Module {title} is part of {cat_title}'.format(
                title=modulename,
                cat_title=repo.description
            )
            # IT WORKS
            #newrepo = gh.create_repo(
            #    modulename,
            #    description=description
            #)
            # assign teams
            #for team in repo.iter_teams():
                #team.add_repo(u'{0}/{1}'.format(ORGNAME, modulename))
            # create an empty branch
            # hash = git hash-object -t tree /dev/null
            # http://stackoverflow.com/a/9766506/1945921
            #newrepo.create_ref(
            #    "9.0", '4b825dc642cb6eb9a060e54bf8d69288fbee4904')
            history_to_clean = extract(modulename, repo)
            if history_to_clean:
                history_to_clean += ("To remove a directory from history use: "
                                     "git filter-branch --tree-filter 'rm -rf "
                                     "{dirname}' HEAD")
            newrepo.refresh()
            newrepo.create_pull(
                "Migration to 9.0 [fork me]", "9.0",
                'OCA/migrate_{0}'.format(modulename),
                body="Migration of {0}\n{1}".format(modulename,
                                                    history_to_clean))
            # call set_repo_with_labels

            # add to web site page ??

if __name__ == '__main__':
    main()
