from typing import Sequence

from mesop.features.query_params import (
  QueryParams,
)
from mesop.runtime import runtime
from mesop.utils.url_utils import remove_url_query_param
from mesop.warn import warn


def navigate(
  url: str,
  *,
  query_params: dict[str, str | Sequence[str]] | QueryParams | None = None,
  open_in_new_tab: bool = False,
) -> None:
  """
  Navigates to the given URL.

  Args:
    url: The URL to navigate to.
    query_params: A dictionary of query parameters to include in the URL, or `me.query_params`. If not provided, all current query parameters will be removed.
    open_in_new_tab: Whether to open the URL in a new tab. Defaults to False.
  """
  cleaned_url = remove_url_query_param(url)
  if url != cleaned_url:
    warn(
      "Used me.navigate to navigate to a URL with query params. The query params have been removed. "
      "Instead pass the query params using the keyword argument like this: "
      "me.navigate(url, query_params={'key': 'value'})"
    )
  if isinstance(query_params, QueryParams):
    query_params = {key: query_params.get_all(key) for key in query_params}

  # Clear the query params because the query params will
  # either be replaced with the new query_params or emptied (in server.py).
  runtime().context().query_params().clear()
  runtime().context().navigate(cleaned_url, query_params, open_in_new_tab)
