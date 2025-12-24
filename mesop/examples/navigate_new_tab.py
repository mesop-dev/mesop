import mesop as me


@me.page(path="/navigate_new_tab")
def page():
  me.text("Navigate to New Tab Example", type="headline-5")
  me.text("Click the buttons below to test navigation in new tabs:")
  
  with me.box(style=me.Style(margin=me.Margin.all(15))):
    me.button("Open about page in new tab", on_click=navigate_to_about_new_tab)
  
  with me.box(style=me.Style(margin=me.Margin.all(15))):
    me.button("Open about page in same tab", on_click=navigate_to_about_same_tab)
  
  with me.box(style=me.Style(margin=me.Margin.all(15))):
    me.button(
      "Open external URL in new tab", on_click=navigate_to_external_new_tab
    )
  
  with me.box(style=me.Style(margin=me.Margin.all(15))):
    me.button(
      "Open with query params in new tab",
      on_click=navigate_with_query_params_new_tab,
    )


def navigate_to_about_new_tab(e: me.ClickEvent):
  me.navigate("/about", open_in_new_tab=True)


def navigate_to_about_same_tab(e: me.ClickEvent):
  me.navigate("/about", open_in_new_tab=False)


def navigate_to_external_new_tab(e: me.ClickEvent):
  me.navigate("https://google.com", open_in_new_tab=True)


def navigate_with_query_params_new_tab(e: me.ClickEvent):
  me.navigate(
    "/query_params",
    query_params={"search": "test", "page": "1"},
    open_in_new_tab=True,
  )


@me.page(path="/about")
def about():
  me.text("About Page", type="headline-4")
  me.text("This is the about page opened from the navigation example.")
