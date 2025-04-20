import requests
import pandas as pd
import matplotlib.pyplot as plt
import datetime

# 配置参数
API_KEY = "YOUR_API_KEY"  # 替换为你的 Etherscan API 密钥
ADDRESS = "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"  # 以太坊基金会地址示例
BASE_URL = "https://api.etherscan.io/api"

def get_transactions(address, num_tx=100):
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    if data["status"] == "1":
        df = pd.DataFrame(data["result"][:num_tx])
        df["time"] = df["timeStamp"].apply(lambda x: datetime.datetime.fromtimestamp(int(x)))
        df["value_eth"] = df["value"].astype(float) / 1e18  # 转换单位为 ETH
        return df
    else:
        print("Error:", data["message"])
        return pd.DataFrame()

# 获取最近的100笔交易
transactions = get_transactions(ADDRESS, 100)

# 数据清洗
transactions = transactions[transactions["value_eth"] > 0]  # 过滤零转账
transactions["gas_price_gwei"] = transactions["gasPrice"].astype(float) / 1e9  # 转换单位为 Gwei

# 生成图表
plt.figure(figsize=(14, 8))

# 图表1: 交易价值分布
plt.subplot(2, 2, 1)
plt.hist(transactions["value_eth"], bins=20, color='skyblue', edgecolor='black')
plt.title("Distribution of Transaction Values (ETH)")
plt.xlabel("ETH Amount")
plt.ylabel("Frequency")

# 图表2: Gas价格趋势
plt.subplot(2, 2, 2)
plt.plot(transactions["time"], transactions["gas_price_gwei"], marker='o', linestyle='-', color='orange')
plt.title("Gas Price Over Time")
plt.xlabel("Time")
plt.ylabel("Gas Price (Gwei)")
plt.xticks(rotation=45)

# 图表3: 交易价值 vs Gas费用
plt.subplot(2, 2, 3)
plt.scatter(transactions["value_eth"], transactions["gas_price_gwei"], color='green', alpha=0.6)
plt.title("Transaction Value vs Gas Price")
plt.xlabel("ETH Amount")
plt.ylabel("Gas Price (Gwei)")
plt.xscale('log')

# 图表4: 区块确认时间分布
plt.subplot(2, 2, 4)
plt.hist(transactions["confirmations"].astype(int), bins=15, color='purple', edgecolor='black')
plt.title("Block Confirmations Distribution")
plt.xlabel("Confirmations")
plt.ylabel("Frequency")

plt.tight_layout()
plt.savefig("eth_analysis.png", dpi=300)
plt.show()