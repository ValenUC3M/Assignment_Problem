import sys
import copy
from nodos import my_node
from queue import PriorityQueue
import time
global final, ide, total_nodes, final_node


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
            aux.append("port0")
            container_list.append(aux)
    return container_list


def modify_map(map_list):
    # this function is a bit more complex, it will adjust the map matrix to assure no flying X's create problems
    # also it will calc and return the lists with the id of the N+E type slots and E type slots
    # the for loop will read backwards the matrix, going from the bottom right to the top left,
    # being the objective to find any flying X's and set to X everything that is located upwards in the same column
    aux_col = len(map_list[0])
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
    return map_list


def calc_descendants(old, new, map_list):
    global final, ide, final_node
    # print("Calc descendants:")
    # acquire the node value to calc it's descendants
    # while not correct value keep it
    node = None
    # while we don't find a node that does not already exists in old
    while node is None and not new.empty():
        # first check if solution found
        node, new, old = search_new_node(new, old)
        # if node.state is empty we finished
        if node is not None and not node.state:
            final = True
            final_node = node
            return old, new
    # if we did fin a node the we continue, if not exit with the new empty
    if node is None:
        return old, new
    # we will check if all containers are in the boat to activate move boat protocol
    # if any found then all_in = False
    all_in = True
    # for each container in state
    for i in range(len(node.state)):
        # calc all the insertions possible in the boat regardless of the port
        # for each column in boat try insertion
        for j in range(len(node.next_cords)):
            # if container in portX we can load it
            if node.state[i][3] == node.port:
                all_in = False
                # only load if there is available space in the column
                if node.next_cords[j] is not None:
                    # try to load container
                    new, old = load_container(new, old, node, i, j, map_list)
        # if port is port1 or port2 then we need to do extra calc
        if node.port == "port1" or node.port == "port2":
            # if container not already in port
            if node.state[i][3] != "port0" and node.state[i][3] != "port1" and node.state[i][3] != "port2":
                new, old = offload(copy.deepcopy(node), new, old, i)
    # boat can navigate both ways but can't go back to port0
    # boat i
    # if all in true then create aux and try to store navigate node in new
    if all_in:
        aux = copy.deepcopy(node)
        new, old = navigate(aux, new, old)
    return old, new


def offload(node, new, old, i):
    # if cord is none its means there is no more space in the column
    if node.next_cords[node.state[i][3][0]] is None:
        # only the first container can be offloaded
        if node.state[i][3][1] == 0:
            # now we check if the offloaded is in the correct port
            # if correct port then we need to eliminate the container from list
            aux = copy.deepcopy(node)
            aux.cost += 15
            # set father's id
            aux.father = ide
            # next cords will be the location of the offloaded container
            aux.next_cords[node.state[i][3][0]] = node.state[i][3]
            # if in port then pop the data
            if node.state[i][2] == node.port[4]:
                aux.state.pop(i)
            else:
                aux.state[i][3] = aux.port
            # now calc the heuristic with the given state
            aux.heuristic = calc_heuristic(aux.state, aux.port)
            # now try to insert into new or old
            new, old = insert_check(aux, new, old)
    # we enter here to check if the container is in the more upper level available
    # not the x,0 level, the most upper right now
    else:
        # compare the state[i] values with the next_cords[j] values
        node_height = copy.deepcopy(node.state[i][3])
        # reduce in one the height value to check if its equal to the next cords value
        node_height[1] -= 1
        if node_height == node.next_cords[node.state[i][3][0]]:
            # create the new node using the original's copy
            aux = copy.deepcopy(node)
            # calc the cost having into consideration the original height
            aux.cost += 15 + 2*node.state[i][3][1]
            # set father's id
            aux.father = ide
            # next cords will be the location of the offloaded container
            aux.next_cords[node.state[i][3][0]] = node.state[i][3]
            # check if container offloaded is in the correct port
            if node.state[i][2] == node.port[4]:
                # if in port then pop the data
                aux.state.pop(i)
            # now calc the heuristic with the given state
            aux.heuristic = calc_heuristic(aux.state, aux.port)
            # now try to insert into new or old
            new, old = insert_check(aux, new, old)
    return new, old


def navigate(aux, new, old):
    # check for port, if port is 0 or 1 then upgrade 1
    aux.cost += 3500
    aux.father = ide
    # if in port 0 the create the go to port1
    if aux.port == "port0":
        aux.port = "port1"
        aux.heuristic = calc_heuristic(aux.state, aux.port)
        return insert_check(aux, new, old)
    # if in port 1 the create the go to port2
    elif aux.port == "port1":
        for i in range(len(aux.state)):
            if aux.state[i][2] == "1":
                return new, old
        aux.port = "port2"
        aux.heuristic = calc_heuristic(aux.state, aux.port)
        return insert_check(aux, new, old)
    # if in port 2 the create the go to port1 and to port0 nodes

    return new, old


