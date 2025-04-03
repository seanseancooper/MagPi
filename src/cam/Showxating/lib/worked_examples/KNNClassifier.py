import os
import shutil
import threading
import numpy as np
from scipy.stats import mode
from sklearn.metrics.pairwise import euclidean_distances
from src.lib.instrumentation import timer
import logging

cam_logger = logging.getLogger('cam_logger')

def innerproduct(X, Z=None):
    if Z is None:  # case when there is only one input (X)
        return innerproduct(X, X)
    else:  # case when there are two inputs (X,Z)
        return np.dot(X, Z.T)

def l2distance(X, Z=None):
    if Z is None:
        return l2distance(X, X)
    return euclidean_distances(X, Z)


class KNNClassifier(threading.Thread):

    def __init__(self, k):
        super(KNNClassifier, self).__init__()
        self.xTr = None
        self.yTr = None
        self.xTe = None
        self.yTe = None
        self.k = k

    def get_config(self):

        try:
            # for KNN classifier... only imagecache online
            shutil.rmtree(self.imagecache)
        except Exception:
            pass

        try:
            # for debug... only imagecache online
            os.mkdir(self.imagecache)
        except Exception:
            pass

        return super().get_config()

    def accuracy_grader(self, truth, preds):

        truth = truth.flatten()
        preds = preds.flatten()

        if len(truth) == 0 and len(preds) == 0:
            output = 0
            return output
        return np.mean(truth == preds)

    def accuracy(self, truth, preds):
        """
        function output=accuracy(truth,preds)
        Analyzes the accuracy of a prediction against the ground truth

        Input:
        truth = n-dimensional vector of true class labels
        preds = n-dimensional vector of predictions

        Output:
        accuracy = scalar (percent of predictions that are correct)
        """
        i = [p == truth[i] for i, p in enumerate(preds)]
        return len(i) / len(truth)

    def load_frame_data(self, train_data, frame, f_id):
        # reinitialized on every pass.
        data = {"xTr": [],
                "yTr": [],
                "xTe": [],
                "yTe": [],
                }

        train_items = list(train_data.keys())
        if len(train_items) > 0:

            def loadTraining(item):
                data["xTr"].append(train_data.get(item).wall.flatten())  # try ravel, this is a copy
                data["yTr"].append(item)

            [loadTraining(item) for item in train_items]

            data["xTe"].append(frame.T.flatten())  # try ravel, this is a copy
            # this label is not really used. Why pass it in?
            data["yTe"].append(str(f_id))

            xTr = np.array(data["xTr"], dtype='float64').T      # 337920, 580 load in Training data (np.array of 'item')
            yTr = np.array([data["yTr"]])                       # 1, 580 load in Training labels (tags)
            xTe = np.array(data["xTe"], dtype='float64').T      # 337920, 7 load in Testing data
            yTe = np.array([data["yTe"]])                       # 1, 7 load in Testing labels

            self.xTr = xTr.T
            self.yTr = yTr.T
            self.xTe = xTe.T
            self.yTe = yTe.T

    def findknn(self, xTr, xTe, k):
        """
        function [indices,dists]=findknn(xTr,xTe,k);

        Finds the k nearest neighbors of xTe in xTr.

        Input:
        xTr = nxd input matrix with n row-vectors of dimensionality d
        xTe = mxd input matrix with m row-vectors of dimensionality d
        k = number of nearest neighbors to be found

        Output:
        indices = kxm matrix, where indices(i,j) is the i^th nearest neighbor of xTe(j,:)
        dists = Euclidean distances to the respective nearest neighbors
        """
        # Compute distances D between xTr and xTe
        # are these always the same size???
        D = l2distance(xTr, xTe)
        # [33403.42380655 35627.0538215 ]
        # sorted distances for each testing point in xTe
        dists = np.sort(D, axis=0)

        # create I (indices) argsort returns the indices that *would* sort an array
        indices = np.argsort(D, axis=0)

        # return "two matrices I and D, both of dimensions 𝑘×𝑚"
        # indices = kxm matrix, where indices(i,j) is the i^th nearest neighbor of xTe(j,:)
        # dists = Euclidean distances to the k nearest neighbors of xTe in xTr
        # return indices[:k], xTe_d_s[:k] or
        return indices[:k, :], dists[:k, :]

    def classify(self):
        """
        Output:
        preds = predicted labels, ie preds(i) is the predicted label of xTe(i,:)
        """

        indices, _ = self.findknn(self.xTr, self.xTe, self.k)
        vals = self.yTr[indices[0:]]  # the nearest neighbors, label in training set
        [print(f"candidate: {val}") for val in vals]
        mode_obj = mode(vals)

        return mode_obj[0][0]  # ...the one occurring most often.


if __name__ == "__main__":
    training_data = []
    test_data = []

    k = 5
    classifier = KNNClassifier(k)
    classifier.load_frame_data(training_data, test_data)  # load the data
    preds = classifier.classify()   # find single nearest neighbor of k

    [cam_logger.debug(f"prediction: {p}") for p in preds]
    cam_logger.debug("You obtained %.2f%% classification acccuracy\n" % (classifier.accuracy(classifier.yTe, preds) * 100.0,))
