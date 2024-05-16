from pathlib import Path
from typing import Any, Final, Literal, cast

from rt_bi_commons.Base.TransitionParser import Discard, Token, TransitionParser, TransitionTransformer, Tree, UnexpectedToken
from rt_bi_commons.Utils import Ros


class PredicateToQueryName(TransitionTransformer):
	def NOT(self, _: Any) -> Any: return Discard
	def connector(self, _: Any) -> Any: return Discard
	def value(self, _: Any) -> Any: return Discard
	def test(self, _: Any) -> Any: return Discard

	def simple_expression(self, subExpressions: list[str]) -> str:
		if len(subExpressions) != 1: raise UnexpectedToken(subExpressions, {"1 strings: variable."})
		return subExpressions[0]

	def property_seq(self, variables: list[str]) -> str:
		return variables[0]

PREDICATE_VARNAME_PLACEHOLDER: Final = "?predicate_varname"
class TemporalPredicateToVariable(TransitionTransformer):
	def EQ(self, _: Any) -> Literal["="]: return "="
	def connector(self, _: Token) -> Any: raise UnexpectedToken(_, {"No connectors are expected in a single predicate."})
	def value(self, v: list[str]) -> str: return v[0]
	def test(self, t: list[str]) -> str: return t[0]

	def simple_expression(self, subExpressions: list[str]) -> str:
		if len(subExpressions) != 3: raise UnexpectedToken(subExpressions, {"3 strings: variable, test, value"})
		return f"BIND ({subExpressions[0]} {subExpressions[1]} {subExpressions[2]} AS {PREDICATE_VARNAME_PLACEHOLDER})"

	def property_seq(self, variables: list[str]) -> str:
		return f"?{variables[-1]}"

class SpatialPredicateToVariable(TransitionTransformer):
	def EQ(self, _: Any) -> Literal["="]: return "="
	def connector(self, _: Token) -> Any: raise UnexpectedToken(_, {"No connectors are expected in a single predicate."})
	def value(self, v: list[str]) -> str: return v[0]
	def test(self, t: list[str]) -> str: return t[0]

	def simple_expression(self, subExpressions: list[str]) -> str:
		if len(subExpressions) != 3: raise UnexpectedToken(subExpressions, {"3 strings: variable, test, value"})
		return f"BIND ({subExpressions[0]} {subExpressions[1]} {subExpressions[2]} AS {PREDICATE_VARNAME_PLACEHOLDER})"

	def property_seq(self, variables: list[str]) -> str:
		return f"?{variables[-1]}"

class PredicateToQueryStr:
	def __init__(
		self,
		namespace: Literal["spatial", "temporal"],
		baseDir: str,
		transitionGrammarDir: str,
		transitionGrammarFileName: str,
		sparqlDir: str,
		orderPlaceholder: str,
		selectorPlaceholder: str,
		variablesPlaceholder: str,
	) -> None:
		super().__init__()
		self.__namespace: Literal["spatial", "temporal"] = namespace
		self.__baseDir = baseDir
		self.__sparqlDir = sparqlDir
		self.__transitionParser = TransitionParser(baseDir, transitionGrammarDir, transitionGrammarFileName)
		self.__orderPlaceholder = orderPlaceholder
		self.__selectorPlaceholder = selectorPlaceholder
		self.__variablesPlaceholder = variablesPlaceholder
		return

	def __regexMatchPlaceholders(self, queryName: str, placeholder: str) -> str:
		raise NotImplementedError(f"REGEX MATCH: q = {queryName}, placeholder = {placeholder}")
		queryContent = Path(self.__baseDir, self.__sparqlDir, self.__queryFiles[queryName]).read_text()
		import re
		pattern = f"{placeholder}(.*){placeholder}"
		result = re.search(pattern, queryContent, re.RegexFlag.DOTALL)
		if result: return result.group(1)
		raise RuntimeError(f"The query file for variable \"{queryName}\" does not contain the required placeholder comments.")

	def __toBind(self, parsedPred: Tree[str], index: int) -> tuple[str, str]:
		predicateXfmr = SpatialPredicateToVariable() if self.__namespace == "spatial" else TemporalPredicateToVariable()
		bindStatement = cast(str, predicateXfmr.transform(parsedPred))
		if bindStatement == "": return ("", "")
		varName = f"?p_{index}"
		bindStatement = bindStatement.replace(PREDICATE_VARNAME_PLACEHOLDER, varName)
		return (bindStatement, varName)

	def transformPredicate(self, predicate: str, index: int) -> tuple[str, str, str, str]:
		parsedPred = self.__transitionParser.parse(predicate)
		parsedPred = cast(Tree[str], parsedPred)
		# For predicates, we add the bound boolean variables rather than the sparql variable
		(whereClause, _, orders) = self.selector(PredicateToQueryName().transform(parsedPred))
		(varBindings, variables) = self.__toBind(parsedPred, index)
		return (whereClause, variables, varBindings, orders)

	def selector(self, propertySeq: str) -> tuple[str, str, str]:
		if propertySeq == "": return ("", "", "")
		whereClause = self.__regexMatchPlaceholders(propertySeq, self.__selectorPlaceholder)
		try: # Not all queries have variables
			variables = self.__regexMatchPlaceholders(propertySeq, self.__variablesPlaceholder)
		except:
			variables = ""
		try: # Not all queries have order by
			orders = self.__regexMatchPlaceholders(propertySeq, self.__orderPlaceholder)
		except:
			orders = ""
		return (whereClause, variables, orders)