def load_container(new, old, node, i, j, map_list):
    # create aux copy of node
    # only if both the slot and the container match (E) or container is N type
    if map_list[node.next_cords[j][1]][j] == node.state[i][1] or node.state[i][1] == "N":
        aux = copy.deepcopy(node)
        # set the state of i container to "in boat" with given coordinates
        aux.state[i][3] = node.next_cords[j]
        # increase cost by 10 + the deepness value
        aux.cost += 10 + node.next_cords[j][1]
        # the father is the ide value in this iteration
        aux.father = ide
        # if there are still available slots in the column change next_cords[j] deep coord value
        if node.next_cords[j][1] - 1 >= 0:
            aux.next_cords[j][1] -= 1
        else:
            # if there are not more available spaces in column, set next cords[j] to none
            aux.next_cords[j] = None
        # calc the heuristic for the new node
        aux.heuristic = calc_heuristic(aux.state, aux.port)
        # verify that there is no node with the same state
        new, old = insert_check(aux, new, old)
    return new, old


def insert_check(aux, new, old):
    global total_nodes
    found = False
    # first we check if it's on the old nodes dict
    # if found, we check the costs and if better costs then we swap them
    for key in old:
        # if state + port is equal then found and check who's better in costs
        if old[key].state == aux.state and old[key].port == aux.port:
            # if better total cost for aux then change for old
            if (old[key].cost+old[key].heuristic) > (aux.cost+aux.heuristic):
                old[key] = copy.deepcopy(aux)
            # if same cost in both nodes then the one with better heuristic wins
            elif (old[key].cost+old[key].heuristic) == (aux.cost+aux.heuristic):
                if old[key].heuristic > aux.heuristic:
                    old[key] = copy.deepcopy(aux)
            return new, old
    # if we didn't fin it in the old dict
    if not found:
        total_nodes += 1
        new.put((aux.cost + aux.heuristic, aux))
        # if not in old insert into the MutableMap new without checking if it already exists
        return new, old


def search_new_node(new, old):
    found = False
    try_node = new.get()[1]
    # pop of the try node to see if it fits
    for key in old:
        # if found we first need to check if its total value is better than the old one
        # the state + port value identifies a node
        if old[key].state == try_node.state and old[key].port == try_node.port:
            found = True
            # set found to true for later
            # now if total cost is lower in the try node change old for try node
            if (old[key].cost + old[key].heuristic) > (try_node.cost + try_node.heuristic):
                old[key] = copy.deepcopy(try_node)
            # if the have equal costs then the better heuristic wins
            elif (old[key].cost + old[key].heuristic) == (try_node.cost + try_node.heuristic):
                if old[key].heuristic > try_node.heuristic:
                    old[key] = copy.deepcopy(try_node)
    if not found:
        # if we didn't find it in old means we can use it as the father in this iteration
        node = try_node
        old[ide] = node
        return node, new, old
    return None, new, old


def calc_heuristic(state, port):
    if sys.argv[4] == "heuristic0":
        return 0
    elif sys.argv[4] == "heuristic1":
        return heuristic1(state, port)
    elif sys.argv[4] == "heuristic2":
        return heuristic2(state, port)
    else:
        print("Something went hell wrong here")


def heuristic1(state, port):
    # this heuristic is gonna check if there is any need to move to any other ports besides
    # the one in which we are right now
    # if check ports[i] == True then we will add a 3500 cost to the heuristic
    port1 = False
    port2 = False
    val = 0
    for i in range(len(state)):
        if type(state[i][3]) != str:
            val += 15 + 2 * state[i][3][1]
        else:
            val += 25
        if state[i][2] == "1":
            port1 = True
        elif state[i][2] == "2":
            port2 = True
    if port == "port0":
        if port1 and port2:
            val += 7000
        else:
            val += 3500
    elif port == "port1":
        if port2:
            val += 3500
    return val


def heuristic2(state, port):
    # this heuristic is gonna check if there is any need to move to any other ports besides
    # the one in which we are right now
    # if check ports[i] == True then we will add a 3500 cost to the heuristic
    port1 = False
    port2 = False
    val = 0
    for i in range(len(state)):
        if type(state[i][3]) != str:
            if port == "port0":
                val += 15 + 2 * state[i][3][1]
            elif port == "port1":
                val += 12 + state[i][3][1]
            else:
                val += 10
        else:
            val += 25
        if state[i][2] == "1":
            port1 = True
        elif state[i][2] == "2":
            port2 = True
    if port == "port0":
        if port1 and port2 or port2:
            val += 7000
        else:
            val += 3500
    elif port == "port1":
        if port2:
            val += 3500
    return val


