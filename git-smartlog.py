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

CONFIG_FNAME = "smartlog"

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
        repo = git.Repo(cwd, search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        print("Could not find a git repository at {}".format(cwd))
        exit(1)

    # Load the smartlog config file
    config = configparser.ConfigParser(allow_no_value = True)
    config.read(os.path.join(repo.git_dir, CONFIG_FNAME))
    
    refmap = RefMap(repo.head)

    head_refname = config.get("remote", "head", fallback="origin/HEAD")
    try:
        head_ref = repo.refs[head_refname]
        refmap.add(head_ref)
    except IndexError:
        print(f"Unable to find {head_refname} branch")
        exit(1)

    tree_builder = TreeBuilder(repo, head_ref.commit, date_limit = date_limit)

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

    # Add any extra remote branches from the config file
    if config.has_section("extra_refs"):
        for key in config["extra_refs"]:
            try:
                ref = repo.refs[key]
                refmap.add(ref)
                tree_builder.add(ref.commit)
            except IndexError:
                print(f"Unable to find {key} ref. Check configuration in .git/{CONFIG_FNAME} file")

    node_printer = TreeNodePrinter(repo, refmap)
    tree_printer = TreePrinter(repo, node_printer)
    tree_printer.print_tree(tree_builder.root_node)

    if tree_builder.skip_count > 0: 
        print("Skipped {} old commits. Use `-a` argument to display them.".format(tree_builder.skip_count))

    print("Finished in {:.2f} s.".format(time() - start_time))

if __name__ == "__main__":
    main()
