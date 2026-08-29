from typing import Any, Callable

from mesop.runtime import runtime


def serve(
  *,
  rule: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
  def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    runtime().register_handler(
      rule=rule,
      handler=func,
    )
    return func

  return decorator
