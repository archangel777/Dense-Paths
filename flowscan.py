import sys
import time
import datetime

def inter(l1, l2):
	return list(filter(lambda x: x in l2, l1))

class Graph:

	def __init__(self):
		self.nodes = self.load_nodes()
		self.edges = self.load_edges()
		self.inv_nodes = self.get_inverted_dict(self.nodes)
		self.inv_edges = self.get_inverted_dict(self.edges)
		self.forward_hops = self.get_forward_hops()
		self.backward_hops = self.get_backward_hops()

	def load_nodes(self):
		with open('beijing_data/table_vertices.csv', 'r') as f:
			return {int(line.split(';')[0]) : (float(line.split(';')[2]), float(line.split(';')[1])) for line in f.readlines()}

	def load_edges(self):
		with open('beijing_data/beijing_fixed.csv', 'r') as f:
			return {int(line.split(';')[0]) : (int(line.split(';')[1]), int(line.split(';')[2])) for line in f.readlines()}

	def get_forward_hops(self):
		hops = {node_id: [] for node_id in self.nodes}
		for edge in self.edges.values():
			hops[edge[0]].append(edge[1])
		return hops

	def get_backward_hops(self):
		hops = {node_id: [] for node_id in self.nodes}
		for edge in self.edges.values():
			hops[edge[1]].append(edge[0])
		return hops

	def get_inverted_dict(self, dic):
		return {value: key for key, value in dic.items()}

	def get_node_id(self, lat, lng):
		return self.inv_nodes[(lat, lng)]

	def get_edge_id(self, from_id, to_id):
		return self.inv_edges[(from_id, to_id)]

	def get_neighborhood(self, edge_id, eps):
		neighbors = []
		x = [edge_id]
		for i in range(eps):
			aux = [self.get_successors(e_id) for e_id in x]
			x = [e_id for y in aux for e_id in y]
			neighbors += x
		return neighbors

	def get_successors(self, edge_id):
		return [self.inv_edges[(self.edges[edge_id][1], node_id)] for node_id in self.forward_hops[self.edges[edge_id][1]]]

	def get_predecessors(self, edge_id):
		return [self.inv_edges[(node_id, self.edges[edge_id][0])] for node_id in self.backward_hops[self.edges[edge_id][0]]]

