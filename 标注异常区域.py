anomaly_mask = (smoothed_matrix < np.percentile(smoothed_matrix, 10))
ax.scatter(T[anomaly_mask], P[anomaly_mask],
          smoothed_matrix[anomaly_mask],
          c='red', s=50, marker='o')