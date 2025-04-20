from sklearn.cluster import DBSCAN
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler

# 加载数据集
iris = load_iris()
X = iris.data

# 数据预处理，标准化数据
scaler = StandardScaler()
X = scaler.fit_transform(X)

# 使用DBSCAN聚类算法
dbscan = DBSCAN(eps=0.5, min_samples=5)
y_pred = dbscan.fit_predict(X)

# 输出聚类结果
print('聚类结果:', y_pred)
