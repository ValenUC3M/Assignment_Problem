class my_node:

    def __init__(self, state, cost, father, next_cords, heuristic, port):
        self.state = state
        self.cost = cost
        self.father = father
        self.next_cords = next_cords
        self.heuristic = heuristic
        self.port = port

    def __str__(self):
        var = ("Objeto:\n" + str(self.state)) + "\nCost: " + str(self.cost) + ", " + str(self.heuristic) \
              + "\nFather id: " + str(self.father) + "\nNext cords: " + str(self.next_cords) + "\nPort: " + self.port+"\n"
        return var

    def __gt__(self, other):
        return self.heuristic > other.heuristic

    def __lt__(self, other):
        return self.heuristic < other.heuristic
