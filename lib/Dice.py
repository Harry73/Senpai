import logging
from pyparsing import Literal, CaselessLiteral, Word, Combine, Group, Optional, ZeroOrMore, Forward, nums, alphas, \
    oneOf, ParseException
import math
from random import SystemRandom
import operator

from lib.Message import Message

LOGGER = logging.getLogger('Senpai')

totalDice = 0
crypto = SystemRandom()


# Used to evaluate an expression string
class NumericStringParser(object):

    """Most of this code comes from the fourFn.py pyparsing example"""
    def push_first(self, tokens):
        self.exprStack.append(tokens[0])

    def push_uminus(self, tokens):
        if tokens and tokens[0] == '-':
            self.exprStack.append('unary -')

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
        self.exprStack = []
        point = Literal('.')
        e = CaselessLiteral('E')
        fnumber = Combine(Word('+-' + nums, nums) +
                          Optional(point + Optional(Word(nums))) +
                          Optional(e + Word('+-' + nums, nums)))
        ident = Word(alphas, alphas + nums + '_$')
        plus = Literal('+')
        minus = Literal('-')
        mult = Literal('*')
        div = Literal('/')
        lpar = Literal('(').suppress()
        rpar = Literal(')').suppress()
        addop = plus | minus
        multop = mult | div
        expop = Literal('^')
        pi = CaselessLiteral('PI')
        expr = Forward()
        atom = ((Optional(oneOf('- +'))
                + (pi | e | fnumber | ident + lpar + expr + rpar).setParseAction(self.push_first))
                | Optional(oneOf('- +')) + Group(lpar + expr + rpar)
                ).setParseAction(self.push_uminus)
        factor = Forward()
        factor << atom + ZeroOrMore((expop + factor).setParseAction(self.push_first))
        term = factor + ZeroOrMore((multop + factor).setParseAction(self.push_first))
        expr << term + ZeroOrMore((addop + term).setParseAction(self.push_first))
        self.bnf = expr
        # Map operator symbols to corresponding arithmetic operations
        self.opn = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '^': operator.pow
        }
        self.fn = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'abs': abs,
            'trunc': lambda a: int(a),
            'round': round
        }

    def evaluate_stack(self, s):
        op = s.pop()
        if op == 'unary -':
            return -self.evaluate_stack(s)
        if op in '+-*/^':
            op2 = self.evaluate_stack(s)
            op1 = self.evaluate_stack(s)
            return self.opn[op](op1, op2)
        elif op == 'PI':
            return math.pi  # 3.1415926535
        elif op == 'E':
            return math.e   # 2.718281828
        elif op in self.fn:
            return self.fn[op](self.evaluate_stack(s))
        elif op[0].isalpha():
            return 0
        else:
            return float(op)

    def eval(self, num_string, parse_all=True):
        self.bnf.parseString(num_string, parse_all)
        val = self.evaluate_stack(self.exprStack[:])
        return val


# Split a string by sep and keep sep as an element in the result
def split_string(string, sep):
    array = string.split(sep)
    new_array = []
    for index, item in enumerate(array):
        new_array.append(item)
        if index != len(array)-1:
            new_array.append(sep)

    return new_array


# Split elements in an array using splitString
def split_array(array, sep):
    for index, item in enumerate(array):
        if sep in item and sep != item:
            temp_array = split_string(item, sep)
            del array[index]
            temp_array.reverse()
            for temp in temp_array:
                array.insert(index, temp)

    return array


# Generate random numbers for each die requested
def roll_dice(dice):
    global totalDice

    try:
        number, limit = dice.split('d', 1)
        limit = int(float(limit))
        if number == '':
            number = 1
        else:
            number = int(float(number))

        if limit < 0 or number < 0:
            raise RuntimeError('No negative numbers')

        # There's recursion limits on the evaluation method, so limit things here
        totalDice += number
        if totalDice > 1000:
            raise RuntimeError('Numbers too big')

        rolls = []
        for r in range(number):
            rolls.append(crypto.randint(1, limit))

        if number == 1:
            string_result = str(sum(rolls))
        else:
            string_result = ' + '.join(str(x) for x in rolls)

        return string_result
    except Exception as e:
        if 'No negative numbers' in str(e) or 'Numbers too big' in str(e):
            raise
        else:
            raise RuntimeError('Bad dice format')


# Figure out what a roll means and evaluate any expressions
async def parse_roll(dice_string):
    if dice_string == 'stats':
        response = await stats()
        return Message(message=response)

    LOGGER.debug('Dice.parse_roll: request, %s', dice_string)

    global totalDice
    totalDice = 0

    dice_string = dice_string.replace(' ', '')
    try:
        dice_array = split_string(dice_string, '+')
        dice_array = split_array(dice_array, '-')
        dice_array = split_array(dice_array, '*')
        dice_array = split_array(dice_array, '/')
        dice_array = split_array(dice_array, '^')
        dice_array = split_array(dice_array, '(')
        dice_array = split_array(dice_array, ')')
    except Exception as e:
        LOGGER.exception(e)
        return Message(message='Tell Ian whatever you just tried to do.')

    # Roll for an NdM parts and substitute in the result in parenthesis
    for index, item in enumerate(dice_array):
        if 'd' in item:
            try:
                string_result = roll_dice(item)
                del dice_array[index]
                dice_array.insert(index, '({0})'.format(string_result))
            except RuntimeError as e:
                if 'Bad dice format' in str(e):
                    LOGGER.debug('Dice.parse_roll: bad dice format')
                    return Message(message='Use an NdM format for rolls please.')
                elif 'Numbers too big' in str(e):
                    LOGGER.debug('Dice.parse_roll: numbers too big')
                    return Message(message='You ask for too much.')
                else:
                    LOGGER.exception(e)
                    return Message(message='Tell Ian whatever you just tried to do')

    result_string = ''.join(dice_array)

    # Attempt to evaluate the expression
    nsp = NumericStringParser()
    try:
        result = nsp.eval(result_string.replace(' ', ''))
    except ParseException:
        LOGGER.debug('Dice.parse_roll: could not evaluate %s', result_string)
        return Message(message='Bad expression')
    except RecursionError:
        LOGGER.debug('Dice.parse_roll: recursion limit reached.')
        return Message(message='Sorry, there are too many operations needed to evaluate that')
    except OverflowError:
        LOGGER.debug('Dice.parse_roll: overflow error')
        return Message(message='Ahhhh! Sorry, the result was too big.')

    # Convert to integer, if possible
    if not isinstance(result, complex):
        if result == int(result):
            result = int(result)
        else:
            result = round(result, 4)
    result_string += '\n\t = {0}'.format(result)

    # Tell discord message to ignore * use for italics
    result_string.replace('*', '\*')

    # Discord puts a 2000 character limit on messages
    LOGGER.debug('Dice.parse_roll: response, %s', result_string)
    return Message(message=result_string, cleanup_original=False, cleanup_self=False)


async def stats():
    LOGGER.debug('Dice.stats: request')
    rounds = []
    for i in range(6):
        r = []
        for j in range(4):
            roll = crypto.randint(1, 6)
            r.append(roll)
        rounds.append(r)

    string = ''
    for r in rounds:
        min_index = r.index(min(r))
        for index, value in enumerate(r):
            if index == min_index:
                string = string + '~~' + str(value) + '~~ + '
            else:
                string = string + str(value) + ' + '
        string = string[:-3]
        r.remove(min(r))
        string += ' = ' + str(sum(r)) + '\n'

    LOGGER.debug('Dice.stats: response, %s', string)
    return string

