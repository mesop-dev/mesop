# Mesop: Build delightful web apps quickly in Python 🚀

> [!WARNING]
> **Mesop is no longer maintained as of September 30, 2026.** No further updates, bug fixes, or support will be provided.

[![PyPI](https://img.shields.io/pypi/v/mesop)](https://pypi.org/project/mesop/)
[![PyPI downloads](https://img.shields.io/pypi/dm/mesop)](https://pypi.org/project/mesop/)
[![Twitter follow](https://img.shields.io/twitter/follow/mesop_dev?style=social&label=follow)](https://twitter.com/mesop_dev)

- If you're interested in learning how to use Mesop, please [read our main docs](https://mesop-dev.github.io/mesop/).

- If you're interested in contributing to the core Mesop framework, please [read our contributing guide](https://mesop-dev.github.io/mesop/internal/contributing/).

### Used at Google for rapid internal app development

Mesop is a Python-based UI framework that allows you to rapidly build web apps like demos and internal apps:

**Intuitive for UI novices ✨**

- Write UI in idiomatic Python code
- Easy to understand reactive UI paradigm
- Ready to use components

**Frictionless developer workflows 🏎️**

- Hot reload so the browser automatically reloads and preserves state
- Rich IDE support with strong type safety

**Flexible for delightful demos 🤩**

- Build custom UIs _without_ writing Javascript/CSS/HTML
- Compose your UI into components, which are just Python functions

## Write your first Mesop app in less than 10 lines of code...

[Demo app](https://mesop-dev.github.io/mesop/demo/?demo=text_to_text)

```python
import mesop as me
import mesop.labs as mel


@me.page(path="/text_to_text", title="Text to Text Example")
def app():
  mel.text_to_text(
    upper_case_stream,
    title="Text to Text Example",
  )


def upper_case_stream(s: str):
  return "Echo: " + s.capitalize()
```

</div>

## Try it

### Colab

You can try [Mesop on Colab](https://colab.research.google.com/github/mesop-dev/mesop/blob/main/notebooks/mesop_colab_getting_started.ipynb)!

### Locally

**Step 1:** Install it

```sh
pip install mesop
```

**Step 2:** Copy the example above into `main.py`

**Step 3:** Run the app

```sh
mesop main.py
```

Learn more in [Getting Started](https://mesop-dev.github.io/mesop/getting-started/installing/).

## Reporting a security issue

If you identify a security vulnerability with Mesop, please file a [GitHub security issue](https://github.com/mesop-dev/mesop/security/policy) and we will promptly respond to it.

## Disclaimer

_This is not an officially supported Google product._
