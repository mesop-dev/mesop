import mesop as me


def navigate(event: me.ClickEvent):
  me.navigate("/examples/navigate/about")


@me.page(path="/examples/navigate/home")
def home():
  me.text("This is the home page")
  me.button("navigate to about page", on_click=navigate)


@me.page(path="/examples/navigate/about")
def about():
  me.text("This is the about page")
