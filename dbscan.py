from sklearn.cluster import DBSCAN
import numpy as np

# 输入数据
X = np.array([(1,1), (1,2), (2,1), (8,8), (8,9), (9,8), (15,15)])

# 创建DBSCAN对象，设置半径和最小样本数
dbscan = DBSCAN(eps=2, min_samples=3)

# 进行聚类
labels = dbscan.fit_predict(X)

# 输出聚类结果
for i in range(max(labels)+1):
    print(f"Cluster {i+1}: {list(X[labels==i])}")
print(f"Noise: {list(X[labels==-1])}")
