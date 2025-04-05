import threading
import numpy as np
import cv2 as cv
from setuptools import glob


def hashImageFeatures(name, d, FIX, debug=True):
    """
    Input:
        name : a string representing the baby's name to be hashed
        d: the number of dimensions to be in the feature vector
        FIX: the number of chunks to extract and hash from each string
        debug: a bool for printing debug values (default False)

    Output:
        v: a feature vector representing the input
    """

    # histogram? distribution of color -- images need to be RGB!
    color = ('b', 'g', 'r')
    imageVector = []
    for i, col in enumerate(color):
        imageVector.append(cv.calcHist([name], [i], None, [d], [0, 256]))

    return np.array([imageVector])


def wallimage2features(dir, d=128, FIX=3, LoadFile=True, debug=False):
    """
    Output:
        X : n feature vectors of dimension d, (nxd)
    """
    # read in images from a directorys.
    xTr = []
    if LoadFile:
        dir_items = glob.glob(dir + "/*.jpeg")
        if len(dir_items) > 0:
            [xTr.append(cv.imread(item, cv.IMREAD_COLOR)) for item in dir_items]
    else:
        pass  # loading from not a file; hold this!

    n = len(xTr)
    X = np.zeros((n, d, 3))

    for i in range(n):
        X[i, ::] = hashImageFeatures(xTr[i], d, FIX).reshape(3, d).T

    return (X, xTr) if debug else X


# NOTE: this would need to load the latest wall
#  and add it to xTr as opposed to read the
#  entire cache every frame
def genTrainFeatures(dimension=128):
    """
    Input:
        dimension: desired dimension of the features
    Output:
        X: n feature vectors of dimensionality d (nxd)
        Y: n labels (-1 = b, +1 = a) (n)
    """
    a_train_file = '_imagecache'
    b_train_file = '_imagecache_test'

    # Load in the data (the mutually exclusive class examples; the a & b are the classes (is vs. is not))
    x_a = wallimage2features(a_train_file, d=dimension)
    x_b = wallimage2features(b_train_file, d=dimension)

    # NOTE: this now needs to maintain state; we're
    #  caching previous values. Move these (X, Y) to instance variables
    X = np.concatenate([x_a, x_b])

    # Generate Labels
    Y = np.concatenate([-np.ones(len(x_a)), np.ones(len(x_b))])

    # shuffle data into random order
    ii = np.random.permutation([i for i in range(len(Y))])

    # IDEA: this is the wrong model for what I want to do.
    #  stopping work here.
    return X[ii, :], Y[ii]


