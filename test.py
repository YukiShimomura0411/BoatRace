import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score
import torch
import torch.nn as nn
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score

data = pd.read_csv('/content/drive/MyDrive/merge_3/卒論データ.csv', index_col = None, header = 0, encoding = "cp932")

X = data.drop(["win_1"], axis=1)
T = data[["win_1"]]

X_train, X_test, T_train, T_test = train_test_split(X, T, test_size=0.1, random_state = 42)

DataList = []
for i in range(66):
    DataList.append(f'PC{i+1}')

x_train = X_train[DataList]
t_train = T_train["win_1"]

x_test = X_test[DataList]
t_test = T_test["win_1"]

print(len(x_train))
print(len(x_test))

x_train= torch.tensor(x_train.values, dtype=torch.float32)
x_test= torch.tensor(x_test.values, dtype=torch.float32)
t_train= torch.tensor(t_train.values, dtype=torch.long)
t_test= torch.tensor(t_test.values, dtype=torch.long)

t_train = t_train.reshape((-1,1))
t_test = t_test.reshape((-1,1))

from torch.utils.data import TensorDataset, DataLoader
train_dataset = TensorDataset(x_train, t_train)
test_dataset = TensorDataset(x_test, t_test)

batch_size = 430
train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=False)
test_dataloader = DataLoader(test_dataset, batch_size=batch_size, shuffle=True, drop_last=False)

import torch.nn.functional as F
class model(nn.Module):
    def __init__(self):
        super(model, self).__init__()
        self.model_info = nn.ModuleList([
             nn.Linear(66,100),
             nn.ReLU(),
             nn.BatchNorm1d(100),
             nn.Dropout(0.5),
             nn.Linear(100,50),
             nn.ReLU(),
             nn.BatchNorm1d(50),
             nn.Dropout(0.5),
             nn.Linear(50,1),
             nn.Sigmoid()
            ])

    def forward(self, x):
        for i in range(len(self.model_info)):
            x = self.model_info[i](x)
        return x

device = torch.device("cuda" if torch.cuda.is_available() else 'cpu')
model = model().to(device)

from torch import optim
criterion = nn.BCELoss()
l1_lambda = 0.0001
l2_lambda = 0.0001
optimizer = optim.Adam(model.parameters(), lr = 0.00001, weight_decay = l2_lambda)
for param in model.parameters():
    param.register_hook(lambda grad: l1_lambda * torch.sign(grad))
num_epochs = 500

loss_train_history = []
loss_test_history = []
accuracy_train_list = []
accuracy_test_list = []

for epoch in range(num_epochs):
  model.train()

  epoch_train_loss = 0
  epoch_test_loss = 0
  num_train_batches = 0
  num_test_batches = 0
  correct_train = 0
  correct_test = 0

  for x,t in train_dataloader:
    x = x.to(device)
    t = t.to(device).float()
    optimizer.zero_grad()
    y = model(x)
    loss_train = criterion(y,t)
    epoch_train_loss += loss_train.item()
    num_train_batches += 1
    pred_train = torch.where(y < 0.5,0,1)
    correct_train += pred_train.eq(t.view_as(pred_train)).sum().item()
    loss_train.backward()
    optimizer.step()

  model.eval()

  with torch.no_grad():
    for x,t in test_dataloader:
      x = x.to(device)
      t = t.to(device).float()
      y = model(x)
      loss_test = criterion(y,t)
      epoch_test_loss += loss_test.item()
      num_test_batches += 1
      pred_test = torch.where(y < 0.5,0,1)
      correct_test += pred_test.eq(t.view_as(pred_test)).sum().item()

  avg_train_loss = epoch_train_loss / num_train_batches
  loss_train_history.append(avg_train_loss)
  avg_test_loss = epoch_test_loss / num_test_batches
  loss_test_history.append(avg_test_loss)
  avg_train_acc = correct_train / len(train_dataset)
  accuracy_train_list.append(avg_train_acc)
  avg_test_acc = correct_test / len(test_dataset)
  accuracy_test_list.append(avg_test_acc)


  print(f"Epoch: {epoch+1}/{num_epochs}, Train_Loss: {avg_train_loss:.4f}, Train_Acc: {avg_train_acc:.4f}, Test Loss: {avg_test_loss:.4f}, Test_Acc: {avg_test_acc:.4f}")

model.eval()

loss_sum = 0
correct = 0

with torch.no_grad():
  for x,t in test_dataloader:
    x = x.to(device)
    t = t.to(device).float()
    y = model(x)
    loss_sum += criterion(y,t)
    pred = torch.where(y < 0.5,0,1)
    correct += pred.eq(t.view_as(pred)).sum().item()

print(f"Test Loss: {loss_sum.item() / len(test_dataloader)}, {100*correct/len(test_dataset)}% ({correct}/{len(test_dataset)})")

plt.figure(figsize=(10, 6))
plt.plot(range(1, num_epochs + 1), loss_train_history, label = 'Train Loss')
plt.plot(range(1, num_epochs + 1), loss_test_history, label = 'Test Loss')
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.grid()
plt.legend()
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(range(1, num_epochs + 1), accuracy_train_list, label='Train Accuracy')
plt.plot(range(1, num_epochs + 1), accuracy_test_list, label='Test Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.grid()
plt.legend()
plt.show()

pred = torch.where(model(x_train.to(device)) < 0.5,0,1)

#pred = pred.detach().cpu().numpy()
#pred

#prob = model(x_train.to(device))
#prob = prob.detach().cpu().numpy()
#prob

#X_train['pred_binary_1'] = pred

#X_train['pred_prob_1'] = prob

#X_train

#data_1 = X_train[X_train['pred_binary_1'] == 1]
#data_2 = X_train[X_train['pred_binary_1'] == 0]

#data_2[['rank_1']]

#data_1.to_csv('data_逃げるレース_3.csv', index=None, encoding='cp932')

#data_2.to_csv('data_逃げないレース_3.csv', index=None, encoding='cp932')

acc = accuracy_score(t_train,pred.cpu())
print('Acc :', acc)
pre = precision_score(t_train, pred.cpu(), average = None)
print('Pre :', pre)
recall = recall_score(t_train, pred.cpu(), average = None)
print('Recall :', recall)
f1 = f1_score(t_train, pred.cpu(), average=None)
print('F1 :', f1)

pred_1 = torch.where(model(x_test.to(device)) < 0.5,0,1)

acc = accuracy_score(t_test,pred_1.cpu())
print('Acc :', acc)
pre = precision_score(t_test, pred_1.cpu(), average = None)
print('Pre :', pre)
recall = recall_score(t_test, pred_1.cpu(), average = None)
print('Recall :', recall)
f1 = f1_score(t_test, pred_1.cpu(), average=None)
print('F1 :', f1)

print(loss)

from sklearn.metrics import accuracy_score
accuracy_score(t_test, model(x_test).argmax(dim=1))

! pip install shap

import shap

explanier = shap.DeepExplainer(model, x_train.to(device))

shap_values = explanier.shap_values(x_train.to(device), t_train.to(device))

