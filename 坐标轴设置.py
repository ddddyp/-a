ax.set_xticks(np.linspace(0, len(time_bins), 6))
ax.set_xticklabels([f"{int(t/3600):02d}:00" for t in np.linspace(0,86400,6)])
ax.set_yticks(np.linspace(0, len(price_bins), 5))
ax.set_yticklabels(np.linspace(price_bins[0], price_bins[-1],5).astype(int))
ax.set_zlabel('流动性深度 (ETH)')

plt.colorbar(surf, shrink=0.5, aspect=10)
plt.show()
