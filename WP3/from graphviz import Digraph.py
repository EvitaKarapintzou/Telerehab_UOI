from graphviz import Digraph

# Create a new directed graph with left-to-right rank direction
dot = Digraph(comment='Yaw Angle Calculation', format='png')
dot.attr(rankdir='LR', size='12,8')  # Left-to-right direction with a fixed size

# Define node attributes with larger font
box_attrs = {'shape': 'box', 'style': 'rounded,filled', 'color': '#e0e0e0', 'fontname': 'Helvetica', 'fontsize': '14'}

# Add nodes (boxes) to the graph with detailed labels
dot.node('A', 'Euler angles\nE(y, p, r, t)', **box_attrs)
dot.node('B', 'Measurement in\npitch plane\nP(t)', **box_attrs)
dot.node('C', 'Values pre-\nprocessing\n(normalization)\n\nP\'(t)\n(full circles elimination\nzero normalization)', **box_attrs)
dot.node('D', 'Low pass filter\nH(P\'(s)) = wc / (s + wc)', **box_attrs)
dot.node('E', '1st derivative\ndP\'(t)/dt', **box_attrs)
dot.node('F', 'Local extrema\ndP\'(t)/dt = 0', **box_attrs)
dot.node('G', 'Outliers\nelimination', **box_attrs)
dot.node('H', 'min - max\npairing', **box_attrs)
dot.node('I', 'metric calculation\n(range, time,\nvariation, mean)', **box_attrs)

# Add edges (arrows) between nodes
dot.edge('A', 'B')
dot.edge('B', 'C')
dot.edge('C', 'D')
dot.edge('D', 'E')
dot.edge('E', 'F')
dot.edge('F', 'G')
dot.edge('G', 'H')
dot.edge('H', 'I')

# Save and render the graph
dot.render('yaw_angle_calculation_horizontal_flowchart', format='png', view=True)
