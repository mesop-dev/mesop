import mesop as me


@me.page(path="/navigate_new_tab/about")
def about():
  me.text("About Page", type="headline-4")
  me.text(
    "This is the about page. Use the buttons below to navigate to different pages, "
    "some of which will open in a new tab."
  )


@me.page(path="/navigate_new_tab")
def page():
  me.text("Navigate in New Tab Examples", type="headline-4")
  me.divider()

  me.text("Open internal pages in new tab:", type="headline-6")
  me.button(
    "Open /navigate_new_tab/about in new tab",
    on_click=navigate_about_new_tab,
  )

  me.divider()

  me.text("Open full website URLs in new tab:", type="headline-6")
  me.button("Open example.com in new tab", on_click=navigate_example_new_tab)

  me.divider()

  me.text("Open with query params in new tab:", type="headline-6")
  me.button("Open with query params", on_click=navigate_with_params_new_tab)

  me.divider()

  me.text("Open with url query params in new tab:", type="headline-6")
  me.button(
    "Open with url query params", on_click=navigate_with_url_params_new_tab
  )

  me.divider()

  me.text("Traditional navigation (same tab):", type="headline-6")
  me.button(
    "Navigate to /navigate_new_tab/about (same tab)",
    on_click=navigate_same_tab,
  )


def navigate_about_new_tab(e: me.ClickEvent):
  me.navigate("/navigate_new_tab/about", open_in_new_tab=True)


def navigate_example_new_tab(e: me.ClickEvent):
  me.navigate("https://example.com", open_in_new_tab=True)


def navigate_with_params_new_tab(e: me.ClickEvent):
  me.navigate(
    "/navigate_new_tab/about",
    query_params={"foo": "bar", "baz": "qux"},
    open_in_new_tab=True,
  )


def navigate_with_url_params_new_tab(e: me.ClickEvent):
  me.navigate(
    "/navigate_new_tab/about?foo=bar&baz=qux",
    open_in_new_tab=True,
  )


def navigate_same_tab(e: me.ClickEvent):
  me.navigate("/navigate_new_tab/about")