class NaiveBayesClassifier(threading.Thread):

    def naivebayesPY(self, Y):
        """
        Estimate the class probability 𝑃(𝑦) in naivebayesPY. This should return the
        probability that a sample in the training set is positive or negative, independent of its features
        .
        naivebayesPY(X, Y) returns [pos,neg]

        Computation of P(Y)
        Input:
            X : n input vectors of d dimensions (nxd)
            Y : n labels (-1 or +1) (nx1)

        Output:
            pos: probability p(y=1)
            neg: probability p(y=-1)
        """

        # add one positive and negative example to avoid division by zero ("plus-one smoothing")
        Y = np.concatenate([Y, [-1, 1]])

        # take the mean of the elements in Y that meet the criteria 'Y == 1'; this an index of a, as True
        pos = np.mean(Y == 1)

        # ... and b; as False
        neg = np.mean(Y == -1)

        return pos, neg

    def naivebayesPXY(self, X, Y):
        """
        Estimate the conditional probabilities 𝑃([𝐱]𝛼=1|𝑌=𝑦)

        in naivebayesPXY. Notice that by construction, our features are binary categorical features.
        Use a categorical distribution as model and return the probability vectors for each feature
        being 1 given a class label. Note that the result will be two vectors of length d (the number
        of features), where the values represent the probability that feature i is equal to 1.

        Here we compute the fraction of counts that a feature is hot or not ([𝐱]𝛼=1 or [𝐱]𝛼=0) conditioned on gender.
        For example, if [𝐱]1=[1,0,1,0,1] and 𝑌=[1,1,1,1,−1] (a=1 and b=−1),
        then 𝑃([𝐱]1=1|𝑌=1)=(1+0+1+0)/4=0.5 and 𝑃([𝐱]1=1|𝑌=−1)=(1)/1=1.

        You need to compute this for each dimension 0 <= i < d for each gender.

        naivebayesPXY(X, Y) returns [posprob,negprob]

        Input:
            X : n input vectors of d dimensions (nxd)
            Y : n labels (-1 or +1) (n)

        Output:
            posprob: probability vector of p(x_alpha = 1|y=1)  (d)
            negprob: probability vector of p(x_alpha = 1|y=-1) (d)
        """
        n, d = X.shape

        # add one positive and negative example to avoid division by zero ("plus-one smoothing")
        X = np.concatenate([X, np.ones((2, d, n)), np.zeros((2, d, n))])
        Y = np.concatenate([Y, [-1, 1, -1, 1]])

        # take the mean of all of the elements in X that have the same index
        # as the conditional 'Y==1', moving on the axis index 0; These are 'a'
        posprob = np.mean(X[Y == 1], axis=0)

        # b
        negprob = np.mean(X[Y == -1], axis=0)

        return posprob, negprob

    def loglikelihood(self, posprob, negprob, X_test, Y_test):
        """
        Calculate the log likelihood log𝑃(𝐱|𝑌=𝑦)

        for each point in X_test given label Y_test in loglikelihood.
        Recall

            Naïve Bayes assumption: the likelihood 𝑃(𝐱|𝑌=𝑦)

        of a data point 𝐱 is equal to the product of the conditional probabilities of each feature
        [𝐱]𝛼 having value 𝑥𝛼, i.e., 𝑃(𝐱|𝑌=𝑦)=∏𝛼=1𝑑𝑃([𝐱]𝛼=𝑥𝛼|𝑌=𝑦).
        F
        or example, with 𝐱=[1,0,1] and corresponding label 𝑌=1,
        you will calculate likelihood 𝑃(𝐱|𝑌=1) as 𝑃([𝐱]1=1|𝑌=1)⋅𝑃([𝐱]2=0|𝑌=1)⋅𝑃([𝐱]3=1|𝑌=1)

        Given probabilities:

            posprob vector: 𝑃([𝐱]𝛼=1|𝑌=1)

        negprob vector: 𝑃([𝐱]𝛼=1|𝑌=−1)

        Fact log(𝑎𝑏)=log𝑎+log𝑏

        loglikelihood(posprob, negprob, X_test, Y_test) returns loglikelihood of each point in X_test

        Input:
            posprob: conditional probabilities for the positive class (d)
            negprob: conditional probabilities for the negative class (d)
            X_test : features (nxd)
            Y_test : labels (-1 or +1) (n)

        Output:
            loglikelihood (ll) of each point in X_test (n)
        """
        n, d = X_test.shape

        positive = list(Y_test == 1)
        negative = list(Y_test == -1)

        a_features = X_test[positive]
        b_features = X_test[negative]

        ll = np.ndarray(n)

        # the 'inverse' of boolean 'a_features' (i.e. 'not a') flips 1=0 & 0=1.
        # print(np.logical_not(a_features)) <= numpy way; think
        # print(1- a_features) <= idiomatic way

        # skew conditional probability negative; subtract 1 from existing array float values
        # print(1- negprob)

        # "product of the conditional probabilities of each feature [𝐱]𝛼 having value 𝑥𝛼"
        # a & 'not_a' ('inverse' features and skewed probs)
        a = np.dot(a_features, np.log(posprob))
        not_a = np.dot(1 - a_features, np.log(1 - posprob))
        # b & 'not_b'...
        b = np.dot(b_features, np.log(negprob))
        not_b = np.dot(1 - b_features, np.log(1 - negprob))

        # Sum...
        ll[positive] = a + not_a
        ll[negative] = b + not_b

        return ll

    def naivebayes_pred(self, pos, neg, posprob, negprob, X_test):
        """
        Observe that for a test point 𝐱𝑡𝑒𝑠𝑡, we should classify it as positive if the log ratio
        log(𝑃(𝑌=1|𝐱=𝐱𝑡𝑒𝑠𝑡)𝑃(𝑌=−1|𝐱=𝐱𝑡𝑒𝑠𝑡))>0 and negative otherwise. Implement the naivebayes_pred
        by first calculating the log ratio log(𝑃(𝑌=1|𝐱=𝐱𝑡𝑒𝑠𝑡)𝑃(𝑌=−1|𝐱=𝐱𝑡𝑒𝑠𝑡)) for each test point in 𝐱𝑡𝑒𝑠𝑡

        Using Bayes' rule and predict the label of the test points by looking at the log ratio.
        Recall

            Bayes' theorem:
            𝑃(𝑌=𝑦|𝐱=𝐱𝑡𝑒𝑠𝑡)=𝑃(𝐱=𝐱𝑡𝑒𝑠𝑡|𝑌=𝑦)⋅𝑃(𝑌=𝑦)𝑃(𝐱)

        𝑃(𝑌=𝑦|𝐱=𝐱𝑡𝑒𝑠𝑡)
        posterior∝𝑃(𝐱=𝐱𝑡𝑒𝑠𝑡|𝑌=𝑦)
        likelihood⋅𝑃(𝑌=𝑦) prior


        where ∝ is the proportionality symbol. Proportionality applies because we have dropped
        the denominator 𝑃(𝐱), which is just a multiplicative constant when finding 𝑦 that
        maximizes the posterior.

        Given probabilities:
            pos: 𝑃(𝑌=1)
            neg: 𝑃(𝑌=−1)

        posprob vector: 𝑃([𝐱]𝛼=1|𝑌=1)
        negprob vector: 𝑃([𝐱]𝛼=1|𝑌=−1)

        loglikelihood function just implemented.

        Facts log(𝑎𝑏)=log𝑎+log𝑏 and log(𝑎𝑏)=log𝑎−log𝑏 (can simplify your calculations).

        naivebayes_pred(pos, neg, posprob, negprob, X_test) returns the prediction of each point in X_test

        Input:
            pos: class probability for the positive class
            neg: class probability for the negative class
            posprob: conditional probabilities for the positive class (d)
            negprob: conditional probabilities for the negative class (d)
            X_test : features (nxd)

        Output:
            prediction of each point in X_test (n)
        """
        n, d = X_test.shape
        prediction = -np.ones(n)

        # loglikelihood + log of class prob... including 'inverse' probabilities
        ratio = self.loglikelihood(posprob, negprob, X_test, np.ones(n)) + np.log(pos) \
                - self.loglikelihood(posprob, negprob, X_test, -np.ones(n)) - np.log(neg)

        # leave what is > 0; (𝑃(𝑌=1|𝐱=𝐱𝑡𝑒𝑠𝑡)𝑃(𝑌=−1|𝐱=𝐱𝑡𝑒𝑠𝑡)) > 0
        prediction[ratio > 0] = 1

        return prediction


if __name__ == "__main__":

    DIMS = 128
    print('Loading data ...')
    # NOTE: this would need to iterate over the
    #  current _imagecache every time it changes
    X, Y = genTrainFeatures(DIMS)

    print('Training classifier ...')
    c = NaiveBayesClassifier()
    pos, neg = c.naivebayesPY(Y)
    posprob, negprob = c.naivebayesPXY(X, Y)

    error = np.mean(c.naivebayes_pred(pos, neg, posprob, negprob, X) != Y)
    print('Training error: %.2f%%' % (100 * error))

    while True:
        # NOTE: this would need to accept the current frame.
        frame = None
        xtest = wallimage2features(frame, d=DIMS, LoadFile=False)
        pred = c.naivebayes_pred(pos, neg, posprob, negprob, xtest)
        if pred > 0:
            print("This is an 'a'")  # 'seen' before
        else:
            print("This is a 'b'")




