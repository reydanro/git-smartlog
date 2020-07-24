import logging
from time import time
from git import Repo

logger = logging.getLogger("builder")
logger.setLevel(logging.ERROR)

class TreeBuilder:
    """
    A class that can build a sparse commit tree.
    Each node in the tree represents a commit that we want to display to the user.
    Nodes in this tree have a parent-child relationship that loosely matches the commit relationship.
    """
    def __init__(self, repo, master_commit, date_limit=None):
        if repo is None:
            raise ValueError("repo is null")
        if master_commit is None:
            raise ValueError("root ref is null")

        self.repo = repo
        self.master_commit = master_commit

        self.date_limit = date_limit
        self.skip_count = 0

        self.node_lookup = TreeNodeDict()

        # Create a root node to hold our entire tree
        self.root_node = TreeNode(repo, None)

        # Create a node for our master commit
        self.master_node = TreeNode(master_commit, is_on_master_branch = True)
        self.root_node.add_child(self.master_node)
        
        self.node_lookup.insert(self.master_node)


    """
    Main method for adding a new commit to the sparse tree
    """
    def add(self, commit, ignore_date_limit = False):
        if commit is None:
            logger.error("Invalid commit value (None)")
            return

        # Skip commit if we already processed it
        if self.node_lookup.get(commit) is not None:
            logger.debug("Commit {} is already processed".format(commit.hexsha))         
            return

        # Skip commits that are older than our date limit
        if self.date_limit is not None and not ignore_date_limit and commit.committed_date < self.date_limit:   
            self.skip_count += 1
            logger.debug("Skipping {} commit as too old. Date: {}".format(commit.hexsha, commit.committed_date))         
            return

        logger.info("Adding commit {}".format(commit.hexsha))

        # Find the lowest common ancestor commit
        lca_commit = self._get_lca_commit(commit, self.master_commit)
        if lca_commit is None:
            print("Warning: Unable to process commit that is not connected to master branch: {}".format(commit))
            return

        # Create nodes for all commits between commit and lca_commit
        last_node = None
        c = commit
        while c != lca_commit:
            if len(c.parents) > 1:
                logger.error("Merged commits are not supported!")
                return                 
            node = self.node_lookup.get(c)
            if node is None:
                node = TreeNode(c)
                self.node_lookup.insert(node)

            if last_node is not None:
                node.add_child(last_node)

            if node.has_parent():
                last_node = None
                break

            last_node = node
            c = c.parents[0]

        # Map the LCA commit into a new node if needed and insert in the tree
        lca_node = self.node_lookup.get(lca_commit)
        if lca_node is None:
            lca_node = TreeNode(lca_commit, is_on_master_branch = True)
            self.node_lookup.insert(lca_node)
            self._insert_lca(lca_node)

        # Connect our new commit chain to the LCA node
        if last_node is not None:
            lca_node.add_child(last_node)

    def _get_lca_commit(self, c1, c2):        
        commits = self.repo.merge_base(c1, c2)
        return commits[0] if len(commits) == 1 else None

    def _get_lca_node(self, node1, node2):
        commit = self._get_lca_commit(node1.commit, node2.commit)
        return self.node_lookup.get(commit) if commit is not None else None
        
    def _insert_lca(self, lca_node):
        """
        This method will adjust the entire tree by inserting a new common ancestor node.
        """

        def insert(parent, node, child):
            """
            Inserts a node between an already existing parent and child nodes
            """
            parent.remove_child(child)
            parent.add_child(node)
            node.add_child(child)

        if lca_node == self.master_node:
            return

        node = self.master_node
        while node is not None:
            if node.parent == self.root_node:
                insert(self.root_node, lca_node, node)
                break
                
            base_node = self._get_lca_node(lca_node, node.parent)
            if base_node == node.parent:
                insert(node.parent, lca_node, node)
                break

            node = node.parent    

class TreeNode:
    """
    A class that holds the definition of a node in the sparse commit tree
    """
    def __init__(self, commit, is_on_master_branch = False):
        self.commit = commit
        self.parent = None
        self.children = []
        self.is_on_master_branch = is_on_master_branch

    def add_child(self, node):
        if node is None:
            raise ValueError("node is null")
        node.parent = self
        self.children.append(node)

    def remove_child(self, node):
        if node is None:
            raise ValueError("node is null")
        if node.parent != self:
            return
        node.parent = None
        self.children.remove(node)

    def has_parent(self):
        return self.parent is not None

    
    def is_direct_child(self):
        """
        This method returns true if the parent of this node's commit matches the node's parent. Basically checks if there are
        commits between this node and its parent that have not been added to our tree.
        """
        if (self.commit is None or
            self.parent is None or
            self.parent.commit is None):
            return False
        return self.parent.commit in self.commit.parents


class TreeNodeDict:
    """
    A class that allows for fast lookup of a tree node based on its commit hash
    """
    def __init__(self):
        self.lookup = {}

    def insert(self, node):
        if node is None or node.commit is None:
            return
        self.lookup[node.commit.hexsha] = node

    def get(self, commit):
        if commit is None:
            return None
        try:
            return self.lookup[commit.hexsha]
        except KeyError:
            return None