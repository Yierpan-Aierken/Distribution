import pandas as pd
import numpy as np


class FilesDistributor:
    def __init__(self, files_filename, nodes_filename):
        """
        Distribute a list of files with different sizes to a list of nodes with different capacities
        :param files_filename:
        :param nodes_filename:
        """
        self.files, self.nodes = self.parse_files(files_filename, nodes_filename)
        if self.nodes.empty or self.files.empty:
            raise RuntimeError("one of the file contents are empty")

    def parse_files(self, files_filename, nodes_filename):
        """
        parse files and nodes using pandas' DataFrame.
        Adding 'notAllocated' and 'AssignedNode' columns in files to indicate the state of each file
        and the node it has assigned to. Adding 'files' columns to indicate a list of files it has
        been assigned to.
        """
        # read two files as pandas Dataframes
        files = pd.read_csv(files_filename, sep=' ',
                            header=None, comment='#', names=['files', 'size'],
                            dtype={'files': str, 'size': np.int32})
        nodes = pd.read_csv(nodes_filename, sep=' ',
                            header=None, comment='#', names=['nodes', 'capacity'],
                            dtype={'nodes': str, 'capacity': np.int32})
        # initialize them
        files['notAllocated'] = True
        files['AssignedNode'] = ''
        nodes['files'] = ''
        nodes['files'] = nodes['files'].apply(list)
        # make a copy of the total capacity
        nodes['space_left'] = nodes['capacity']
        return files, nodes

    def distribute(self):
        """
        Sort the files and the nodes by size and capacity respectively. First, assign the biggest file
        to the nodes with largest available capacity. Then, reduce the capacity by the
        size of the file it has been assigned. If the largest files size is bigger
        than the largest available node capacity, Mark as NULL. Repeat until all
        files are allocated or marked as NULL.

        """
        files = self.files
        nodes = self.nodes
        files.sort_values('size', inplace=True, ascending=False)
        while any(files['notAllocated']):  # repeat if any of the files is not allocated.
            rest_files = files[files['notAllocated']].copy()
            rest_files.sort_values('size', inplace=True, ascending=False)
            nodes.sort_values('space_left', inplace=True, ascending=False)  # sort the nodes by capacity
            for i in range(min(sum(rest_files['notAllocated']), len(nodes['space_left']))):
                # iterate for the shorter of two lists
                if nodes['space_left'].iloc[i] >= rest_files['size'].iloc[i]:  # if there is enough available space
                    # reduce the available space by file size
                    nodes.set_value(nodes.index[i], 'space_left',
                                    nodes['space_left'].iloc[i] - rest_files['size'].iloc[i])
                    # mark it as allocated
                    files.set_value(rest_files.index[i], 'notAllocated', False)
                    # mark which node it was assigned to
                    files.set_value(rest_files.index[i], 'AssignedNode', nodes['nodes'].iloc[i])
                    # append which file is assigned to this node
                    nodes['files'].iloc[i].append(rest_files['files'].iloc[i])
                elif i == 0:  # if there isn't available space on the largest node, mark it as NULL
                    files.set_value(rest_files.index[i], 'notAllocated', False)
                    files.set_value(rest_files.index[i], 'AssignedNode', 'NULL')
                    break  # break to resort the node, and repeat.

    def plot_bar(self):
        """
        plot the usage of each node containing blocks of bar for the files the node has been assigned.
        :return:
        """
        import matplotlib.pyplot as plt
        # pivot table files vs nodes with file size as elements
        files_nodes = pd.pivot_table(self.files[self.files['AssignedNode'] != 'NULL'], values='size',
                                     index='AssignedNode', columns='files')
        self.nodes.set_index('nodes', inplace=True)
        # append space left on each node
        total_fn = pd.concat([files_nodes, self.nodes['space_left']], axis=1)
        # make stacked bar plot
        n_col = int((len(self.files['files']) + 14) / 14)
        ax = total_fn.plot.bar(figsize=(5 + n_col * 2, 5), stacked=True, title='Files distribution among nodes',
                               cmap='nipy_spectral_r')
        ax.set_xlabel("Nodes")
        ax.set_ylabel("Capacity")
        # make legend for the file names, ncol will increase accordingly with the number of files
        ax.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.2, ncol=n_col)
        plt.tight_layout()
        plt.show()

    def print_output(self, out_files):
        from tabulate import tabulate
        self.files.set_index('files', inplace=True)
        self.nodes.sort_values('capacity', inplace=True, ascending=False)

        if out_files:
            # output files
            self.files.to_csv(out_files, columns=['AssignedNode'], header=False, sep=' ')
            # output nodes
            # self.nodes.to_csv('nodes.out',header=False,sep=' ',index=False)
        else:
            print tabulate(self.files[['size', 'AssignedNode']], headers='keys', tablefmt='fancy_grid')
            print tabulate(self.nodes, headers='keys', tablefmt='fancy_grid')
