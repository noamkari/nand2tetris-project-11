"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
from VMWriter import *
from SymbolTable import *


# try

class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """

    def __init__(self, input_stream: "JackTokenizer", output_stream) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        # Your code goes here!
        # Note that you can write to output_stream like so:
        # output_stream.write("Hello world! \n")
        self._class_name = ""
        self._output_stream = output_stream
        self._input_stream = input_stream
        self.VMWriter = VMWriter(output_stream)
        self.type_dict = {"KEYWORD": "keyword", "SYMBOL": "symbol",
                          "INT_CONST": "integerConstant",
                          "STRING_CONST": "stringConstant",
                          "IDENTIFIER": "identifier"}
        # self.binary_op = {'+', '-', '*', '/', '|', '=', '&lt;', '&gt;',
        #                   '&amp;'}
        self.binary_op_dct = {'+': '+', '-': '-', '*': '*', '/': '/', '|': '|',
                              '=': '=', '<': '&lt;', '>': '&gt;', '&': '&amp;'}
        self.unary_op = {'-', '~', '^', '#'}

        self.binary_op_dct_vm = {'+': 'ADD', '-': 'SUB', '*': '*', '/': '/',
                                 '|': 'OR',
                                 '=': 'EQ', '<': 'LT', '>': 'GT',
                                 '&': 'AND'}
        self.unary_op_vm = {'-': 'NEG', '~': 'NOT', '^': 'SHIFTLEFT',
                            '#': 'SHIFRIGHT'}

        self.keyword_constant = {'true', 'false', 'null', 'this'}
        self.keyword_constant_dct = {'true': ['CONST', 1],
                                     'false': ['CONST', 0],
                                     'null': ['CONST', 0],
                                     'this': ['POINTER', 0]}
        self.classVarDec = ['static', 'field']
        self.subroutineDec = ['constructor', 'method', 'function']
        self.symbol_table = SymbolTable()
        self.if_while_labels_count = 0

    def compile_class(self) -> None:
        """Compiles a complete class."""
        # Your code goes here!
        self._output_stream.write("<class>\n")
        self.write_token()  # class
        self._class_name = self._input_stream.cur_token()
        self.write_token()  # class_name
        self.write_token()  # {
        while self._input_stream.cur_token() in self.classVarDec \
                or self._input_stream.cur_token() in self.subroutineDec:
            if self._input_stream.cur_token() in self.classVarDec:
                self.compile_class_var_dec()
            elif self._input_stream.cur_token() in self.subroutineDec:
                self.compile_subroutine()
        self.write_token()  # }
        self._output_stream.write("</class>\n")

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        # Your code goes here!
        self._output_stream.write("<classVarDec>\n")
        kind = self._input_stream.cur_token()
        self.write_token()  # static or field
        type = self._input_stream.cur_token()
        self.write_token()  # var type
        names = []
        names.append(self._input_stream.cur_token())
        self.write_token()  # var name
        while self._input_stream.cur_token() == ",":
            self.write_token()  # ","
            names.append(self._input_stream.cur_token())
            self.write_token()  # var name
        self.write_token()  # ;
        for name in names:
            self.symbol_table.define(name, type, kind)
        self._output_stream.write("</classVarDec>\n")

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        # Your code goes here!
        # Your code goes here!
        self.symbol_table.start_subroutine()
        self._output_stream.write("<subroutineDec>\n")
        func_type = self._input_stream.cur_token()
        if (func_type == "method"):
            self.symbol_table.define('this', self._class_name, 'ARG')
        self.write_token()  # get field \ method \ contracture
        self.write_token()  # get subroutine return type \ 'constructor'
        sub_name = self._input_stream.cur_token()
        self.write_token()  # get subroutine name \ 'new'
        self.write_token()  # get '(' symbol
        self.compile_parameter_list()
        self.write_token()  # get ')' symbol
        self.compile_subroutine_body(func_type, sub_name)
        # self.write_token() #'}'
        self._output_stream.write("</subroutineDec>\n")

    def compile_subroutine_body(self, func_type, name):
        self._output_stream.write("<subroutineBody>\n")
        self.write_token()  # '{'
        while self._input_stream.cur_token() == 'var':
            self.compile_var_dec()
        vars = self.symbol_table.var_count('VAR')
        self.VMWriter.write_function(name, vars)
        if func_type == 'method':
            # Save self at pointer
            self.VMWriter.write_push('ARG', 0)
            self.VMWriter.write_pop('POINTER', 0)
        if func_type == 'contracture':
            # Memory allocates for all fields
            fields = self.symbol_table.var_count('FIELD')
            self.VMWriter.write_push('CONST', fields)
            self.VMWriter.write_call('Memory.alloc', 1)
            # Save allocated memory at pointer
            self.VMWriter.write_pop('POINTER', 0)
        self.compile_statements()
        self.write_token()  # '}'
        self._output_stream.write("</subroutineBody>\n")

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        # Your code goes here!
        params = 0
        self._output_stream.write("<parameterList>\n")
        while self._input_stream.cur_token() != ")":
            params += 1
            type = self._input_stream.cur_token()
            name = self._input_stream.cur_token()
            self.symbol_table.define(name, type, 'ARG')
            self.write_token()
        self._output_stream.write("</parameterList>\n")

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        # Your code goes here!
        self._output_stream.write("<varDec>\n")
        self.write_token()  # var
        type = self._input_stream.cur_token()
        self.write_token()  # type
        names = []
        names.append(self._input_stream.cur_token())
        self.write_token()  # var name
        while self._input_stream.cur_token() == ',':
            self.write_token()  # ","
            names.append(self._input_stream.cur_token())
            self.write_token()  # var name
        self.write_token()  # ';'
        for name in names:
            self.symbol_table.define(name, type, 'VAR')

        self._output_stream.write("</varDec>\n")

    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        # Your code goes here!
        self._output_stream.write("<statements>\n")
        while self._input_stream.cur_token() in ["let", "if", "while", "do",
                                                 "return"]:
            if self._input_stream.cur_token() == "let":
                self.compile_let()
            elif self._input_stream.cur_token() == "if":
                self.compile_if()
            elif self._input_stream.cur_token() == "while":
                self.compile_while()
            elif self._input_stream.cur_token() == "do":
                self.compile_do()
            elif self._input_stream.cur_token() == "return":
                self.compile_return()
        self._output_stream.write("</statements>\n")

    def compile_do(self) -> None:
        """Compiles a do statement."""
        # Your code goes here!
        self._output_stream.write("<doStatement>\n")
        self.write_token()  # do

        identifier = self._input_stream.cur_token()
        kind = self.symbol_table.kind_of(identifier)

        self.write_token()  # identifier
        while self._input_stream.cur_token() == ".":
            self.write_token()  # '.'
            identifier += '.' + self._input_stream.cur_token()
            self.write_token()  # subroutine name
        self.write_token()  # '('
        num_args = self.compile_expression_list()
        self.VMWriter.write_call(identifier, num_args)
        self.write_token()  # ')'
        self.VMWriter.write_pop('TEMP', 0)
        self.write_token()  # ;

        self._output_stream.write("</doStatement>\n")

    def compile_let(self) -> None:
        """Compiles a let statement."""
        # Your code goes here!
        self._output_stream.write("<letStatement>\n")
        self.write_token()  # let
        var_name = self._input_stream.cur_token()
        var_kind = self.symbol_table.kind_of(var_name)
        var_index = self.symbol_table.index_of(var_name)
        self.write_token()  # varName
        if self._input_stream.cur_token() == "[":
            self.write_token()  # [
            self.compile_expression()
            self.write_token()  # ]
        self.write_token()  # =
        self.compile_expression()
        self.write_token()  # ;
        self.VMWriter.write_pop(var_kind, var_index)
        self.VMWriter.write_push(var_kind, var_index)
        self._output_stream.write("</letStatement>\n")

    def compile_while(self) -> None:
        """Compiles a while statement."""
        # Your code goes here!
        self._output_stream.write("<whileStatement>\n")
        self.if_while_labels_count += 1
        self.VMWriter.write_label(f"label {self.if_while_labels_count}")
        self.write_token()  # while
        self.write_token()  # (
        self.compile_expression()
        self.write_token()  # )

        self.VMWriter.write_arithmetic("NEG")
        self.VMWriter.write_if(f"label {self.if_while_labels_count + 1}")
        self.write_token()  # {

        if_while_labels_count = self.if_while_labels_count  # for recursive
        self.if_while_labels_count += 1
        self.compile_statements()
        self.VMWriter.write_goto(f"label {if_while_labels_count}")
        self.VMWriter.write_label(f"label {if_while_labels_count + 1}")

        self.write_token()  # }
        self._output_stream.write("</whileStatement>\n")

    def compile_return(self) -> None:
        """Compiles a return statement."""
        # Your code goes here!
        self._output_stream.write("<returnStatement>\n")
        self.write_token()  # return
        while self._input_stream.cur_token() != ';':
            self.compile_expression()
        else:
            self.VMWriter.write_push('CONST', 0)
        self.write_token()  # ';'
        self.VMWriter.write_return()
        self._output_stream.write("</returnStatement>\n")

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        # Your code goes here!
        self._output_stream.write("<ifStatement>\n")
        self.write_token()  # if
        self.write_token()  # (
        self.compile_expression()
        self.write_token()  # )
        self.VMWriter.write_arithmetic("NEG")
        self.if_while_labels_count += 1
        self.VMWriter.write_if(f"label {self.if_while_labels_count}")

        if_while_labels_count = self.if_while_labels_count  # for recursive call
        self.if_while_labels_count += 1
        self.VMWriter.write_goto(f"label {if_while_labels_count + 1}")

        self.VMWriter.write_label(f"label {self.if_while_labels_count}")
        self.write_token()  # {
        self.compile_statements()
        self.write_token()  # }

        if self._input_stream.cur_token() == "else":
            self.write_token()  # else
            self.write_token()  # {
            self.compile_statements()
            self.write_token()  # }
        self.VMWriter.write_label(f"label {if_while_labels_count + 1}")

        self._output_stream.write("</ifStatement>\n")

    def compile_expression(self) -> None:
        """Compiles an expression."""
        # Your code goes here!
        self._output_stream.write("<expression>\n")
        self.compile_term()
        while self._input_stream.cur_token() in self.binary_op_dct_vm:
            self.compile_term()
            if self._input_stream.cur_token() == '*':
                self.VMWriter.write_call('Math.multiply', 2)
            elif self._input_stream.cur_token() == '/':
                self.VMWriter.write_call('Math.divide', 2)
            else:
                self.VMWriter.write_arithmetic(
                    self.binary_op_dct_vm[self._input_stream.cur_token()])
            self.write_token()  # op
        self._output_stream.write("</expression>\n")

    def compile_term(self) -> None:
        """Compiles a term. 
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        # Your code goes here!
        self._output_stream.write("<term>\n")
        if self._input_stream.token_type()  == 'INT_CONST':
            self.VMWriter.write_push('CONST', self._input_stream.cur_token())
            self.write_token()  # the number

        if self._input_stream.token_type() == 'STRING_CONST': #fixme: check
            string = self._input_stream.cur_token()
            self.VMWriter.write_push('CONST', string)
            self.VMWriter.write_call('String.new', 1)
            for char in string:
                self.VMWriter.write_push('CONST', ord(char))
                self.VMWriter.write_call('String.appendChar', 2)

        elif self._input_stream.cur_token() in self.keyword_constant:
            self.VMWriter.write_push(
                self.keyword_constant_dct[self._input_stream.cur_token()][0],
                self.keyword_constant_dct[self._input_stream.cur_token()][1])
            if self._input_stream.cur_token() == 'true':
                self.VMWriter.write_arithmetic('NEG')
            self.write_token()  # the keywordConstant

        elif self._input_stream.cur_token() in self.unary_op_vm:
            self.write_token()  # ~ or -
            self.compile_term()
            self.VMWriter.write_arithmetic('NEG')


        elif self._input_stream.token_type() == "IDENTIFIER":
            identifier = self._input_stream.token_type()
            self.write_token()  # identifier
            if self._input_stream.cur_token() == "[":  # fixme: check
                self.write_token()  # [
                self.compile_expression()
                self.write_token()  # ]
                # Compile array indexing
                kind = self.symbol_table.kind_of(identifier)
                index = self.symbol_table.index_of(identifier)
                self.VMWriter.write_push(kind, index)
                self.VMWriter.write_arithmetic('+')
                self.VMWriter.write_pop('POINTER', 1)
                self.VMWriter.write_push('THAT', 0)

            elif self._input_stream.cur_token() == "(":  # fixme: incomplited. should be expression list?
                self.write_token()  # (
                self.compile_expression()
                self.write_token()  # )
            elif self._input_stream.cur_token() == ".": # fixme:compileSubroutineCall(), like DoStatement
                self.write_token()  # '.' symbol
                identifier += '.' + self._input_stream.cur_token()
                self.write_token()  # subroutine name
                self.write_token()  # '(' symbol
                num_args = self.compile_expression_list()
                self.VMWriter.write_call(identifier, num_args)
                self.write_token()  # ')' symbol

        elif self._input_stream.cur_token() == "(":
            self.write_token()  # (
            self.compile_expression()
            self.write_token()  # )

        self._output_stream.write("</term>\n")

    def compile_expression_list(
            self) -> int:
        """Compiles a (possibly empty) comma-separated list of expressions."""
        # Your code goes here!
        self._output_stream.write("<expressionList>\n")
        num_args = 0
        if self._input_stream.cur_token() != ")":
            self.compile_expression()
            num_args += 1
            while self._input_stream.cur_token() == ",":
                self.write_token()  # ','
                self.compile_expression()
                num_args += 1
        self._output_stream.write("</expressionList>\n")
        return num_args

    def write_token(self):
        type = self.type_dict[self._input_stream.token_type()]

        if self._input_stream.cur_token() in self.binary_op_dct_vm:
            t = self.binary_op_dct_vm[self._input_stream.cur_token()]
        else:
            t = self._input_stream.cur_token()

        token = f"#<{type}> {t} </{type}>\n"
        self._output_stream.write(token)
        self._input_stream.advance()
