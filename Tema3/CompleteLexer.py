import sys

eps = "^"

from main import increase_states

class NFA:
	def __init__(self, alphabet, initial, final, f, count):
		self.alphabet = alphabet
		self.initial = initial
		self.final = final
		self.f = f
		self.nr_states = count

	def __str__(self):
		string = "f: " + str(self.f) + ", init st: " + str(self.initial) + ", final st: " + str(self.final) + " alph: " + str(self.alphabet)
		return string

class DFA:
	def __init__(self, token, expr):
		self.token = token
		nfa = expr.to_nfa()
		config = nfa_to_dfa(nfa)
		self.alphabet = config[0]
		self.initial = 0
		self.finals = config[2]
		self.f = config[3]
		self.nr_states = config[4]

	def step(self, config):
		(curent_state, word) = config
		next_state = self.f[curent_state][word[0]]
		return (next_state, word[1:])

	def accept(self, word):
		current_state = self.initial
		for letter in word:
			if current_state not in self.f or letter not in self.f[current_state]:
				return "rejected"
			(current_state, _) = self.step((current_state, letter))
		if current_state in self.finals:
			return "accepted"
		else:
			return "rejected"

	def __str__(self):
		string = ""
		for char in self.alphabet:
			string += char
		string += "\n" + str(self.nr_states) + "\n"
		string += str(self.initial) + "\n"
		for char in self.finals:
			string += str(char) + " "
		for state in self.f:
			for key in self.f[state]:
				string += "\n" + str(state) + ",'" + key + "'," + str(self.f[state][key]) 
		return string


class Lexer:
	dfas: []
	def __init__(self, dfas):
		self.dfas = []
		token = ""
		dfa = ""
		for line in dfas:
			[token, regex] = line.split(" ", 1)
			regex = regex.split(";")[0]
			expr = parse_expr(regex)
			self.dfas.append(DFA(token, expr))
	
	def longest_prefix(self, word):
		longest_accepted = 0
		last_accepted = -1
		id_longest_dfa = -1
		for dfa in self.dfas:
			index = 0
			current_state = dfa.initial
			parsed_word = word

			while parsed_word != "":
				index += 1
				if current_state not in dfa.f:
					break
				if parsed_word[0] not in dfa.f[current_state]:
					break
				(current_state, parsed_word) = dfa.step((current_state, parsed_word))
				if current_state in dfa.finals:
					last_accepted = index
			if last_accepted > longest_accepted:
				longest_accepted = last_accepted
				id_longest_dfa = dfa.token
		return (longest_accepted, id_longest_dfa)


	def parse(self, word):
		longest_accepted = 0
		result = ""
		consumed = 0
		while len(word) > 0:
			loop = word
			(longest_accepted, id_longest_dfa) = self.longest_prefix(word)
			consumed = consumed + longest_accepted 
			if id_longest_dfa == -1:
				result = "No viable alternative at character " + str(consumed + 1) + ", line 0"#character 10, line 0"
				return result
			if word[0:longest_accepted] == "\n":
				result = result + str(id_longest_dfa) + " " + "\\n" + "\n"
			else:
				result = result + str(id_longest_dfa) + " " + word[0:longest_accepted] + "\n"
			word = word[longest_accepted:]
			if loop == word:
				break
		return result

	def __str__(self):
		string = ""
		for dfa in self.dfas:
			string = string + str(dfa) + "\n"
		return string

class Expr:
	pass

class Symbol(Expr):
	char: str

	def __init__(self, c:str):
		self.char = c

	def __str__(self):
		return self.char

	def to_nfa(self):
	 	#construieste nfa
	 	f = {}
	 	f[0] = {}
	 	f[0][self.char] = 1
	 	return NFA(set(self.char), 0, 1, f, 2)


class Star(Expr): 
	expr: Expr

	def __init__(self, expr:Expr):
		self.expr = expr

	def __str__(self):
		if isinstance(self.expr, Symbol) or isinstance(self.expr, Union):
			string = str(self.expr) + "*"
		else:
			string = "(" + str(self.expr) + ")" + "*"
		return string

	def to_nfa(self):
		nfa = self.expr.to_nfa()
		alphabet = nfa.alphabet
		initial = 0
		final = nfa.nr_states + 1
		f = {}
		f[0] = {}
		f[0][eps] = [1, final]
		f.update(increase_states(nfa.f, 1))
		f[nfa.nr_states] = {}
		f[nfa.nr_states][eps] = [1, final]
		return NFA(alphabet, initial, final, f, final + 1)



