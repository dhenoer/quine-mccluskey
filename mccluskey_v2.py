import string
import tabulate
import random
import re
import time


DEBUG = True
TABLEFMT = 'fancy_grid'
TABLEFMT = 'grid'
TABLEFMT = None


def debug(var):
	global DEBUG
	if DEBUG:
		print('debug>', var, end=' ')
		e = eval(var)
		print(type(e), e)


class Quine:

	expression = None
	expressionType = None
	symbols = []
	operands = [] # operands for literal SOP format
	minterm = [] # in integer SOP format
	numliteral = 0

	def __init__(self):
		pass

	def info(self):
		print('Symbols', self.symbols)
		print('Operands', self.operands)
		print('Minterm', self.minterm)
		print('Number of literal', self.numliteral)

	def set_symbols(self, sym='XYZ'):
		''' set all literal symbols found in expression 
			return value: None
		'''

		self.symbols = []
		if sym=='ABC':
			for i in range(self.numliteral):
				self.symbols.append(chr(ord('a')+i))
		elif sym=='XYZ':
			for i in range(self.numliteral):
				self.symbols.append(chr(ord('z')-self.numliteral+i+1))


	def expression_to_minterm(self, expression):
		'''
		convert expression to minterms
		expression: string containing SOP format, or literal format
			e.g 0,5,13,... or ab'c+a'c+...
		'''

		self.symbols = []
		self.operands = []

		# preprocess expression
		expression.replace(' ', '')
		arproblemABC = expression.split('+')
		arproblemSOP = expression.split(',')

		# if expression is literal ABC
		if len(arproblemABC) > 1:

			self.expressionType = 2

			for p in arproblemABC:
				# find format a or a' 
				allre = re.findall('([a-z]\')|([a-z])', p)
				allre = [ ''.join(s) for s in allre ]
				self.operands.append( allre )

				# collects symbol
				for literal in allre:
					self.symbols.append( literal[0] )

			# default minterm based on symbols
			self.symbols = sorted(set(self.symbols))
			defaultmt = {}
			for s in self.symbols:
				defaultmt[s]='01'


			# populate minterm for SOP format
			mintermall = []

			# iterate through operands
			for o in self.operands:

				minterm = defaultmt.copy()

				for s in o:
					if len(s)==1:
						# assume single literal
						minterm[s] = '1'
					else:
						# non-single means inverter
						minterm[s[0]] = '0'

				#print('minterm', minterm)
				mintermall.extend( self.literalbool_to_minterm( list( minterm.values()) ))
				
			self.minterm = list(set(mintermall))
			self.numliteral = len(self.symbols)


		# assume integer SOP format minterm
		else:

			self.expressionType = 1
			self.minterm = sorted(list(map(int, arproblemSOP)))



		# count number of variables
		lenOfBinary = len(bin(max(self.minterm)))-2
		lenOfSymbols = len(self.symbols)
		self.numliteral = max([lenOfBinary, lenOfSymbols])
		self.expression = expression
	
		if len(self.symbols)==0:
			self.set_symbols()

		#print(self.info())
			

	def literalbool_to_minterm(self, multimt, prev=[]):
		''' 
		convert literal boolean of operands to decimal minterm 
		operands: list of string operand, eg ['1', '01', '0' ] means AC'
		'''

		result = []
		if len(multimt) == 0 :

			dec = 0
			prev.reverse()
			for i, d in enumerate(prev):
				dec += (2**i if d=='1' else 0)
			return [dec]

		else:

			for b in multimt[0]:

				anext = prev.copy()
				anext.append(b)

				result.extend( self.literalbool_to_minterm( multimt[1:], anext))

			return result

	def notasi(self, i):
		''' generate literal symbol
		i: integer, index of symbols
		return  char symbol, eg: A or X 
		'''
		return self.symbols[i]


	def literal_term(self, bin):
		''' generatere literal term
		bin: list of binary, eg [0, -, 1, -]
		return literal term, eg  AC'D
		'''
		retval = []
		for i, d in enumerate(bin):
			if d in [0, 1]:
				retval.append(self.notasi(i))
			if d==0:
				retval.append('\'')
		return ''.join(retval)


	def dec2bin(self, d):
		'''
		decimal to list binary
		d: integer to be converted to binary list
		return value: list of binary with length of self.numliteral
		'''

		dbin = bin(d) # bin function return string contains biner with prepended by '0b'
		retv = []
		for d in dbin[-1:1:-1]:
			retv.insert(0,int(d))
		for i in range(self.numliteral - len(retv)):
			retv.insert(0,0)
		return retv

	def solve(self):
		'''solve the problem
		'''


		table_minterm = {}
		table_minterm_next = {}
		table_gid_next = set()


		## minterm to binary ----------------------

		table_minterm[0] = {}
		for mt in self.minterm:

			listbin = self.dec2bin( mt )
			gid = sum( listbin )

			rowmt = {}
			rowmt['mt'] = [mt]
			rowmt['bin'] = listbin
			rowmt['tag'] = ''

			table_minterm[0][str(mt)] = rowmt
			table_gid_next.add(gid)

			if not table_minterm_next.get(gid):
				table_minterm_next[gid] = {}
			table_minterm_next[gid][mt] = rowmt
	
		table_gid_next = sorted(table_gid_next)


		# send output -- tabulate
		print('\nTabel Desimal to Binary\n')
		tbl_out = [['Desimal', 'Binary']]
		for mt, row in table_minterm[0].items():
			row = [mt, ''.join(map(str,row['bin']))]
			tbl_out.append(row)
		print(tabulate.tabulate(tbl_out, headers='firstrow', 
			numalign='center', stralign='center',
			tablefmt=TABLEFMT))



		## process next minterm implicant ------------------

		table_minterm_nontag = {}

		loopingNum = 0
		while True:
			loopingNum += 1

			# move next table to current table
			table_minterm = table_minterm_next.copy()
			table_gid = table_gid_next.copy()

			# and empty next table
			table_minterm_next = {}
			table_gid_next = set()

			firstG = True
			nTag = 0
			for currG in table_gid:

				# skip first group
				if firstG:
					firstG = False
					prevG = currG
					continue

				# compare adjacent group
				for mt2 in table_minterm[currG]:

					# read previous group
					for mt1 in table_minterm[prevG]:

						currBin = table_minterm[currG][mt2]['bin']
						prevBin = table_minterm[prevG][mt1]['bin']					
						newBin = []

						nDiff = 0
						for i,d in enumerate(currBin):

							# ompare for 0,1 to any 0,1
							if d in [0,1] and prevBin[i] in [0,1]:
								if d != prevBin[i]:
									newBin.append('-')
									nDiff += 1
								else:
									newBin.append(d)
							# else 0,1,- to -
							else:
								if d != prevBin[i]:
									# abandon for 0,1 compare to -
									nDiff += 99
								newBin.append(d)
	

						# if differencies was found
						if nDiff == 1:

							newG = sum([d for d in newBin if type(d)==int ])

							table_minterm[prevG][mt1]['tag']='v'
							table_minterm[currG][mt2]['tag']='v'

							newMt = []
							newMt.extend(table_minterm[prevG][mt1]['mt'])
							newMt.extend(table_minterm[currG][mt2]['mt'])

							newMt = sorted(set(newMt))
							newMtLbl = ','.join([ str(d) for d in newMt ])

							if not table_minterm_next.get(newG) :
								table_minterm_next[newG] = {}
							if not table_minterm_next[newG].get(newMtLbl) :
								table_minterm_next[newG][newMtLbl] = {}

							table_minterm_next[newG][newMtLbl]['mt'] = newMt
							table_minterm_next[newG][newMtLbl]['bin'] = newBin
							table_minterm_next[newG][newMtLbl]['tag'] = ''

							table_gid_next.add(newG)

							nTag += 1
			
				prevG = currG

			# collects non tag for table implicant process
			for g,gv in table_minterm.items():
				for mt, mtv in gv.items():
					if mtv['tag'] == '':
						table_minterm_nontag[mt] = {'mt': mtv['mt'], 'bin':mtv['bin']}

	
			# output -- tabulation
			print('\nTable Minterm - Iterasi', loopingNum)

			# header
			tbl_out = []
			row = ['Group', 'Minterm']
			row.extend(self.symbols)
			row.append('Tag')
			tbl_out.append(row)

			# row cell
			for g in table_gid:
				for mt, mtv in table_minterm[g].items():
					row = []
					row.append(g)
					row.append(mt)
					row.extend(mtv['bin'])
					row.append(mtv['tag'])
					tbl_out.append(row)

			print(tabulate.tabulate(tbl_out, headers='firstrow', 
				numalign='center', stralign='center',
				tablefmt=TABLEFMT))

			if nTag == 0:
				break



		# print nontag
		#print('nontag', table_minterm_nontag)

		# ready to solve prime implicant table
		#print('------- solve find implicant table -----')


		table_prime_implicant = {}
		checkrow = {}
		checkcol = {}
		for mt, mtv in table_minterm_nontag.items():

			#debug('mtid')
			#debug('bin')

			literalTerm = self.literal_term(mtv['bin'])
			table_prime_implicant[literalTerm] = {}
			checkrow[literalTerm] = 0

			armtid = mtv['mt']
			for p in self.minterm:
				strp = str(p)
				if p in armtid:
					table_prime_implicant[literalTerm][strp] = 1
					checkcol[strp] = checkcol.get(strp,0) + 1
				else:
					table_prime_implicant[literalTerm][strp] = ''


		# ouput table

		print('\nTabel Prime Implicant')
		# -----------------------------
		# header
		tbl_out = []
		row = ['Literal']
		for i in self.minterm:
			row.append(i)
		tbl_out.append(row)

		# body cell
		for litm, litmv in table_prime_implicant.items():
			row = [litm]
			for d in litmv.values():
				row.append(d)
			tbl_out.append(row)

		print(tabulate.tabulate(tbl_out, headers='firstrow', 
			numalign='center', stralign='center',
			tablefmt=TABLEFMT))



		loopingNum = 0
		while True and loopingNum < 10:
			loopingNum += 1

			#sorted checkrow
			#sum checkcol
			for mtid,vcol in checkcol.items():
				if vcol == 'v':
					continue
				sumrow = 0
				for litmt,vrow in checkrow.items():
					if vrow == 'v':
						continue
					if table_prime_implicant[litmt][mtid] == 1:
						sumrow += 1
				checkcol[mtid] = sumrow

			#mincol = sorted(checkcol, key=int(checkcol.get))
			mincol = checkcol
			for mtid in mincol:

				if checkcol[mtid]=='v':
					continue

				#debug('mtid')

				if checkcol[mtid] == 1:

					# find what literal term
					for litm in checkrow:

						cell = table_prime_implicant[litm][mtid]
						if cell == 1 :

							# found pivoting on litm, mtid
							table_prime_implicant[litm][mtid] = 'v'
							checkrow[litm] = 'v'
							checkcol[mtid] = 'v'

							# check all cell horizontal
							for mtid2 in mincol:

								cell2 = table_prime_implicant[litm][mtid2]

								# if found 1 tag
								if cell2 == 1:

									table_prime_implicant[litm][mtid2] = 'v'

									# check cell vertically
									for litm2 in checkrow:
										if litm2 == litm:
											continue

										cell3 = table_prime_implicant[litm2][mtid2]

										# if found
										if cell3 == 1:

											table_prime_implicant[litm2][mtid2] = '.'

									checkcol[mtid2] = 'v'


			'''
			print('\nTabel Prime Implicant - Essential')
			# header
			tbl_out = []
			row = ['Literal']
			for i in self.minterm:
				row.append(i)
			row.append('Check')
			tbl_out.append(row)

			# row cell
			for litm, v in table_prime_implicant.items():
				row = [litm]
				for d in v.values():
					row.append(d)
				row.append(checkrow[litm])
				tbl_out.append(row)

			# foorer
			row = ['Check']
			for i in self.minterm:
				row.append(checkcol[str(i)])
			row.append('--')
			tbl_out.append(row)

			print(tabulate.tabulate(tbl_out, headers='firstrow', 
				numalign='center', stralign='center',
				tablefmt=TABLEFMT))
			'''


			# reduced

			# check that not yet verified, still 0
			superset = {}
			for termABC, vABC in checkrow.items():
				if vABC == 'v':
					continue

				superset[termABC] = set()

				for mtid, vmtid in checkcol.items():
					if vmtid == 1:
						continue

					cell = table_prime_implicant[termABC][mtid]
					if cell == 1:
						superset[termABC].add(mtid)

				if len(superset[termABC])==0:
					superset.pop(termABC)


			#if len(superset) == 0:
			#	break

			#debug('superset')

			for termABC, mtidset in superset.items():
				for termABC2, mtidset2 in superset.items():

					if termABC2 == termABC:
						continue

					if mtidset.issuperset(mtidset2):
						#print(termABC, mtidset, 'superset of', mtidset2)

						#checkrow[termABC] = 1 # <- test again v
						for id in mtidset:

							table_prime_implicant[termABC][id] = 1 # <- agai v

							for termABC3, vtermABC3 in table_prime_implicant.items():
								if termABC3 == termABC:
									continue

								if table_prime_implicant[termABC3][id] == 1:
									table_prime_implicant[termABC3][id] = '.'

							checkcol[id] == 1
						 

					#if mtidset.issubset(mtidset2):
					#	for id in mtidset:
					#		table_prime_implicant[termABC][id] = '.'

			#find superset
			#debug('superset')
			#debug('checkrow')
			#debug('checkcol')	
						
			if len(superset) == 0:
				print('\nTabel Prime Implicant - Essential - Iterasi', loopingNum)
			else:
				print('\nTabel Prime Implicant - Essential & Reduced - Iterasi', loopingNum)

			# header
			tbl_out = []
			row = ['Literal']
			for i in self.minterm:
				row.append(i)
			#row.append('Chek')
			tbl_out.append(row)

			# row cell
			for termABC, v in table_prime_implicant.items():
				row = [termABC]
				for d in v.values():
					row.append(d)
				#row.append(checkrow[termABC])
				tbl_out.append(row)

			# footer
			#row = ['Check']
			#for i in self.minterm:
			#	row.append(checkcol[str(i)])
			#row.append('--')
			#tbl_out.append(row)

			print(tabulate.tabulate(tbl_out, headers='firstrow', 
				numalign='center', stralign='center',
				tablefmt=TABLEFMT))


			if len(superset) == 0:
				break



		print('\n\nSolusi')
		print('-------')
		print('Penyederhanaan F:', 
			chr(0x2211) if self.expressionType==1 else '', 
			self.expression)
		print('F = ', end='')
		print(' + '.join([ mt for mt, vmt in checkrow.items() if vmt=='v' ]))



	def input_minterm_expression(self):
		''' input minterm expression
		return value: Boolean for valid expresssion
		'''

		expr = input('Input persamaan minterm > ')

		try:
			inpExpr = list(map(int, expr.split(',')))
			inpExpr = sorted(set(inpExpr))
			self.expression_to_minterm(','.join([str(d) for d in inpExpr]))
			return True

		except:
			print('--Error: Input tidak valid. Gunakan integer dipisah koma')
			time.sleep(0.5)
			return False



	def input_literal_expression(self):
		''' input literal expression
		return value: Boolean True for valid expression
		'''

		expr = input('Input persamaan literal > ').lower()

		try:
			# validate
			inpExpr = expr.split('+')
			inpExpr = [ o.strip() for o in inpExpr ]
			for o in inpExpr:
				if not re.fullmatch('([a-z]|[a-z]\')+', o):
					raise f'--Error: Literal {o} tidak valid'
			self.expression_to_minterm(' + '.join(inpExpr))
			return True

		except:
			print('--Error: Input tidak valid, gunakan literal a-z \' dan +')
			time.sleep(0.5)
			return False


	def input_random_minterm(self):
		minterm = []
		maxrange = 2**5
		nsample = random.randint(maxrange//10, 17)
		minterm = sorted(random.sample(list(range(0, maxrange+1)), k=nsample))
		self.expression_to_minterm(','.join([str(d) for d in minterm ]))
		return True


# ---- main program

quine = Quine()


print('Penyederhanaan Fungsi Boolean dg Metode Quine-McCluskey')
#print('-------------------------------------------------------')
print(chr(0x2014) * 55)


# example problem

probMint = '1,2,4,5,9,11,12,14,17,18,21,31,32'
probABC = 'xy + xy\' + y'

print('\nSoftware ini adalah implemetasi MK LogMat untuk memecahkan')
print('persoalahan penyederhanaan persamaan Boolean dengam metode')
print('Quine-McCluskey')
print('(c) 2022, Nurhidayat, NIM: 211511001 - K2\n')

while True:
	print('\nMenu pilihan:')
	print('1) Input fungsi SOP setiap minterm dipisah dg koma, misal')
	print('  ',probMint)
	print('2) Input Fungsi SOP dengan format literal, misal')
	print('  ',probABC)
	print('3) Generate fungsi SOP minterm secara random')
	print('4) Selesai\n')

	menu = input('Input > ')
	if menu not in ['1','2','3','4']:
		print('--Error: pilihan tidak valid')
		time.sleep(0.5)
		continue

	ret = False
	if menu == '1':
		ret = quine.input_minterm_expression()

	elif menu == '2':
		ret = quine.input_literal_expression()

	elif menu == '3':
		ret = quine.input_random_minterm()

	else:
		break


	if ret:
		print('Penyederhanaan F:', chr(0x2211) if quine.expressionType==1 else '', 
			quine.expression)
		solve = input('Solve, Y/t? ').lower()
		if solve in ['y', 'ya', 'yes']:
			quine.solve()
			print('\n-- Selesai, Enter untuk lanjut --')
			input()


print('Bye..')
quit()

