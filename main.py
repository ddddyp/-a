import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.datasets import make_moons
from sklearn.preprocessing import StandardScaler

# 生成示例数据
# make_moons函数用于生成两个交错的半环形数据，适合展示DBSCAN发现任意形状簇的能力
X, y = make_moons(n_samples=200, noise=0.05, random_state=42)

# 数据标准化
# 标准化可以使数据具有零均值和单位方差，有助于DBSCAN算法更好地工作
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 创建DBSCAN对象并进行聚类
# eps是邻域半径，min_samples是形成核心点所需的最小样本数
dbscan = DBSCAN(eps=0.3, min_samples=5)
clusters = dbscan.fit_predict(X_scaled)

# 可视化聚类结果
plt.figure(figsize=(10, 6))
# c=clusters指定颜色根据聚类标签来区分，cmap='viridis'使用颜色映射
plt.scatter(X_scaled[:, 0], X_scaled[:, 1], c=clusters, cmap='viridis', s=50)
# 找出噪声点（标签为 -1）并标记为红色
plt.scatter(X_scaled[clusters == -1, 0], X_scaled[clusters == -1, 1], c='red', marker='x', s=100, label='Noise')
plt.title('DBSCAN Clustering')
plt.xlabel('Feature 1')
plt.ylabel('Feature 2')
plt.legend()
plt.show()
# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。


def print_hi(name):
    # 在下面的代码行中使用断点来调试脚本。
    print(f'Hi, {name}')  # 按 Ctrl+F8 切换断点。


# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    print_hi('PyCharm')

# 访问 https://www.jetbrains.com/help/pycharm/ 获取 PyCharm 帮助