class Flowscan:

	def __init__(self, min_traffic, eps):
		self.runtimes = {
			'get_edge_to_trajectory_dict': [],
			'get_hot_starts': [],
			'is_directly_traffic_reachable': [],
			'is_traffic_reachable': [],
			'run': [],
			'extend_hot_route': [],
			'save_hot_routes': []
		}
		t_i = time.time()
		self.graph = Graph()
		self.min_traffic = min_traffic
		self.eps = eps
		self.runtimes['graph_initialization'] = [time.time() - t_i]

	def set_timewindow(self, timewindow):
		filename = 'data/clean_inputs_8-9/clear_' + str(timewindow) + '.csv'
		self.setup(filename)

	def setup(self, filename):
		t_i = time.time()
		self.trajectories = self.get_trajectory(filename)
		self.e_to_traj = self.get_edge_to_trajectory_dict()
		self.densities = self.get_density_dict()
		self.runtimes['flowscan_initialization'] = [time.time() - t_i]

	def print_runtimes(self):
		for func in sorted(self.runtimes):
			print(func + '.'*(40-len(func)) + 'avg: %.4f s'%(sum(self.runtimes[func])/len(self.runtimes[func])) + '  ...... total: %.4f s'%(sum(self.runtimes[func])))
		print('-'*60)
	
	def get_density_dict(self):
		return {e_id: len(self.e_to_traj[e_id]) for e_id in self.graph.edges}

	def get_trajectory(self, filename):
		with open(filename, 'r') as f:
			d = {int(line.split(';')[0]) : [float(x) for x in line.split(';')[1:]] for line in f.readlines() if len(line.split(';')) >= 5}
		return {key : [self.graph.get_edge_id(self.graph.get_node_id(value[2*i], value[2*i+1]), self.graph.get_node_id(value[2*(i+1)], value[2*(i+1)+1])) for i in range(int(len(value)/2) - 1)] for key, value in d.items()}

	def get_neighborhood(self, e):
		return self.graph.get_neighborhood(e, self.eps)

	def get_edge_to_trajectory_dict(self):
		t_i = time.time()
		e_to_traj = {e_id: [] for e_id in self.graph.edges}
		for t in self.trajectories:
			for e in self.trajectories[t]:
				if t not in e_to_traj[e]:
					e_to_traj[e].append(t)
		self.runtimes['get_edge_to_trajectory_dict'].append(time.time() - t_i)
		return e_to_traj

	def get_hot_starts(self):
		t_i = time.time()
		hot_starts = []
		for e in self.graph.edges:
			prev_union = set()
			for predecessor in self.graph.get_predecessors(e):
				if predecessor in self.densities and self.densities[predecessor] >= self.min_traffic:
					prev_union = prev_union.union(self.e_to_traj[predecessor])
			if len([t for t in self.e_to_traj[e] if t not in prev_union]) >= self.min_traffic:
				hot_starts.append(e)
		self.runtimes['get_hot_starts'].append(time.time() - t_i)
		return hot_starts

	def is_directly_traffic_reachable(self, r, s):
		t_i = time.time()
		res = s in self.get_neighborhood(r) and len(inter(self.e_to_traj[r], self.e_to_traj[s])) >= self.min_traffic
		self.runtimes['is_directly_traffic_reachable'].append(time.time() - t_i)
		return res

	def is_traffic_reachable(self, traj, edge):
		t_i = time.time()
		new_traj = traj + [edge]
		to_check = new_traj[-self.eps:]
		x = self.e_to_traj[edge]
		for l in to_check: x = inter(x, self.e_to_traj[l])
		self.runtimes['is_traffic_reachable'].append(time.time() - t_i)
		return len(x) >= self.min_traffic

	def extend_hot_route(self, r, log_time = True):
		t_i = time.time()
		p = r[-1]
		Q = [neigh for neigh in self.graph.get_successors(p) if self.is_directly_traffic_reachable(p, neigh) and neigh not in r]
		if Q:
			res = []
			for splt in Q:
				if self.is_traffic_reachable(r, splt):
					res += self.extend_hot_route(list(r) + [splt], False)
		else:
			res = [r]
		if log_time: self.runtimes['extend_hot_route'].append(time.time() - t_i)
		return res

	def run(self):
		t_i = time.time()
		R = []
		H = self.get_hot_starts()
		for h in H:
			r = [h]
			R += self.extend_hot_route(r)
		self.runtimes['run'].append(time.time() - t_i)
		return R

	def save_hot_routes(self, hot_routes, timewindow, for_george = True):
		t_i = time.time()
		path = 'outputs/hot_routes/hot_routes_' + str(timewindow) + '.csv'
		with open(path, 'w') as f:
			_id = 0
			for route in hot_routes:
				_id += 1
				if len(route) >= 2:
					if not for_george:
						f.write(str(_id))
					for e in route:
						lat = self.graph.nodes[self.graph.edges[e][0]][0]
						lng = self.graph.nodes[self.graph.edges[e][0]][1]
						if for_george:
							f.write(str(_id))
						f.write(';' + str(lat) + ';' + str(lng))
						if for_george:
							f.write('\n')
					lat = self.graph.nodes[self.graph.edges[route[-1]][1]][0]
					lng = self.graph.nodes[self.graph.edges[route[-1]][1]][1]
					if for_george:
						f.write(str(_id))
					f.write(';' + str(lat) + ';' + str(lng) + '\n')
		self.runtimes['save_hot_routes'].append(time.time() - t_i)




MIN_TRAFFIC = 10
EPS = 3
flowscan = Flowscan(MIN_TRAFFIC, EPS)

for timewindow in range(6):

	flowscan.set_timewindow(timewindow)

	res = flowscan.run()

	flowscan.save_hot_routes(res, timewindow, False)

	#flowscan.print_runtimes()
	print('%.4f s'%flowscan.runtimes['run'][timewindow])
