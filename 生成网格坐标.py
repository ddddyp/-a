time_axis = np.arange(len(time_bins))
price_axis = np.arange(len(price_bins))
T, P = np.meshgrid(time_axis, price_axis, indexing='ij')