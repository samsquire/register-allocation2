registers = ["rdi", "rsi", "rax", "rdx", "rcx"]
colours = ["#19a516",
          "#f64b49",
         "#315bb6",
         "#afe838",
         "#ea3d9e",
         "#04ba72"]
class Ins:

  def __init__(self, name, children, value):
    self.name = name
    self.children = children
    self.value = value
    self.var_name = "unset"
    self.dependencies = []
    self.colour = "white"

  def getdependencies(self):
    return []

  
  
  def walk(self, depth=0):
    yield (self.var_name,
           self), "{} {} <- {} {}".format(" " * depth, self.var_name,
                                          self.name, self)
    for child in self.children:
      yield from child.walk(depth=depth + 1)

  def anf(self, depth=0):

    for child in self.children:
      yield from child.anf(depth=depth + 1)
    yield (self.var_name, self), "{} {} <- {}".format(" " * depth,
                                                      self.var_name, self)

  def index(self, vars):
    for child in self.children:
      child.index(vars)
    vars[self.name] = self


class Literal(Ins):

  def __init__(self, value):
    super(Literal, self).__init__(value, [], value)

  def __repr__(self):
    return "literal {}".format(self.value)


class Mul(Ins):

  def __init__(self, name, children, value):
    super(Mul, self).__init__(name, children, value)

  def __repr__(self):
    return "mul {}".format(self.children)


class Reference(Ins):

  def __init__(self, name):
    super(Reference, self).__init__("ref_" + name, [], name)

  def __repr__(self):
    return "ref {}".format(self.value)

  def getdependencies(self):
    return [self.value]


class Assign(Ins):

  def __init__(self, name, children, value):
    super(Assign, self).__init__(name, children, value)

  def __repr__(self):
    return "assign {} = {}".format(self.name, self.dependencies)


class Add(Ins):

  def __init__(self, name, children, value):
    super(Add, self).__init__(name, children, value)

  def __repr__(self):
    return "add {}".format(self.dependencies)


class Print(Ins):

  def __init__(self, name, children, value):
    super(Print, self).__init__(name, children, value)

  def __repr__(self):
    return "print {}".format(self.children)


def assign_vars(root, vars):
  var_count = 0

  def _assign_vars(var_count, item):
    for child in item.children:
      var_count = var_count + 1
      child.var_name = "v{}".format(var_count)
      var_count, item = _assign_vars(var_count, child)
      child.dependencies = [child for child in child.children]
      child.dependencies.extend([vars[dep] for dep in child.getdependencies()])
      child.dependencies = list(set(child.dependencies))

    item.dependencies = [child for child in item.children]
    item.dependencies.extend([vars[dep] for dep in item.getdependencies()])
    item.dependencies = list(set(item.dependencies))
    return var_count, item

  var_count, newroot = _assign_vars(var_count, root)

  return var_count, newroot


ins = Ins("Root", [
    Assign("a", [Add("add", [Literal(6), Literal(7)], None)], None),
    Assign("b", [Literal(8)], None),
    Assign("m", [Add("add2", [Reference("a"), Reference("b")], None)], None),
    Print("print", [Reference("m")], None)
], None)

vars = {}
ins.index(vars)
assign_vars(ins, vars)
for item in ins.walk():
  print(item)

print("# ANF")
for item in ins.anf():
  print(item[1])

from pprint import pprint

from subprocess import Popen, PIPE


class Graph():

  def __init__(self, name):
    self.adjacency = {}
    self.backwards = {}
    self.name = name
    self.nodes = []

  def search(self, node):
    found = set()
    if node in self.nodes:
      for out in self.adjacency[node]:
        found.add(out)

      for backward in self.backwards[node]:
        found.add(backward)
    return found
  def restore(self):
    self.adjacency = self.adjacency_backup
  def backup(self):
    self.adjacency_backup = dict(self.adjacency)
  
  def remove_node(self, size):
    removals = []
    for node, links in self.adjacency.items():
      if len(links) < size:
        removals.append(node)
        break
    for removal in removals:
      del self.adjacency[removal]
    if removals:
      return removals[0]
    return None
  
  def has_node_with_degree(self, size):
    for node, links in self.adjacency.items():
      if len(links) < size:
        return True
    return False
  
  def add_edge(self, start, end):

    if start not in self.adjacency:
      self.adjacency[start] = []
      self.backwards[start] = []
      self.nodes.append(start)
    if end not in self.adjacency:
      self.adjacency[end] = []
      self.backwards[end] = []
      self.nodes.append(end)
    self.adjacency[start].append(end)
    self.adjacency[end].append(start)

  def draw(self):
    dot = Popen(["dot", "-Tsvg", "-o", "graphs/{}.svg".format(self.name)],
                stdin=PIPE,
                stdout=PIPE)
    graph = "digraph G {\n"
    for item, value in self.adjacency.items():
      name = "{} ({})".format(str(item), item.register)
      graph += "\"{}\" [style=filled,fillcolor=\"{}\"];\n".format(name, item.colour)
      for link in value:
        
        linkname = "{} ({})".format(str(link), link.register)
        
        graph += "\"{}\" -> \"{}\";\n".format(name, linkname)
    graph += "}"
    print(graph)
    dot.communicate(graph.encode("utf8"))





def live_range(ins):
  stacks = []

  anf = list(ins.anf())
  for item in anf:
    print(item[0][1].dependencies)
  pprint(anf)
  for index, item in enumerate(anf):
    notused_start = -1
    used_start = -1
    notused = -1
    stack = []
    used = []
    unused = []

    for subindex, subitem in enumerate(anf):
      if subitem[0][1] == item[0][1]:
        continue
      if subitem[0][1] in item[0][1].dependencies:

        unused = []
        if len(used) == 0:
          used.append({
              "item": item[0][1],
              "start": subindex,
              "vars": [subitem[0][1]],
              "end": subindex,
              "type": "used"
          })
          stack.append(used[-1])
        else:
          used[-1]["end"] = subindex
          used[-1]["vars"].append(subitem[0][1])
      else:
        if len(used) > 0:

          used[-1]["end"] = used[-1]["end"] = subindex

          used = []
        if len(unused) == 0:
          unused.append({
              "item": item[0][1],
              "start": subindex,
              "end": subindex,
              "type": "unused"
          })
          stack.append(unused[-1])
        else:
          unused[-1]["end"] = subindex

    # print("{} start at {}".format(item[0], subindex))
    # print("{} not used at {}".format(item[0], notused_start, notused_end))
    pprint(stack)
    stacks.append(stack)

  edges = []
  vertices = []
  interactions = Graph("root")
  

  
  for stack in stacks:
    for item in stack:
      if item["type"] == "used":
        for var in item["vars"]:
          print("{} -> {}".format(var, item["item"]))
          interactions.add_edge(var, item["item"])

  interactions.backup()
  stack = []
  while interactions.has_node_with_degree(4):
    node = interactions.remove_node(4)
    stack.append(node)

  assigned = []
  pprint(stack)
  available = list(registers)
  while len(stack) > 0:
    if len(available) == 0:
      available = list(registers)
    register = available.pop(0)
    item = stack.pop(0)
    assigned.append((register, item))
    item.register = register
    item.colour = colours[registers.index(register)]

  interactions.restore()
  interactions.draw()
  
  
  pprint(assigned)
live_range(ins)




def register_allocate():
  pass
