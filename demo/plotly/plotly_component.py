import mesop as me


@me.web_component(path="./plotly_component.js")
def plotly_component():
  return me.insert_web_component(name="plotly-component")
