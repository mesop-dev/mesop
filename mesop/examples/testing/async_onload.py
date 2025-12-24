"""
Test script to verify async on_load support.
This reproduces the issue from GitHub issue #1300.
"""

import asyncio

import mesop as me


@me.stateclass
class State:
  message: str = ""


async def async_on_load(e: me.LoadEvent):
  """Async generator on_load handler."""
  state = me.state(State)
  state.message = "Loading..."
  yield

  # Simulate async operation
  await asyncio.sleep(0.1)

  state.message = "Loaded from async generator!"
  yield


async def async_coroutine_on_load(e: me.LoadEvent):
  """Async coroutine on_load handler (no yield)."""
  state = me.state(State)
  await asyncio.sleep(0.1)
  state.message = "Loaded from coroutine!"


@me.page(path="/async_gen", on_load=async_on_load)
def page_async_gen():
  state = me.state(State)
  me.text(f"Async Generator: {state.message}")


@me.page(path="/async_coro", on_load=async_coroutine_on_load)
def page_async_coro():
  state = me.state(State)
  me.text(f"Async Coroutine: {state.message}")
