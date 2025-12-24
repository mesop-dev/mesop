import mesop as me


@me.page(path="/navigate_new_tab")
def page():
  me.text("Navigate in New Tab Examples", type="headline-4")
  me.divider()

  me.text("Open relative URLs in new tab:", type="headline-6")
  me.button("Open /examples/navigate/about in new tab", on_click=navigate_relative_new_tab)
  me.button("Open /examples/navigate/home in new tab", on_click=navigate_relative_home_new_tab)

  me.divider()

  me.text("Open absolute URLs in new tab:", type="headline-6")
  me.button("Open Google in new tab", on_click=navigate_absolute_new_tab)
  me.button("Open Example.com in new tab", on_click=navigate_example_new_tab)

  me.divider()

  me.text("Open with query params in new tab:", type="headline-6")
  me.button("Open with query params", on_click=navigate_with_params_new_tab)

  me.divider()

  me.text("Traditional navigation (same tab):", type="headline-6")
  me.button("Navigate to /examples/navigate/about (same tab)", on_click=navigate_same_tab)


def navigate_relative_new_tab(e: me.ClickEvent):
  me.navigate("/examples/navigate/about", open_in_new_tab=True)


def navigate_relative_home_new_tab(e: me.ClickEvent):
  me.navigate("/examples/navigate/home", open_in_new_tab=True)


def navigate_absolute_new_tab(e: me.ClickEvent):
  me.navigate("https://google.com", open_in_new_tab=True)


def navigate_example_new_tab(e: me.ClickEvent):
  me.navigate("http://example.com", open_in_new_tab=True)


def navigate_with_params_new_tab(e: me.ClickEvent):
  me.navigate(
    "/examples/query_params/page_2",
    query_params={"foo": "bar", "baz": "qux"},
    open_in_new_tab=True,
  )


def navigate_same_tab(e: me.ClickEvent):
  me.navigate("/examples/navigate/about")
