import datetime
prefix = 'data/inputs/'
clean_prefix = 'data/clean_inputs_8-9/'


filename = 'output_8.csv'
print('filename: ', filename)
with open(prefix + filename, 'r') as f:
    lines = f.readlines()
    for i in range(6):
        result = []
        bot_date = datetime.datetime.strptime('04/02/2008 08:' + str(i*10) + ':00', "%d/%m/%Y %H:%M:%S").timestamp()
        top_date = datetime.datetime.strptime('04/02/2008 08:' + str(i*10 + 9) + ':59', "%d/%m/%Y %H:%M:%S").timestamp()
        print(str(bot_date) + "|" + str(top_date))
        prev_id = None
        for j in range(1, len(lines)):
            data_line = lines[j].split(';')      
            if int(data_line[3])/1000 >= bot_date and int(data_line[3])/1000 <= top_date:
                new_id = data_line[0]
                if (new_id != prev_id):
                    coordinates_list = [new_id]
                    result.append(coordinates_list)
                prev_id = new_id
                coordinates_list.append(data_line[1])
                coordinates_list.append(data_line[2])
        print(result[0])
        output_filename = 'clear_' + str(i) + '.csv'
        with open(clean_prefix + output_filename, 'a') as f:
            for line in result:
                f.write(';'.join(line))
                f.write('\n')
