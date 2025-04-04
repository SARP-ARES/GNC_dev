t(p[0], p[1], 'ro', label='Current Position') # current position
plt.plot(0,0, 'bo', markerfacecolor='none', markeredgewidth=2, label='Target (Launch Pad)')
plt.plot([p[0], 0], [p[1], 0], 'm--', label='Target Heading')
plt.plot(