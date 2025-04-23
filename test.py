import pandas as pd
from utils import get_vector_store, run_query
import os
from bert_score import score
import matplotlib.pyplot as plt

# Paths & config
GROUND_TRUTH_PATH = "ground_truth.csv"
CSV_FILES = ["Schemes.csv"]  # <- update your CSV source
PC_INDEX_NAME = "qa-assistant"  # <- update your index name

# Load ground truth data
df = pd.read_csv(GROUND_TRUTH_PATH)

# Set up vector store
vector_store = get_vector_store(PC_INDEX_NAME, CSV_FILES)

# Metrics
correct = 0
total = len(df)
precision_total = 0
recall_total = 0
f1_total = 0

# Tracking for plot
f1_scores = []
correct_flags = []

# Run test
for i, row in df.iterrows():
    question = row["question"]
    ground_truth = row["ground_truth"]

    print(f"\n🔍 Q{i+1}: {question}")
    response = run_query(question, vector_store)
    predicted_answer = response[0]  
    print(f"🧠 Predicted: {predicted_answer}")
    print(f"✅ Ground Truth: {ground_truth}")

    # Compute BERTScore (using 'bert-base-uncased' as the default model)
    P, R, F1 = score([predicted_answer], [ground_truth], lang='en')
    f1_value = F1.mean().item()

    # Add to totals for average calculation
    precision_total += P.mean().item()
    recall_total += R.mean().item()
    f1_total += f1_value

    # Track F1 score and correctness for plotting
    f1_scores.append(f1_value)
    correct_flags.append(f1_value > 0.9)

    if f1_value > 0.9:
        correct += 1

# Report
accuracy = correct / total * 100
avg_precision = precision_total / total
avg_recall = recall_total / total
avg_f1 = f1_total / total

print("\n📊 Evaluation Summary:")
print(f"   Accuracy        : {accuracy:.2f}% ({correct}/{total})")
print(f"   Avg Precision   : {avg_precision:.4f}")
print(f"   Avg Recall      : {avg_recall:.4f}")
print(f"   Avg F1 Score    : {avg_f1:.4f}")

# Plot F1 scores per question
plt.figure(figsize=(12, 6))
plt.bar(range(1, total + 1), f1_scores, color=["green" if c else "red" for c in correct_flags])
plt.axhline(0.9, color='blue', linestyle='--', label='Threshold (0.9)')
plt.title("BERTScore F1 per Question")
plt.xlabel("Question Number")
plt.ylabel("F1 Score")
plt.ylim(0, 1.05)
plt.xticks(range(1, total + 1))
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
