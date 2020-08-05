#!/usr/bin/env python3
import argparse
import configparser
import git
import logging
import os
import sys
from smartlog.builder import TreeBuilder
from smartlog.printer import TreePrinter, TreeNodePrinter, RefMap
from time import time

logging.basicConfig()

logger = logging.getLogger("smartlog")
logger.setLevel(logging.ERROR)

def parse_args():
    parser = argparse.ArgumentParser(description="Git Smartlog")
    parser.add_argument("-a", "--all", action="store_true", help="Force display all commits, regardless of time")
    return parser.parse_args()

def main():
    start_time = time()


    args = parse_args()

    # Compute minimum commit time for displayed commits
    if args.all:
        date_limit = None
    else:
        date_limit = time() - (14 * 24 * 3600)  # 14 days

    # Attempt to open the git repo in the current working directory
    cwd = os.getcwd()
    try:        
        repo = git.Repo(cwd)
    except git.exc.InvalidGitRepositoryError:
        print("Could not find a git repository at {}".format(cwd))
        exit(1)

    refmap = RefMap(repo.head)

    try:
        master_ref = repo.refs["origin/master"]
        refmap.add(master_ref)
    except IndexError:
        print("Unable to find origin/master branch")
        exit(1)

    tree_builder = TreeBuilder(repo, master_ref.commit, date_limit = date_limit)

    # Add current head commit
    tree_builder.add(repo.head.commit, ignore_date_limit = True)

    # Add all local branches (and remote tracking too)
    for ref in repo.heads:
        logger.debug("Adding local branch {}".format(ref.name))
        tree_builder.add(ref.commit)
        refmap.add(ref)

        try:
            remote_ref = ref.tracking_branch()
            if remote_ref is not None:
                logger.debug("Adding remote tracking branch {}".format(remote_ref.name))
                if remote_ref.commit != ref.commit:
                    tree_builder.add(remote_ref.commit)
                refmap.add(remote_ref)
        except ValueError:
            pass

    node_printer = TreeNodePrinter(repo, refmap)
    tree_printer = TreePrinter(repo, node_printer)
    tree_printer.print_tree(tree_builder.root_node)

    if tree_builder.skip_count > 0: 
        print("Skipped {} old commits. Use `-a` argument to display them.".format(tree_builder.skip_count))

    print("Finished in {:.2f} ms.".format(time() - start_time))

if __name__ == "__main__":
    main()
