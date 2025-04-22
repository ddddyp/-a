from scipy.ndimage import gaussian_filter
smoothed_matrix = gaussian_filter(liquidity_matrix, sigma=1.5)