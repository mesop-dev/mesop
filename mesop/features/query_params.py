from typing import Callable, Iterator, MutableMapping, Sequence

from mesop.runtime import runtime
from mesop.runtime.context import Context


class QueryParams(MutableMapping[str, str]):
  def __init__(self, get_context: Callable[[], Context]):
    self._get_context = get_context

  def __iter__(self) -> Iterator[str]:
    return iter(self._get_context().query_params())

  def __len__(self) -> int:
    return len(self._get_context().query_params())

  def __str__(self) -> str:
    return str(self._get_context().query_params())

  def __getitem__(self, key: str) -> str:
    # Returns the first value associated with the key to match
    # the web API:
    # https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams/get
    return self._get_context().query_params()[key][0]

  def get_all(self, key: str) -> Sequence[str]:
    if key not in self._get_context().query_params():
      return tuple()
    return tuple(self._get_context().query_params()[key])

  def __delitem__(self, key: str) -> None:
    self._get_context().set_query_param(key=key, value=None)

  def __setitem__(self, key: str, value: str | Sequence[str]) -> None:
    self._get_context().set_query_param(key=key, value=value)


query_params = QueryParams(lambda: runtime().context())
