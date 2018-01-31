prefix = 'data/inputs/'
clean_prefix = 'data/clean_inputs/'
for i in range(1):
    #filename = 'output_' + str(i) + '.csv'
    filename = 'timewindow0.csv'
    print('filename: ', filename)
    result = []
    with open(prefix + filename, 'r') as f:
        lines = f.readlines()
        prev_id = None
        for j in range(1, len(lines)):
            data_line = lines[j].split(';')
            new_id = data_line[0]
            if (new_id != prev_id):
                coordinates_list = [new_id]
                result.append(coordinates_list)
            prev_id = new_id
            coordinates_list.append(data_line[1])
            coordinates_list.append(data_line[2])
    print(result[0])
    output_filename = 'clear_' + filename
    with open(clean_prefix + output_filename, 'a') as f:
        for line in result:
            f.write(';'.join(line))
            f.write('\n')
