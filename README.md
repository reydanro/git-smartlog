# git-smartlog
`git-smartlog` displays a sparse graph of commits that are relevant to you.

It includes commits like (head, origin/master and any other local branches) while skipping commits that have very little value. 
For example, in the case of monorepo instances, master can contain hundreds of commits per day, which can make any standard `git log` very verbose. 

# Install

Clone the repo to the location of your choice

```bash
# Create a symlink to a location that is in your environment path (e.g)
$ ln -s /path-to-cloned-repo/git-smartlog.py ~/bin/git-smartlog

# Add an alias to the global git config
$ git config --global alias.sl smartlog

# Install git dependencies
$ python3 -m pip install gitpython colorama
```

(Quick explanation on the git alias: By default, whenever you try to run a command `git foo`, git will search for an executable binary named `git-foo`)

# How it works
Navigate to any folder in the repo you are working on and run
```bash
$ git sl
```
![smartlog example](/doc/example.png)

# Known limitations
`git-smartlog` currently does not support merged commits. Where I needed this so far, it was the case of a monorepo with a rebase approach to landing changes to the master branch. Merged commits were rare and adding support was not a necessity. If you need it, feel free to add it and contribute back to the community.
