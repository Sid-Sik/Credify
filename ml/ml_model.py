import math
import random
# READING THE FILE AND TAKING THE INPUT 
file = open("loan_data.csv", "r")
data = file.readlines()
file.close()
# DATA SPLIT AND NORMALIZATION 
x, y = [], []
for row in data[1:]:
    v = row.strip().split(",")
    x.append([
        float(v[0]) / 100000,
        float(v[1]),
        float(v[2]) / 10,
        float(v[3]) / 100000,
        float(v[4]) / 100,
        int(v[5]) / 120,
        float(v[6]),
        int(v[7]) / 10
    ])
    y.append(int(v[8]))
# TRAINING OF THE MODEL 
weights = [0.5, 1.2, 1.8, -0.6, 1.0, -0.4, 0.7, 0.9]
bias = -1.0
learning_rate = 0.1
n = len(x)

def sigmoid(z):
    z = max(min(z, 500), -500)
    return 1 / (1 + math.exp(-z))

for epoch in range(100):
    for i in range(len(weights)):
        gradient = sum((y[j] - sigmoid(sum(x[j][k] * weights[k] for k in range(8)) + bias)) * x[j][i] for j in range(n))
        weights[i] += learning_rate * gradient / n


train_probs = [sigmoid(sum(x[j][k] * weights[k] for k in range(8)) + bias) for j in range(n)]
train_preds = [1 if p >= 0.5 else 0 for p in train_probs]

accuracy = sum(1 for i in range(n) if train_preds[i] == y[i]) / n
tp = sum(1 for i in range(n) if train_preds[i] == 1 and y[i] == 1)
fp = sum(1 for i in range(n) if train_preds[i] == 1 and y[i] == 0)
fn = sum(1 for i in range(n) if train_preds[i] == 0 and y[i] == 1)

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print("=" * 45)
print("  TRAINING RESULTS (500 samples)")
print("=" * 45)
print(f"  Accuracy:  {accuracy * 100:.2f}%")
print(f"  Precision: {precision:.2f}")
print(f"  Recall:    {recall:.2f}")
print(f"  F1 Score:  {f1:.2f}")
print("=" * 45)

# TESTING OF THE MODEL 
random.seed(20)

test_x, test_y = [], []
for _ in range(100):
    mi  = random.randint(20000, 500000)
    er  = round(random.uniform(0.05, 0.90), 2)
    bc  = random.randint(0, 10)
    ab  = round(random.uniform(500, mi * 2), 2)
    cu  = round(random.uniform(5, 100), 2)
    js  = random.randint(1, 240)
    mer = round(random.uniform(0.20, 0.95), 2)
    elc = random.randint(0, 8)

    score = (-5.5 + 4.0*er + 0.30*bc - 0.000003*ab + 0.022*cu
             - 0.009*js - 0.0000025*mi + 0.18*elc + 1.8*mer)
    prob_default = sigmoid(score)
    label = 1 if random.random() < prob_default else 0

    test_x.append([mi/100000, er, bc/10, ab/100000, cu/100, js/120, mer, elc/10])
    test_y.append(label)

print("\n" + "=" * 45)
print("      LOAN DECISIONS (100 NEW APPLICANTS)")
print("=" * 45)

approved = rejected = 0
test_preds = []

for i, person in enumerate(test_x):
    z = sum(person[k] * weights[k] for k in range(8)) + bias
    prob = sigmoid(z)
    pred = 1 if prob >= 0.5 else 0
    test_preds.append(pred)
    decision = "REJECTED" if pred == 1 else "APPROVED"
    if pred == 1:
        rejected += 1
    else:
        approved += 1
    print(f"  Person {i+1:3}: {decision}  (default probability: {prob:.2f})")


t_tp = sum(1 for i in range(100) if test_preds[i] == 1 and test_y[i] == 1)
t_fp = sum(1 for i in range(100) if test_preds[i] == 1 and test_y[i] == 0)
t_fn = sum(1 for i in range(100) if test_preds[i] == 0 and test_y[i] == 1)

t_accuracy  = sum(1 for i in range(100) if test_preds[i] == test_y[i]) / 100
t_precision = t_tp / (t_tp + t_fp) if (t_tp + t_fp) > 0 else 0
t_recall    = t_tp / (t_tp + t_fn) if (t_tp + t_fn) > 0 else 0
t_f1        = 2 * t_precision * t_recall / (t_precision + t_recall) if (t_precision + t_recall) > 0 else 0

print("\n" + "=" * 45)
print("           TEST RESULTS (100 new people)")
print("=" * 45)
print(f"  Total APPROVED: {approved}")
print(f"  Total REJECTED: {rejected}")
print(f"  Accuracy:       {t_accuracy * 100:.2f}%")
print(f"  Precision:      {t_precision:.2f}")
print(f"  Recall:         {t_recall:.2f}")
print(f"  F1 Score:       {t_f1:.2f}")
print("=" * 45)