import pandas as pd

import csv, sys

from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn import tree, naive_bayes, svm, neural_network

folder = sys.argv[1]

labels = [1450, 1500,1550,1600,1650,1700,1750,1800,1850,1900,1950,2000]


print("loading csv")
X_train = pd.read_csv(f"{folder}/X_train.csv")
X_test = pd.read_csv(f"{folder}/X_test.csv")
y_train = pd.read_csv(f"{folder}/y_train.csv").values.ravel()
y_test = pd.read_csv(f"{folder}/y_test.csv").values.ravel()

# Decision tree
print("Decisions tree...")
clf_train = tree.DecisionTreeClassifier()
print("- fit")
clf_train = clf_train.fit(X_train, y_train)
print("- pred")
clf_y_pred = clf_train.predict(X_test)

# SVM
print("SVM...")
svm_train = svm.SVC()
print("- fit")
svm_train = svm_train.fit(X_train, y_train)
print("- pred")
svm_y_pred = svm_train.predict(X_test)

# Naive Bayes
print("Naive bayes...")
nb_train = naive_bayes.MultinomialNB()
print("- fit")
nb_train = nb_train.fit(X_train, y_train)
print("- pred")
nb_y_pred = nb_train.predict(X_test)

# MLP
print("Perceptron...")
mlp_train = neural_network.MLPClassifier(
    alpha=1e-5,
    hidden_layer_sizes=(100, 100, ),
    random_state=1
)
print("- fit")
mlp_train = mlp_train.fit(X_train, y_train)
print("- pred")
mlp_y_pred = mlp_train.predict(X_test)


clf_accuracy = accuracy_score(y_test, clf_y_pred)
svm_accuracy = accuracy_score(y_test, svm_y_pred)
nb_accuracy = accuracy_score(y_test, nb_y_pred)
mlp_accuracy = accuracy_score(y_test, mlp_y_pred)

clf_confusion = confusion_matrix(y_test, clf_y_pred, labels=labels)
svm_confusion = confusion_matrix(y_test, svm_y_pred, labels=labels)
nb_confusion = confusion_matrix(y_test, nb_y_pred, labels=labels)
mlp_confusion = confusion_matrix(y_test, mlp_y_pred, labels=labels)

clf_report = classification_report(y_test, clf_y_pred)
svm_report = classification_report(y_test, svm_y_pred)
nb_report = classification_report(y_test, nb_y_pred)
mlp_report = classification_report(y_test, mlp_y_pred)

print("=== DecisionTree Report ===")
print(clf_report)
print("=== SVM Report ===")
print(svm_report)
print("=== Naive Bayes Report ===")
print(nb_report)
print("=== MLP Report ===")
print(mlp_report)

print("DecisionTree accuracy", clf_accuracy)
print("SVM accuracy", svm_accuracy)
print("Naive Bayes accuracy", nb_accuracy)
print("MLP accuracy", mlp_accuracy)

pd.DataFrame(clf_confusion, index=labels, columns=labels).to_csv(f"confusion/clf_confusion.csv")
pd.DataFrame(svm_confusion, index=labels, columns=labels).to_csv(f"confusion/svm_confusion.csv")
pd.DataFrame(nb_confusion, index=labels, columns=labels).to_csv(f"confusion/nb_confusion.csv")
pd.DataFrame(mlp_confusion, index=labels, columns=labels).to_csv(f"confusion/mlp_confusion.csv")