class Plus(Expr):
	expr: Expr

	def __init__(self, expr:Expr):
		self.expr = expr

	def __str__(self):
		if isinstance(self.expr, Symbol) or isinstance(self.expr, Union):
			string = str(self.expr) + "+"
		else:
			string = "(" + str(self.expr) + ")" + "+"
		return string


	def to_nfa(self):
		nfa = self.expr.to_nfa()
		alphabet = nfa.alphabet
		initial = 0
		final = nfa.nr_states + 1
		f = {}
		f[0] = {}
		f[0][eps] = 1
		f.update(increase_states(nfa.f, 1))
		f[nfa.nr_states] = {}
		f[nfa.nr_states][eps] = [1, final]
		return NFA(alphabet, initial, final, f, final + 1)


class Concat(Expr):
	expr1: Expr
	expr2: Expr

	def __init__(self, expr1:Expr, expr2:Expr):
		self.expr1 = expr1
		self.expr2 = expr2

	def __str__(self):
		string = str(self.expr1) + str(self.expr2)
		return string

	def to_nfa(self):
		nfa1 = self.expr1.to_nfa()
		nfa2 = self.expr2.to_nfa()
		alphabet = nfa1.alphabet.union(nfa2.alphabet)
		initial = nfa1.initial
		# noua stare finala va fi starea finala din cel de-al doilea nfa
		final = nfa2.final + nfa1.nr_states
		f = nfa1.f
		f.update(increase_states(nfa2.f, nfa1.nr_states))
		f[nfa1.final] = {}
		f[nfa1.final][eps] = nfa1.nr_states
		# reface numarul starilor din a doua expresie
		return NFA(alphabet, initial, final, f, nfa1.nr_states + nfa2.nr_states)
		


class Union (Expr):
	expr1: Expr
	expr2: Expr

	def __init__(self, expr1:Expr, expr2:Expr):
		self.expr1 = expr1
		self.expr2 = expr2

	def __str__(self):
		if isinstance(self.expr1, Concat) and isinstance(self.expr2, Concat):
			string = "(" + "(" + str(self.expr1) + ")" + "|" + "(" + str(self.expr2) + ")" + ")"
		elif isinstance(self.expr2, Concat):
			string = "(" + str(self.expr1) + "|" + "(" + str(self.expr2) + ")" + ")"
		elif isinstance(self.expr1, Concat):
			string = "(" + "(" + str(self.expr1) + ")" + "|" + str(self.expr2) + ")"
		else:
			string = "(" + str(self.expr1) + "|" + str(self.expr2) + ")"
		return string

	def to_nfa(self):
		nfa1 = self.expr1.to_nfa()
		nfa2 = self.expr2.to_nfa()
		alphabet = nfa1.alphabet.union(nfa2.alphabet)
		initial = 0
		final = nfa1.nr_states + nfa2.nr_states + 1
		f = {}
		# creeaza prima stare
		f[0] = {}
		f[0][eps] = [1, nfa1.nr_states + 1]# ^-substituent pentru epsilon
		f.update(increase_states(nfa1.f, 1))
		f.update(increase_states(nfa2.f, nfa1.nr_states + 1))
		nr_states = nfa1.nr_states + nfa2.nr_states + 2
		#creeaza ultima stare, la care se ajunge prin epsilon
		f[nfa1.nr_states] = {}
		f[nr_states - 2] = {}
		f[nfa1.nr_states][eps] = nr_states - 1
		f[nr_states - 2][eps] = nr_states - 1
		return NFA(alphabet, initial, final, f, nr_states)


stack = []

