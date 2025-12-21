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

    state.message = "Loaded!"
    yield


async def async_coroutine_on_load(e: me.LoadEvent):
    """Async coroutine on_load handler (no yield)."""
    state = me.state(State)
    await asyncio.sleep(0.1)
    state.message = "Loaded from coroutine!"


def sync_generator_on_load(e: me.LoadEvent):
    """Sync generator on_load handler."""
    state = me.state(State)
    state.message = "Loading sync..."
    yield
    state.message = "Loaded sync!"
    yield


@me.page(path="/async_gen", on_load=async_on_load)
def page_async_gen():
    state = me.state(State)
    me.text(f"Async Generator: {state.message}")


@me.page(path="/async_coro", on_load=async_coroutine_on_load)
def page_async_coro():
    state = me.state(State)
    me.text(f"Async Coroutine: {state.message}")


@me.page(path="/sync_gen", on_load=sync_generator_on_load)
def page_sync_gen():
    state = me.state(State)
    me.text(f"Sync Generator: {state.message}")


if __name__ == "__main__":
    print("Testing async on_load support...")
    print("Run with: mesop test_async_on_load.py")
    print("Then visit:")
    print("  - http://localhost:32123/async_gen (async generator)")
    print("  - http://localhost:32123/async_coro (async coroutine)")
    print("  - http://localhost:32123/sync_gen (sync generator)")
