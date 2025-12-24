"""Utilities for handling async generators and coroutines in Mesop event handlers."""

import asyncio
import types
from typing import Generator


def run_async_generator(
  agen: types.AsyncGeneratorType[None, None],
) -> Generator[None, None, None]:
  """Run an async generator by iterating through it using an event loop.

  Args:
    agen: The async generator to run

  Yields:
    None for each iteration of the async generator
  """
  loop = get_or_create_event_loop()
  try:
    while True:
      yield loop.run_until_complete(agen.__anext__())
  except StopAsyncIteration:
    pass


def run_coroutine(coroutine: types.CoroutineType):
  """Run a coroutine using an event loop and return its result.

  Args:
    coroutine: The coroutine to run

  Returns:
    The result of the coroutine
  """
  loop = get_or_create_event_loop()
  return loop.run_until_complete(coroutine)


def get_or_create_event_loop():
  """Get the current event loop or create a new one if none exists.

  Returns:
    The asyncio event loop
  """
  try:
    return asyncio.get_running_loop()
  except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop
