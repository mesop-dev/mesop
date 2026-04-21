from plotly_component import plotly_component

import mesop as me


def on_load(e: me.LoadEvent):
  me.set_theme_mode("system")


@me.page(
  on_load=on_load,
  path="/plotly",
  # CAUTION: this disables an important web security feature and
  # should not be used for most mesop apps.
  #
  # Disabling trusted types because plotly uses DomParser#parseFromString
  # which violates TrustedHTML assignment.
  security_policy=me.SecurityPolicy(
    allowed_iframe_parents=["https://mesop-dev.github.io"],
    allowed_script_srcs=[
      "https://cdn.jsdelivr.net",
      "https://cdn.plot.ly",
    ],
    dangerously_disable_trusted_types=True,
  ),
)
def page():
  plotly_component()
