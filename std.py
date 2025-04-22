#!/usr/bin/env python3


from datetime import timedelta
import pyproj


class STDBSCAN(object):

    def __init__(self, spatial_threshold=500.0, temporal_threshold=60.0,
                 min_neighbors=15):
        """

        """
        self.spatial_threshold = spatial_threshold
        self.temporal_threshold = temporal_threshold
        self.min_neighbors = min_neighbors

    def _retrieve_neighbors(self, index_center, matrix):

        center_point = matrix[index_center, :]

        # filter by time
        min_time = center_point[2] - timedelta(seconds=self.temporal_threshold)
        max_time = center_point[2] + timedelta(seconds=self.temporal_threshold)
        matrix = matrix[(matrix[:, 2] >= min_time) &
                        (matrix[:, 2] <= max_time), :]
        # filter by distance
        tmp = (matrix[:, 0]-center_point[0])*(matrix[:, 0]-center_point[0]) + \
            (matrix[:, 1]-center_point[1])*(matrix[:, 1]-center_point[1])
        neigborhood = matrix[tmp <= (
            self.spatial_threshold*self.spatial_threshold), 4].tolist()
        neigborhood.remove(index_center)

        return neigborhood

    def fit_transform(self, df, col_lat, col_lon, col_time,
                      col_cluster='cluster'):
        """

        """
        cluster_label = 0
        noise = -1
        unmarked = 777777
        stack = []

        # initial setup
        df = df[[col_lon, col_lat, col_time]]
        df[col_cluster] = unmarked
        df['index'] = range(df.shape[0])
        matrix = df.values
        df.drop(['index'], inplace=True, axis=1)

        # for each point in database
        for index in range(matrix.shape[0]):
            if matrix[index, 3] == unmarked:
                neighborhood = self._retrieve_neighbors(index, matrix)

                if len(neighborhood) < self.min_neighbors:
                    matrix[index, 3] = noise
                else:  # found a core point
                    cluster_label += 1
                    # assign a label to core point
                    matrix[index, 3] = cluster_label

                    # assign core's label to its neighborhood
                    for neig_index in neighborhood:
                        matrix[neig_index, 3] = cluster_label
                        stack.append(neig_index)  # append neighbors to stack

                    # find new neighbors from core point neighborhood
                    while len(stack) > 0:
                        current_point_index = stack.pop()
                        new_neighborhood = \
                            self._retrieve_neighbors(current_point_index,
                                                     matrix)

                        # current_point is a new core
                        if len(new_neighborhood) >= self.min_neighbors:
                            for neig_index in new_neighborhood:
                                neig_cluster = matrix[neig_index, 3]
                                if any([neig_cluster == noise,
                                        neig_cluster == unmarked]):
                                    matrix[neig_index, 3] = cluster_label
                                    stack.append(neig_index)

        df[col_cluster] = matrix[:, 3]
        return df
