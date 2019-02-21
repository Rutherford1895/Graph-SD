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
    def __init__(self, simulation_time=20, dt=0.25):
        self.sfd = nx.MultiDiGraph()
        self.simulation_time = simulation_time
        self.dt = dt

    def simulation_parameter(self):
        return [self.simulation_time, self.dt]

    def add_element(self, name, element_type, function=None, value=None):
        # this 'function' is a list, containing the function it self and its parameters
        self.sfd.add_node(name, element_type=element_type, function=function, value=value)

    def add_causality(self, from_element, to_element, function=None):
        self.sfd.add_edge(from_element, to_element, function)

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

    # !!!!!!!!!!!!!!!!!!!!!! #
    def calculate(self, name):
        if self.sfd.nodes[name]['value'] is not None:
            return self.sfd.nodes[name]['value']
        else:  # it's not a constant value but a function
            params = self.sfd.nodes[name]['function'][1:]
            for j in range(len(params)):  # use recursion to find the values of params, then --
                params[j] = self.calculate(params[j])  # replace the param's name with its value.

            return self.sfd.nodes[name]['function'][0](*params)

    def step(self):
        flows_dt = dict()  # have a dictionary of flows and their values in this dt, to be added to stocks afterward.

        # find all flows
        for element in self.sfd.nodes:  # loop through all elements in this SFD,
            if self.sfd.nodes[element]['element_type'] == FLOW:  # if this element is a FLOW --
                flows_dt[element] = 0  # make a position for it in the dict of flows_dt, initializing it with 0

        # calculate flows
        for flow in flows_dt.keys():
            flows_dt[flow] = self.dt * self.calculate(flow)
        print('All flows dt:', flows_dt)

        # calculating changes in stocks
        # have a dictionary of affected stocks and their changes, for one flow could affect 2 stocks.
        affected_stocks = dict()
        for flow in flows_dt.keys():
            successors = list(self.sfd.successors(flow))  # successors of a flow into a list
            print('Successors of {}: '.format(flow), successors)
            for successor in successors:
                if self.sfd.nodes[successor]['element_type'] == STOCK:  # flow may also affect elements other than stock
                    if successor not in affected_stocks.keys():
                        affected_stocks[successor] = flows_dt[flow]
                    else:
                        affected_stocks[successor] += flows_dt[flow]

        # updating stocks values
        for stock in affected_stocks.keys():
            self.sfd.nodes[stock]['value'] += affected_stocks[stock]


structure0 = Structure(simulation_time=80, dt=0.25)

structure0.add_element('stock0', STOCK, value=100)
structure0.add_element('flow0', FLOW, function=[DIVISION, 'gap0', 'at0'])
structure0.add_causality('flow0', 'stock0')

structure0.add_element('goal0', PARAMETER, value=20)
structure0.add_element('gap0', VARIABLE, function=[SUBTRACT, 'goal0', 'stock0'])
structure0.add_causality('stock0', 'gap0')
structure0.add_causality('goal0', 'gap0')

structure0.add_element('at0', PARAMETER, value=5)
structure0.add_causality('gap0', 'flow0')
structure0.add_causality('at0', 'flow0')


structure0.display_elements()
structure0.display_element('stock0')
structure0.display_element('flow0')
structure0.display_causalities()
structure0.display_causality('flow0', 'stock0')

# Run a simulation
simulation_steps = int(structure0.simulation_parameter()[0]/structure0.simulation_parameter()[1])
stock_behavior = [structure0.sfd.nodes['stock0']['value']]
for i in range(simulation_steps):
    stock_behavior.append(structure0.sfd.nodes['stock0']['value'])
    print('\nExecuting Step {} :\n'.format(i))
    structure0.step()
    # structure0.display_elements()

stock_behavior.append(structure0.sfd.nodes['stock0']['value'])

print('\nStock Behavior:', stock_behavior)

# Draw the behavior graph
plt.figure(figsize=(10, 5))
plt.subplot(121)
plt.xlabel('Time')
plt.ylabel('Stock Behavior')
plt.axis([0, structure0.simulation_parameter()[0], 0, 100])  # 0 -> end of period (time), 0 -> 100 (y range)
plt.plot(stock_behavior, label='Stock behavior')
plt.legend()

plt.subplot(122)
#labels = nx.get_node_attributes(structure0.sfd, 'value')
#nx.draw(structure0.sfd, labels=labels)
nx.draw(structure0.sfd, with_labels=True)
plt.show()
