import logging
from pyparsing import Literal, CaselessLiteral, Word, Combine, Group, Optional, ZeroOrMore, Forward, nums, alphas, oneOf, ParseException
import math
from random import SystemRandom
import operator

logger = logging.getLogger("Senpai")

totalDice = 0
crypto = SystemRandom()

# Used to evalute an expression string
class NumericStringParser(object):
	'''
	Most of this code comes from the fourFn.py pyparsing example
	'''
	def pushFirst(self, strg, loc, toks):
		self.exprStack.append(toks[0])

	def pushUMinus(self, strg, loc, toks):
		if toks and toks[0]=="-":
			self.exprStack.append("unary -")

	def __init__(self):
		"""
		expop   :: '^'
		multop  :: '*' | '/'
		addop   :: '+' | '-'
		integer :: ['+' | '-'] '0'..'9'+
		atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
		factor  :: atom [ expop factor ]*
		term    :: factor [ multop factor ]*
		expr    :: term [ addop term ]*
		"""
		point = Literal(".")
		e     = CaselessLiteral("E")
		fnumber = Combine( Word("+-"+nums, nums ) +
						   Optional(point + Optional(Word(nums))) +
						   Optional(e + Word("+-"+nums, nums)))
		ident = Word(alphas, alphas+nums+"_$")
		plus  = Literal("+")
		minus = Literal("-")
		mult  = Literal("*")
		div   = Literal("/")
		lpar  = Literal("(").suppress()
		rpar  = Literal(")").suppress()
		addop  = plus | minus
		multop = mult | div
		expop = Literal("^")
		pi    = CaselessLiteral("PI")
		expr = Forward()
		atom = ((Optional(oneOf("- +")) 
				+ (pi|e|fnumber|ident+lpar+expr+rpar).setParseAction(self.pushFirst))
				| Optional(oneOf("- +")) + Group(lpar+expr+rpar)
			).setParseAction(self.pushUMinus)
		# by defining exponentiation as "atom [ ^ factor ]..." instead of
		# "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-right
		# that is, 2^3^2 = 2^(3^2), not (2^3)^2.
		factor = Forward()
		factor << atom + ZeroOrMore((expop + factor).setParseAction(self.pushFirst))
		term = factor + ZeroOrMore((multop + factor).setParseAction(self.pushFirst))
		expr << term + ZeroOrMore((addop + term).setParseAction(self.pushFirst))
		# addop_term = (addop + term).setParseAction(self.pushFirst)
		# general_term = term + ZeroOrMore(addop_term) | OneOrMore(addop_term)
		# expr <<  general_term
		self.bnf = expr
		# map operator symbols to corresponding arithmetic operations
		epsilon = 1e-12
		self.opn = {
			"+" : operator.add,
			"-" : operator.sub,
			"*" : operator.mul,
			"/" : operator.truediv,
			"^" : operator.pow
		}
		self.fn  = {
			"sin" : math.sin,
			"cos" : math.cos,
			"tan" : math.tan,
			"abs" : abs,
			"trunc" : lambda a: int(a),
			"round" : round,
			"sgn" : lambda a: abs(a)>epsilon and cmp(a,0) or 0
		}

	def evaluateStack(self, s ):
		op = s.pop()
		if op == "unary -":
			return -self.evaluateStack(s)
		if op in "+-*/^":
			op2 = self.evaluateStack(s)
			op1 = self.evaluateStack(s)
			return self.opn[op](op1, op2)
		elif op == "PI":
			return math.pi # 3.1415926535
		elif op == "E":
			return math.e  # 2.718281828
		elif op in self.fn:
			return self.fn[op](self.evaluateStack(s))
		elif op[0].isalpha():
			return 0
		else:
			return float(op)
			
	def eval(self,num_string,parseAll=True):
		self.exprStack=[]
		results=self.bnf.parseString(num_string,parseAll)
		val=self.evaluateStack(self.exprStack[:])
		return val

# Check if a string represents an int
def isInt(num_str):
	try:
		num = int(num_str)
		if num < 0:
			return False
		else:
			return True
	except:
		return False

