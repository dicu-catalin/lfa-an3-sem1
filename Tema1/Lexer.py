class Lexer:
	dfas: []

	def __init__(self, dfas):
		self.dfas = []
		dfa = []
		for line in dfas:
			if (line == "\n"):
				self.dfas.append(DFA(dfa))
				dfa = []
			else:
				dfa.append(line)
		self.dfas.append(DFA(dfa))
		

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


class DFA:
	def __init__(self, lines):
		self.alphabet = []
		for char in lines[0]:
			self.alphabet.append(char)
		self.token = lines[1][0:-1]
		self.initial = int(lines[2])
		self.finals = []
		self.f = {}
		for i in range(3, len(lines)-1):
			line = lines[i].split(",")
			if not int(line[0]) in self.f:
				self.f[int(line[0])] = {}
			if line[1][1:-1] == "\\n":
				self.f[int(line[0])]["\n"] = int(line[2])
			else:
				self.f[int(line[0])][line[1][1:-1]] = int(line[2])
		lines[-1] = lines[-1].split()
		for state in lines[-1]:
			self.finals.append(int(state))

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
		string = "f: " + str(self.f) + ", init st: " + str(self.initial) + ", final st: " + str(self.finals) + " token: " + str(self.token)
		return string



def runlexer(lexer, finput, foutput):
	to_read = open(lexer)
	dfas = to_read.readlines()
	my_lexer = Lexer(dfas)
	to_read = open(finput)
	word = to_read.read()
	result = my_lexer.parse(word)
	file = open(foutput, mode = "w")
	file.write(result)
	file.close()