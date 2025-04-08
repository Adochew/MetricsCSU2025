# classifier_base.py
class DataClassifier:
    def classifyData(self): pass
    def readData(self): pass
    def transformData(self): pass
    def classify(self): pass
    def showResults(self): pass


class NaiveBayes:
    def handle(self): pass


class NaiveBayesClassifier(DataClassifier):
    def __init__(self):
        self.classifier = NaiveBayes()

    def classify(self):
        self.classifier.handle()


class KNN:
    def handle(self): pass


class KNNClassifier(DataClassifier):
    def __init__(self):
        self.classifier = KNN()

    def classify(self):
        self.classifier.handle()


class DecisionTree:
    def handle(self): pass


class DecisionTreeClassifier(DataClassifier):
    def __init__(self):
        self.classifier = DecisionTree()

    def classify(self):
        self.classifier.handle()
