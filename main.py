class Ins:
  def __init__(self, name, children, value):
    self.name = name
    self.children = children
    self.value = value
    self.var_name = "unset"
    self.dependencies = []

  def getdependencies(self):
    return []
  
  def walk(self, depth=0):
    yield (self.var_name, self), "{} {} <- {} {}".format(" " * depth, self.var_name, self.name, self)
    for child in self.children:
      yield from child.walk(depth = depth + 1)

  def anf(self, depth=0):
    
    
    for child in self.children:
      yield from child.anf(depth = depth + 1)
    yield (self.var_name, self), "{} {} <- {} {}".format(" " * depth, self.var_name, self.name, self)

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
    return "ref {}".format(self.name)

  def getdependencies(self):
    return [self.value]

class Assign(Ins):
  def __init__(self, name, children, value):
    super(Assign, self).__init__(name, children, value)
  def __repr__(self):
    return "assign {} = ...".format(self.name)

class Add(Ins):
  def __init__(self, name, children, value):
    super(Add, self).__init__(name, children, value)
  def __repr__(self):
    return "add {}".format(self.value)


def assign_vars(root, vars):
  var_count = 0
  def _assign_vars(var_count, item):
    for child in item.children:
      var_count = var_count + 1
      child.var_name = "v{}".format(var_count)
      var_count, item = _assign_vars(var_count, child)
      child.dependencies = [child.var_name for child in child.children]
      child.dependencies.extend([vars[dep] for dep in child.getdependencies()])
      
    item.dependencies = [child.var_name for child in item.children]
    item.dependencies.extend([vars[dep] for dep in item.getdependencies()])
    return var_count, item
    
  var_count, newroot = _assign_vars(var_count, root)
  
  return var_count, newroot



ins = Ins("Root", [
       Assign("a",
              [
                Add("add", [Literal(6), Literal(7)], None)
                    ], None),
      Assign("b", [Literal(8)], None),
      Assign("m", [Reference("a"), Reference("b")], None)
         ], None)

vars = {}
ins.index(vars)
assign_vars(ins, vars)
for item in ins.walk():
  print(item)

print("# ANF")
for item in ins.anf():
  print(item[1])

def live_range(ins):
  anf = list(ins.anf())
  for item in anf:
    print(item[0][1].dependencies)
  
live_range(ins)

registers = [
  "rdi",
  "rsi",
  "rax",
  "rdx",
  "rcx"
]

def register_allocate():
  pass