def traceback(res_stack, g):
    cont = 1
    # this function needs to go back in the nodes till gets to the father and while doing it
    # needs to check what action was made to get from A to B states
    # first the father, quite simple
    node_pre = res_stack.pop()
    while res_stack:
        node_now = res_stack.pop()
        if node_pre.port != node_now.port:
            g.write(str(cont)+". Navigate (" + node_pre.port + ", " + node_now.port + ")\n")
        elif len(node_now.state) < len(node_pre.state):
            for i in range(len(node_pre.state)):
                if node_pre.state[i] not in node_now.state:
                    g.write(str(cont) + ". Deliver (Container" + node_pre.state[i][0] + ", " + node_pre.port + ")\n")
        else:
            container = None
            for i in range(len(node_pre.state)):
                if node_now.state[i] not in node_pre.state:
                    container = node_now.state[i]
                    break
            if type(container[3]) == list:
                g.write(str(cont) + ". Load (Container" + container[0] + ", Location in boat: " + str(container[3]) + ", In: " + node_now.port + ")\n")
            else:
                g.write(str(cont) + ". Offload (Container" + container[0] + ", En:" + container[3] + ")\n")
        node_pre = node_now
        cont += 1
    g.close()


def stats_creator(f, total_time, total_cost, plan_length, total_expanded):
    f.write("Total time: " + str(total_time) + "\n")
    f.write("Total cost: " + str(total_cost) + "\n")
    f.write("Plan length: " + str(plan_length) + "\n")
    f.write("Expanded nodes: " + str(total_expanded) + "\n")
    f.close()


def main():
    start_timer = time.time()
    global ide, final
    global total_nodes
    # check if number of parameters is valid
    if len(sys.argv) != 5:
        print("Invalid amount of parameters")
        return -1
    total_nodes = 0
    # load the path where the map and container files are stored
    problem_data_path = sys.argv[1]
    # load the map file name
    problem_map = sys.argv[2]
    # load de container file name
    problem_container_data = sys.argv[3]
    # check if heuristic is valid
    if sys.argv[4] != "heuristic1":
        if sys.argv[4] != "heuristic2":
            if sys.argv[4] != "heuristic0":
                print("Error: Invalid heuristic given")
                return -1
    # main problem declaration
    # calc the map list and store it in a matrix
    map_list = calc_map(problem_data_path, problem_map)
    # calc the container list and store it in a matrix
    container_list = calc_containers(problem_data_path, problem_container_data)
    # aux data needed for different settings [map_list, refrigerated, all_containers]
    map_list = modify_map(map_list)
    # set the updated map list
    # next steps will be the id to know where you can still put containers
    next_steps = []
    # get the next steps ids
    for i in range(len(map_list[0])):
        # for loops to read columns
        found = False
        for j in range(len(map_list)):
            # first try to find a non x space
            if map_list[j][i] != "X" and not found:
                found = True
            # when found, search for the floor, when floor found establish the next_steps[i] value
            elif found and map_list[j][i] == "X" and len(next_steps) <= i:
                next_steps.append([i, j-1])
        # if none found then assign empty space (maybe column is full of X's)
        if len(next_steps) <= i:
            next_steps.append(None)

    # the first node is created using base parameters and located in the port0
    # we define our MutableMapping ABC using heapdict
    new = PriorityQueue()
    # now we create our root node
    # define the first heuristic value for root
    heuristic = calc_heuristic(container_list, "port0")
    new.put((0 + heuristic, my_node(container_list, 0, "root", next_steps, heuristic, "port0")))
    # in old we will store the already found and read nodes
    old = {}
    # we use the global id no know the number assignment for the parent value of every new node
    ide = 0
    # final will be true when we find a state that is container empty and has the best total cost of all the new+old nodes
    final = False
    # while is now using len(new) for testing
    # define the control variable for the new length using the new.items data
    while final == False and not new.empty():
        # calc descendants and return the new values for "new" and "old"
        old, new = calc_descendants(old, new, map_list)
        # increase ide value in 1 for the next father id
        ide += 1

    end_timer = time.time()
    total_time = end_timer-start_timer
    # we will store the results to extract the in order later
    res_stack = []
    if new.empty() and final == False:
        print("no solution found")
        return -1
    else:
        end = None
        # insert first the final state
        res_stack.append(final_node)
        node = final_node
        while end is None:
            node = old[node.father]
            res_stack.append(node)
            if node.father == "root":
                end = node
    # write in the output file the solution stats
    f = open("./ASTAR-tests/" + problem_map + "-" + problem_container_data + "-" + sys.argv[4] + ".stat", "a")
    # now create the stats file with all the stats in it
    stats_creator(f, total_time, final_node.cost, len(res_stack), total_nodes)
    # now create the file with the traceback route of the actions done
    g = open("./ASTAR-tests/" + problem_map + "-" + problem_container_data + "-" + sys.argv[4] + ".output", "a")
    traceback(res_stack, g)
    return 0


main()
