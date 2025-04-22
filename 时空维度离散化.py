time_bins = pd.interval_range(start=0, end=86400, freq=300)  # 5分钟时间窗
price_bins = np.arange(2400, 2600, 2)  # 2美元价格区间