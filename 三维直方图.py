liquidity_matrix = np.histogramdd(
    samples=[[d['timestamp']%86400 for d in raw_data],
             [d['price'] for d in raw_data]],
    bins=[time_bins, price_bins],
    weights=[d['amount'] for d in raw_data]
)[0]