def reduce_stack():
	item = stack.pop()
	if item == "+" or item == "|" or item == "*" or item == ")":
		stack.append(item)
	elif item == "(":
		expr = stack.pop()
		close_bracket = stack.pop()
		if len(stack) == 0:
			stack.append(expr)
			return
		item = stack.pop()
		if item == "+":
			stack.append(Plus(expr))
			reduce_stack()
		elif item == "*": # poate fi modificat
			stack.append(Star(expr))
			reduce_stack()
		elif item == "|":
			expr2 = stack.pop()
			stack.append(Union(expr, expr2))
		elif isinstance(item, Expr):
			stack.append(Concat(expr, item))
		else:
			stack.append(item)
			stack.append(expr)
	elif isinstance(item, Expr):
		if len(stack) == 0:
			stack.append(item)
			return
		item2 = stack.pop()
		if item2 == "+":
			stack.append(Plus(item))
			reduce_stack()
		elif item2 == "*":
			stack.append(Star(item))
			reduce_stack()
		elif item2 == "|":
			expr2 = stack.pop()
			stack.append(Union(item, expr2))
			reduce_stack()
		elif isinstance(item2, Expr):
			stack.append(Concat(item, item2))
			reduce_stack()
		else:
			stack.append(item2)
			stack.append(item)

def parse_expr(expr: str) -> Expr:
	if expr == "\' \'":
		return Symbol(" ")
	elif expr == "'\\n'":
		return Symbol("\n")
	i = 1
	while i < len(expr) + 1:
		if expr[-i] == "'" and expr[-i - 1] == " ":
			stack.append(Symbol(" "));
			i = i + 2
		elif expr[-i] == "(" or expr[-i] == "+" or expr[-i] == "*" or expr[-i] == ")" or expr[-i] == "|":
			stack.append(expr[-i])
		else:
			stack.append(Symbol(expr[-i]))
		reduce_stack()
		i += 1
	return(stack.pop())

def epsilon_closure(states, f, rez):
	rez_aux = set()
	for state in states:
		if state in f and eps in f[state]:
			if isinstance(f[state][eps], list):
				for new_state in f[state][eps]:
					rez_aux.add(new_state)
			else:
				rez_aux.add(f[state][eps])
	#verifica daca sunt elemente carora nu le-a verificat epsilon-closure
	last_rez = len(rez)
	rez.update(rez_aux)
	if last_rez != len(rez):
		rez.update(epsilon_closure(rez_aux, f, rez))
	return rez


def nfa_to_dfa(nfa):
	initial = set()
	initial.add(nfa.initial)
	initial.update(epsilon_closure(initial, nfa.f, set()))
	alphabet = sorted(nfa.alphabet)
	newf = {}
	stack = []
	stack.append(initial)
	while len(stack) > 0:
		current = stack.pop()
		for key in alphabet:
			rez = set()
			for state in current:
				if state in nfa.f and key in nfa.f[state]:
					rez.add(nfa.f[state][key])
			if len(rez) > 0:
				rez.update(epsilon_closure(rez, nfa.f, set()))
				if not str(current) in newf:
					newf[str(current)] = {}
				newf[str(current)][key] = str(rez)
				if str(rez) not in newf:
					stack.append(rez)
	finals = []
	f = {}
	count = 0
	names = {}
	# redenumire stari
	for states in newf:
		if not states in names:
			if str(nfa.final) in states:
				finals.append(count)
			names[states] = count
			count += 1
		for key in newf[states]:
			if not newf[states][key] in names:
				if str(nfa.final) in newf[states][key]:
					finals.append(count)
				names[newf[states][key]] = count
				count += 1

	for states in newf:
		f[names[states]] = {}
		for key in newf[states]:
			f[names[states]][key] = names[newf[states][key]]
	# sink state
	nr_states = len(names) + 1
	sink = nr_states - 1
	for i in range(0, nr_states):
		if i not in f:
			f[i] = {}
			for char in nfa.alphabet:
				f[i][char] = sink
		else:
			for char in nfa.alphabet:
				if char not in f[i]:
					f[i][char] = sink
	f[sink] = {}
	for char in alphabet:
		f[sink][char] = sink

	return [nfa.alphabet, 0, finals, f, len(names) + 1]


def runcompletelexer(lexer, finput, foutput):
	to_read = open(lexer)
	dfas = to_read.readlines()
	lexer = Lexer(dfas)
	to_read = open(finput)
	word = to_read.read()
	result = lexer.parse(word)
	#print(lexer)
	file = open(foutput, mode = "w")
	file.write(result)
	file.close()


def runparser():
	return