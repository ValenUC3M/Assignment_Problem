from constraint import *
import sys


def not_equal(*args):
    for i in range(len(args)):
        # for every argument given, calc if valid data
        for j in range(i+1, len(args)):
            # compare data in arg[i] with data in arg[j]
            if i != j and args[i] == args[j]:
                # if equal data, the false
                return False
    return True


def in_order(*args):
    # we need the container list to get an aux array with the port data
    # since both arrays (args and container) have the same order we don't need to modify any of them to do the calc
    container_list = calc_containers(sys.argv[1], sys.argv[3])
    for i in range(len(args)):
        # for every container check if order is clear
        for j in range(len(args)):
            # if both are located in the same column
            if i != j and args[i][0] == args[j][0]:
                # check for port id and proceed
                # if both have the same port, it doesn't matter the order
                if container_list[i][2] < container_list[j][2]:
                    # check order based on port id
                    # if i has higher placing then j it's all fine
                    if args[i][1] > args[j][1]:
                        return False

                elif container_list[i][2] > container_list[j][2]:
                    # check order based on port id
                    # if i has lower placing then j it's all fine
                    if args[i][1] < args[j][1]:
                        return False

    return True


def not_flying(*args):
    # no need to update map because domains don't take invalid positions anyway
    map_list = calc_map(sys.argv[1], sys.argv[2])
    for i in range(len(args)):
        # control variable for checking if valid data is given
        verify = False
        # for every argument given, calc if valid data
        for j in range(len(args)):
            # compare data in arg[i] with data in arg[j]
            # if not in the same column, ignore it
            if i != j and args[i][0] == args[j][0]:
                if args[j][1]-1 == args[i][1]:
                    verify = True
                elif map_list[args[i][1]+1][args[i][0]] == "X":
                    verify = True
            elif map_list[args[i][1] + 1][args[i][0]] == "X":
                verify = True
        if not verify:
            return False
    return True


def calc_map(problem_data_path, problem_map):
    map_list = []
    # set map list for latter use in add variable / add constraint protocols
    with open(problem_data_path+"/"+problem_map) as data_file:
        # once the file is open, read it
        for line in data_file:
            # use aux to create the matrix
            aux_map_list = []
            for i in line:
                # only accept data different from blanc or \n
                if i != " " and i != "\n":
                    aux_map_list.append(i)
            # once row is calc, append it to matrix
            map_list.append(aux_map_list)
    return map_list


def calc_containers(problem_data_path, problem_container_data):
    container_list = []
    # set container list for latter use in add variable / add constraint protocols
    with open(problem_data_path+"/"+problem_container_data) as data_file:
        # once the file is open, read it
        for line in data_file:
            # again create a matrix with the data of one container in every row
            aux = []
            aux2 = ""
            # now we need a second aux array to store
            for i in range(len(line)):
                # for latter use, set S and R data to N and E data types
                if line[i] == "S":
                    aux2 = "N"
                elif line[i] == "R":
                    aux2 = "E"
                elif line[i] == " ":
                    aux.append(aux2)
                    aux2 = ""
                elif line[i] == "\n" and aux2 != "":
                    aux.append(aux2)
                    aux2 = ""
                else:
                    aux2 = aux2 + line[i]
            # once row is read, append it to the matrix
            if aux2 != "":
                aux.append(aux2)
            container_list.append(aux)
    return container_list


def modify_map(map_list):
    # this function is a bit more complex, it will adjust the map matrix to assure no flying X's create problems
    # also it will calc and return the lists with the id of the N+E type slots and E type slots
    # the for loop will read backwards the matrix, going from the bottom right to the top left,
    # being the objective to find any flying X's and set to X everything that is located upwards in the same column
    aux_col = len(map_list[0])
    refrigerated = []
    all_containers = []
    # arrays created for later use in set variable / constraints protocols
    for i in range(aux_col):
        # for the algorithm to work we need to set to false both control vars
        container_found = False
        flying_x_found = False
        aux_col -= 1
        aux_row = len(map_list)
        # read from every column, each row
        for j in range(aux_row):
            aux_row -= 1
            if flying_x_found:
                map_list[aux_row][aux_col] = "X"
            else:
                if container_found:
                    if map_list[aux_row][aux_col] == "X":
                        flying_x_found = True
                else:
                    if map_list[aux_row][aux_col] != "X":
                        container_found = True
            # once the new value is calc, we set it on the respective vector if needed
            # we need to set and id for the new container in the respective vector
            if map_list[aux_row][aux_col] == "E":
                refrigerated.append([aux_col, aux_row])
                all_containers.append([aux_col, aux_row])
            elif map_list[aux_row][aux_col] == "N":
                all_containers.append([aux_col, aux_row])
    return [map_list, refrigerated, all_containers]


def set_variable_domains(container_list, refrigerated, all_containers, problem):
    var_list = []
    # var list used for later constraint set
    for i in container_list:
        # add always to the var list and only if true to the other lists
        var_list.append(i[0])
        if i[1] == "N":
            try:
                problem.addVariable(i[0], all_containers)
            except:
                return 0
        elif i[1] == "E":
            try:
                problem.addVariable(i[0], refrigerated)
            except:
                return 0
    return tuple(var_list)


def find_tough_solution(problem, var_list):
    problem.addConstraint(in_order, var_list)
    return problem.getSolutions()


def write_data(f, solution, var_list):
    f.write("Numero de soluciones: " + str(len(solution)) + "\n")
    # now lets write line by line the solutions found
    for data in solution:
        aux = "{"
        for i in range(len(var_list)):
            aux += var_list[i][0] + ":" + "(" + str(data[var_list[i][0]][0]) + "," + str(data[var_list[i][0]][0]) + "),"
        aux = aux[:len(aux) - 1] + "}\n"
        f.write(aux)


def main():
    if (len(sys.argv)) != 4:
        print("Invalid parameters")
        return -1
    # load the path where the map and container files are stored
    problem_data_path = sys.argv[1]
    # load the map file name
    problem_map = sys.argv[2]
    # load de container file name
    problem_container_data = sys.argv[3]
    # main problem declaration
    problem = Problem()
    # calc the map list and store it in a matrix
    map_list = calc_map(problem_data_path, problem_map)
    # calc the container list and store it in a matrix
    container_list = calc_containers(problem_data_path, problem_container_data)
    # aux data needed for different settings [map_list, refrigerated, all_containers]
    data = modify_map(map_list)
    # set the updated map list
    map_list = data[0]
    # calc the var list and set the variables with their domains
    var_list = set_variable_domains(container_list, data[1], data[2], problem)
    # check if domains where rightly settled
    if var_list == 0:
        print("Error in problem")
        return -1
    # add not equal constraint to the problem
    problem.addConstraint(not_equal, var_list)
    # add not flying objects constraint to the problem
    problem.addConstraint(not_flying, var_list)
    # now lets try to see if the problem can be solved with the order constraint
    solution = problem.getSolutions()
    if solution is not None:
        f = open("./CSP-tests/" + problem_map + "-" + problem_container_data + ".output", "a")
        solution2 = find_tough_solution(problem, var_list)
        if solution2 is not None:
            f.write("Ordered solution: \n")
            write_data(f, solution2, var_list)
        f.write("Relaxed solution: \n")
        write_data(f, solution, var_list)
        # first create the output file
        # write the total amount of solutions in it
        # now lets write line by line the solutions found
        f.close()
    else:
        print(solution)
        print("No solution found")
        return -1
    return 0


main()
