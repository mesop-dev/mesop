# Quickstart

Let's build a simple interactive Mesop app.

## Before you start

Make sure you've installed Mesop, otherwise please follow the [Installing Guide](./installing.md).

## Starter kit

The simplest way to get started with Mesop is to use the starter kit by running `mesop init`. You can also copy and paste the code.

```python
--8<-- "mesop/examples/starter_kit/starter_kit.py"
```

## Running a Mesop app

Once you've created your Mesop app using the starter kit, you can run the Mesop app by running the following command in your terminal:

```sh
mesop main.py
```

> If you've named it something else, replace `main.py` with the filename of your Python module.

Open the URL printed in the terminal (i.e. http://localhost:32123) in the browser to see your Mesop app loaded.

## Hot reload

If you make changes to the code, the Mesop app should be automatically hot reloaded. This means that you can keep the `mesop` CLI command running in the background in your terminal and your UI will automatically be updated in the browser.

You can also manually trigger a hot reload using a keyboard shortcut:

- **MacOS**: `Cmd + Shift + R`
- **ChromeOS**: `Alt + Shift + R`
- **Windows/Linux**: `Ctrl + Shift + R`

## Next steps

Learn more about the core concepts of Mesop as you learn how to build your own Mesop app:

<a href="../core-concepts" class="next-step">
    Core Concepts
</a>
