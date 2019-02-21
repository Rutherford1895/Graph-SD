import networkx as nx
import matplotlib.pyplot as plt


# define functions
def linear(x, a=1, b=0):
    return a * float(x) + b


def subtract(x, y):
    return float(x) - float(y)


def division(x, y):
    return float(x) / float(y)


# define constants
STOCK = 'stock'
FLOW = 'flow'
VARIABLE = 'variable'
PARAMETER = 'parameter'
LINEAR = linear
SUBTRACT = subtract
DIVISION = division


class Structure(object):
    def __init__(self):
        self.sfd = nx.MultiDiGraph()

    def add_element(self, element_name, element_type, function=None, value=None):
        # this 'function' is a list, containing the function it self and its parameters
        # this 'value' is also a list, containing historical value throughout this simulation
        self.sfd.add_node(element_name, element_type=element_type, function=function, value=value)

    def add_causality(self, from_element, to_element):
        self.sfd.add_edge(from_element, to_element)

    def display_elements(self):
        print('All elements in this SFD:')
        print(self.sfd.nodes.data())

    def display_element(self, name):
        print('Attributes of element {}:'.format(name))
        print(self.sfd.nodes[name])

    def display_causalities(self):
        print('All causalities in this SFD:')
        print(self.sfd.edges)

    def display_causality(self, from_element, to_element):
        print('Causality from {} to {}:'.format(from_element, to_element))
        print(self.sfd[from_element][to_element])

    # The core function for simulation, based on recursion
    def calculate(self, name):
        if self.sfd.nodes[name]['element_type'] == STOCK:
            # if the node is a stock
            return self.sfd.nodes[name]['value'][-1]  # just return its value, update afterward.
        elif self.sfd.nodes[name]['function'] is None:
            # if the node does not have a function and not a stock, then it's constant
            # if this node is a constant, still extend its value list by its last value
            self.sfd.nodes[name]['value'].append(self.sfd.nodes[name]['value'][-1])
            return self.sfd.nodes[name]['value'][-1]  # use its latest value
        else:  # it's not a constant value but a function  #
            params = self.sfd.nodes[name]['function'][1:]  # extract all parameters needed by this function
            for j in range(len(params)):  # use recursion to find the values of params, then -
                params[j] = self.calculate(params[j])  # replace the param's name with its value.
            new_value = self.sfd.nodes[name]['function'][0](*params)  # calculate the new value for this step
            self.sfd.nodes[name]['value'].append(new_value)  # add this new value to this node's value list
            return new_value  # return the new value to where it was called

    def step(self, dt=0.25):
        flows_dt = dict()  # have a dictionary of flows and their values in this dt, to be added to stocks afterward.

        # find all flows in the model
        for element in self.sfd.nodes:  # loop through all elements in this SFD,
            if self.sfd.nodes[element]['element_type'] == FLOW:  # if this element is a FLOW --
                flows_dt[element] = 0  # make a position for it in the dict of flows_dt, initializing it with 0

        # calculate flows
        for flow in flows_dt.keys():
            flows_dt[flow] = dt * self.calculate(flow)
        print('All flows dt:', flows_dt)

        # calculating changes in stocks
        # have a dictionary of affected stocks and their changes, for one flow could affect 2 stocks.
        affected_stocks = dict()
        for flow in flows_dt.keys():
            successors = list(self.sfd.successors(flow))  # successors of a flow into a list
            print('Successors of {}: '.format(flow), successors)
            for successor in successors:
                if self.sfd.nodes[successor]['element_type'] == STOCK:  # flow may also affect elements other than stock
                    if successor not in affected_stocks.keys():  # if this flow hasn't been calculated, create a new key
                        affected_stocks[successor] = flows_dt[flow]
                    else:  # otherwise update this flow's value on top of results of previous calculation (f2 = f1 + f0)
                        affected_stocks[successor] += flows_dt[flow]

        # updating stocks values
        for stock in affected_stocks.keys():
            # calculate the new value for this stock and add it to the end of its value list
            self.sfd.nodes[stock]['value'].append(self.sfd.nodes[stock]['value'][-1] + affected_stocks[stock])


class Session(object):
    def __init__(self):
        self.simulation_time = 13
        self.dt = 0.25
        self.structures = dict()
        self.add_structure()

    def add_structure(self, structure_name='default'):
        self.structures[structure_name] = Structure()

    # Set the model to a first order negative feedback loop
    def first_order_negative(self, structure_name='default'):
        self.structures[structure_name].add_element('stock0', STOCK, value=[100])
        self.structures[structure_name].add_element('flow0', FLOW, function=[DIVISION, 'gap0', 'at0'], value=list())
        self.structures[structure_name].add_causality('flow0', 'stock0')

        self.structures[structure_name].add_element('goal0', PARAMETER, value=[20])
        self.structures[structure_name].add_element('gap0', VARIABLE, function=[SUBTRACT, 'goal0', 'stock0'], value=list())
        self.structures[structure_name].add_causality('stock0', 'gap0')
        self.structures[structure_name].add_causality('goal0', 'gap0')

        self.structures[structure_name].add_element('at0', PARAMETER, value=[5])
        self.structures[structure_name].add_causality('gap0', 'flow0')
        self.structures[structure_name].add_causality('at0', 'flow0')

    def simulate(self, structure_name='default', simulation_time=13, dt=0.25):
        self.simulation_time = simulation_time
        self.dt = dt
        if simulation_time == 0:  # determine how many steps to run; if not specified, use maximum steps
            total_steps = self.structures[structure_name].maximum_steps
        else:
            total_steps = int(simulation_time/dt)

        # main iteration
        for i in range(total_steps):
            # stock_behavior.append(structure0.sfd.nodes['stock0']['value'])
            print('\nExecuting Step {} :\n'.format(i))
            self.structures[structure_name].step(dt)

    # Draw graphs
    def draw_graphs(self, structure_name='default', names=None):
        if names is None:
            names = list(self.structures[structure_name].sfd.nodes)

        plt.figure(figsize=(10, 5))
        plt.subplot(121)
        plt.xlabel('Time')
        plt.ylabel('Behavior')
        y_axis_minimum = 0
        y_axis_maximum = 0
        for name in names:
            # set the range of axis based on this element's behavior
            # 0 -> end of period (time), 0 -> 100 (y range)
            try:
                name_minimum = min(self.structures[structure_name].sfd.nodes[name]['value'])
            except:  # if this element is a constant, there's no min
                name_minimum = self.structures[structure_name].sfd.nodes[name]['value'][-1]
            if name_minimum < y_axis_minimum:
                y_axis_minimum = name_minimum

            try:
                name_maximum = max(self.structures[structure_name].sfd.nodes[name]['value'])
            except:  # if this element is a constant, there's no max
                name_maximum = self.structures[structure_name].sfd.nodes[name]['value'][-1]
            if name_maximum > y_axis_maximum:
                y_axis_maximum = name_maximum

            plt.axis([0, self.simulation_time, y_axis_minimum, y_axis_maximum])
            plt.plot(self.structures[structure_name].sfd.nodes[name]['value'], label=name)
        plt.legend()

        plt.subplot(122)
        # labels = nx.get_node_attributes(structure0.sfd, 'value')
        # nx.draw(structure0.sfd, labels=labels)
        nx.draw(self.structures[structure_name].sfd, with_labels=True)
        plt.show()


def main():
    sess0 = Session()
    sess0.first_order_negative()
    sess0.simulate(simulation_time=80)
    sess0.draw_graphs(names=['stock0', 'flow0'])


if __name__ == '__main__':
    main()