# Split a string by sep and keep sep as an element in the result
def splitstring(string, sep):
	array = string.split(sep)
	new_array = []
	for index, item in enumerate(array):
		new_array.append(item)
		if index != len(array)-1:
			new_array.append(sep)

	return new_array

# Split elements in an array using splitstring
def splitarray(array, sep):
	for index, item in enumerate(array):
		if sep in item and sep != item:
			temp_array = splitstring(item, sep)
			del array[index]
			temp_array.reverse()
			for temp in temp_array:
				array.insert(index, temp)

	return array

# Generate random numbers for each die requested
def roll_dice(dice):
	global totalDice

	try:
		number, limit = dice.split("d", 1)
		limit = int(float(limit))
		if number == "":
			number = 1
		else:
			number = int(float(number))

		if limit < 0 or number < 0:
			raise RuntimeError("No negative numbers")

		# There's recursion limits on the evalutation method, so limit things here
		totalDice += number
		if totalDice > 1000:
			raise RuntimeError("Numbers too big")

		rolls = []
		for r in range(number):
			rolls.append(crypto.randint(1, limit))

		if number == 1:
			string_result = str(sum(rolls))
		else:
			string_result = " + ".join(str(x) for x in rolls)

		return string_result
	except Exception as e:
		if "No negative numbers" in str(e) or "Numbers too big" in str(e):
			raise
		else:
			raise RuntimeError("Bad dice format")

# Figure out what a roll means and evaluate any expressions
async def parse_roll(dice_string):
	if dice_string == "stats":
		response = await stats()
		return {"message": response}
	
	logger.debug("Rolling: {0}".format(dice_string))

	global totalDice
	totalDice = 0

	dice_string = dice_string.replace(" ", "")
	logger.debug("Rolling %s", dice_string)
	try:
		dice_array = splitstring(dice_string, "+")
		dice_array = splitarray(dice_array, "-")
		dice_array = splitarray(dice_array, "*")
		dice_array = splitarray(dice_array, "/")
		dice_array = splitarray(dice_array, "^")
		dice_array = splitarray(dice_array, "(")
		dice_array = splitarray(dice_array, ")")
	except Exception as e:
		logger.exception(e)
		return {"message": "I can't cope with whatever the hell you just tried to give me."}

	# Roll for an NdM parts and substitute in the result in parenthesis
	for index, item in enumerate(dice_array):
		if "d" in item:
			try:
				string_result = roll_dice(item)
				del dice_array[index]
				dice_array.insert(index, "({0})".format(string_result))
			except RuntimeError as e:
				if "Bad dice format" in str(e):
					logger.info("Bad dice format")
					return {"message": "Use an NdM format for rolls please."}
				elif "Numbers too big" in str(e):
					logger.info("Numbers too big")
					return {"message": "You ask for too much."}
				else:
					logger.exception(e)
					return {"message": "I failed, for some reason I don't know."}

	message = "".join(dice_array)

	# Attempt to evaluate the expression
	nsp = NumericStringParser()
	try:
		result = nsp.eval(message.replace(" ", ""))
	except ParseException as e:
		logger.info("Could not evaluate {0}".format(message))
		return {"message": "Bad expression"}
	except RecursionError as e:
		logger.info("Recursion limit reached.")
		return {"message": "Sorry, there's too many operations needed to evaluate that"}
	except OverflowError as e:
		logger.info("Overflow error")
		return {"message": "Ahhhh! Sorry, the result was too big."}

	# Convert to integer, if possible
	if not isinstance(result, complex):
		if result == int(result):
			result = int(result)
		else:
			result = round(result, 4)
	message += "\n\t = {0}".format(result)

	# Tell discord message to ignore * use for italics
	message.replace("*", "\*")

	# Discord puts a 2000 character limit on messages
	if len(message) > 2000:
		if len(str(result)) + 3 > 2000:
			return {"message": "The result is too big to print."}
		else:
			return {"message": " = {0}".format(result)}
	else:
		return {"message": message}

async def stats():
	logger.debug("Rolling stats")
	rolls = []
	for r in range(4):
		roll = crypto.randint(1, 8)
		if roll <= 4:
			roll -= 4
		else:
			roll -= 5
		rolls.append(roll)

	return "Stats: " + ", ".join(str(x) for x in rolls)

	