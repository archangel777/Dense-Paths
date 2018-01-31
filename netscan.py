import matplotlib.pyplot as plt
import sys
import time
import datetime

class Node:

	def __init__(self, lat, lng):
		self.lat = lat
		self.lng = lng

	def __str__(self):
		return str(self.__dict__)

	def __eq__(self, other): 
		return self.__dict__ == other.__dict__

	def __hash__(self):
		return hash(str(self))

class Edge:

	def __init__(self, _id, f, t, density):
		self.id = _id
		self.f = f
		self.t = t
		self.density = density

def get_edge_list(prefix, filename):
	edge_list = []

	with open(prefix + filename, 'r') as f:
		lines = f.readlines()
		
	for line in lines:
		splt = line.split(';')
		edge_list.append(
			Edge(splt[0], 							# id
			Node(float(splt[1]), float(splt[2])), 	# from
			Node(float(splt[3]), float(splt[4])), 	# to
			int(splt[5])) 							# density
		) 

	return edge_list

def plot_densities(all_edges):
	for i in range(6):
		densities = sorted([edge.density for edge in all_edges[i]], reverse=True)
		aux = 230 + i + 1
		plt.subplot(aux)
		plt.plot(densities)
		plt.title('08:' + '%02i' % (i*10) + ':00 to 08:' + '%02i' % (i*10+9) + ':59')

	plt.show()

def get_all_edges(prefix, make_plot=False):
	all_edges = []

	plt.figure(1)

	for i in range(6):
		filename = 'edges_' + str(i) + '.csv'

		edge_list = get_edge_list(prefix, filename)

		all_edges.append(edge_list)

	if make_plot: plot_densities(all_edges)

	return all_edges

def how_many_edges(densities, threashold):
	print(len([x for x in densities if x >= threashold]))

#how_many_edges(densities, 30)

def get_nodes(all_edges):
	nodes = []
	for l in all_edges:
		for edge in l: nodes += [edge.f, edge.t]

	nodes = dict((str(obj.lat) +'|'+ str(obj.lng), obj) for obj in nodes).values()

	print(len(nodes))

def get_node_dict():
	with open('beijing_data/table_vertices.csv') as f:
		return {int(line.split(';')[0]) : Node(float(line.split(';')[2]), float(line.split(';')[1])) for line in f.readlines()}

def get_velocities():
	node_dict = get_node_dict()
	with open('beijing_data/roads_velocity.csv') as f:
		return {(node_dict[int(line.split(';')[1])], node_dict[int(line.split(';')[2])]) : int(line.split(';')[3]) for line in f.readlines()[1:]}

# -----------------------------------------------------------------------

def find_max_edge(M):
	if not M: return None
	return max(M.keys(), key=lambda key: M[key])

def find_max_forward(M, node, prev_val, max_diff):
	l = {key: value for (key, value) in M.items() if key[0] == node and abs(M[key] - prev_val) <= max_diff}
	if not l: return None
	return min(l.keys(), key=lambda key: abs(M[key] - prev_val))

def find_max_backward(M, node, prev_val, max_diff):
	l = {key: value for (key, value) in M.items() if key[1] == node and abs(M[key] - prev_val) <= max_diff}
	if not l: return None
	return min(l.keys(), key=lambda key: abs(M[key] - prev_val))

def netscan(e_list, max_diff, min_dens, saving_directory, for_george=False):
	t_ = time.time()
	traj_list = []
	k = 0
	M = {}
	for e in e_list:
		if e.density >= min_dens:
			M[(e.f, e.t)] = e.density
	
	while True:
		# condition ---------------------------------
		max_edge = find_max_edge(M)
		if not max_edge: break
		# -------------------------------------------

		k += 1
		traj = [max_edge]
		start_value = M[max_edge]
		del M[max_edge]
		d = max_edge[0]
		f = max_edge[1]

		# forward extension ----------------
		prev_val = start_value
		while True:
			better_forward = find_max_forward(M, f, prev_val, max_diff)
			if not better_forward:
				break

			traj.append(better_forward)
			prev_val = M[better_forward]
			del M[better_forward]
			d = better_forward[0]
			f = better_forward[1]

		d = max_edge[0]
		f = max_edge[1]

		# backward extension ----------------
		prev_val = start_value
		while True:
			better_backward = find_max_backward(M, d, prev_val, max_diff)
			if not better_backward:
				break

			traj.insert(0, better_backward)
			prev_val = M[better_backward]
			del M[better_backward]
			d = better_backward[0]
			f = better_backward[1]

		traj_list.append(traj)

	print("%.4f"%((time.time() - t_)) + ' s')

	#--------------------------------------------------------------
	# Save trajectory list
	save_trajectories(traj_list, saving_directory, for_george)

	

def save_trajectories(traj_list, saving_directory, for_george):
	velocities = get_velocities()
	with open(saving_directory, 'w') as f:
		id_ = 0
		for traj in traj_list:
			if len(traj) > 0:
				if not for_george:
					f.write(str(id_))
				for x in traj:
					node_lat = x[0].lat
					node_lng = x[0].lng
					if for_george:
						f.write(str(id_))
					
					f.write( ';' + str(node_lat) + ';' + str(node_lng) )

					if for_george:
						f.write(';' + str(velocities[(x[0], x[1])]) + '\n')
				node_lat = traj[-1][1].lat
				node_lng = traj[-1][1].lng
				if for_george:
					f.write(str(id_))

				f.write( ';' + str(node_lat) + ';' + str(node_lng) )
				
				if for_george:
					f.write(';' + str(velocities[(traj[-1][0], traj[-1][1])]))

				f.write('\n')
			id_ += 1

def run_time_intervals(for_george=False):
	all_edges = get_all_edges('data/edge_inputs_8-9/')
	MIN_DENS = 10
	MAX_DIFF = 10
		
	for i in range(6):
		netscan(all_edges[i], MAX_DIFF, MIN_DENS, 'outputs/trajectories_8-9/traj_' + str(i) + '.csv', for_george)


def run_whole_hour(for_george=False):
	edge_list = get_edge_list('data/edge_inputs/','edges_8.csv')
	MIN_DENS = 50
	MAX_DIFF = 50

	netscan(edge_list, MIN_DENS, MAX_DIFF, 'outputs/trajectories_8-9/whole_hour.csv', for_george)

run_time_intervals()
# run_whole_hour()