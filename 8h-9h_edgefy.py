import sys
prefix = 'data/clean_inputs_8-9/'
edge_prefix = 'data/edge_inputs_8-9/'
edges = {}
print('       ]', end='\r[')
for i in range(6):
    print('#', sep=' ', end='')
    sys.stdout.flush()
    filename = 'clear_' + str(i) + '.csv'
    with open(prefix + filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            coord = line.split(';')
            for j in range(1, int(len(coord)/2) - 1):
                key = coord[2*j-1] + ';' + coord[2*j] + ';' + coord[2*j+1] + ';' + coord[2*j+2]
                if (key in edges):
                    edges[key] += 1
                else:
                    edges[key] = 1
    with open(edge_prefix + 'edges_' + str(i) + '.csv', 'a') as f:
        for _id, key in zip(range(len(edges)), edges):
            f.write(str(_id) + ';' + key + ';' + str(edges[key]) + '\n')
    for x in edges:
        edges[x] = 0;
