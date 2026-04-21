from svg_icon_component import svg_icon

import mesop as me


def on_load(e: me.LoadEvent):
  me.set_theme_mode("system")


@me.page(
  on_load=on_load,
  path="/svg_icon",
  security_policy=me.SecurityPolicy(
    allowed_iframe_parents=["https://mesop-dev.github.io"],
    allowed_script_srcs=["https://cdn.jsdelivr.net"],
    allowed_connect_srcs=["https://cdn.jsdelivr.net"],
    dangerously_disable_trusted_types=True,
  ),
  title="svg-icon",
)
def page():
  with me.box(style=me.Style(width="200px", padding=me.Padding.all(20))):
    svg_icon(
      svg="""<svg aria-label="Lit" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 425 200" id="full"><view id="flame" viewBox="-132.5 0 160 200"></view><view id="name" viewBox="332.5 127.5 185 122"></view><symbol id="name-symbol" viewBox="240 78 185 122"><path fill="var(--lit-logo-text-color, black)" d="M394.5 78v28.8H425v15.6h-30.5V158c0 3.6.1 7.2.5 10.3.8 5.3 4 10.5 8.4 12.5 5.7 2.6 9.7 2.1 21.6 1.7l-2.9 17.2c-.8.4-4 .3-7 .3-7 0-33.4 2.5-38.8-24.7-.9-4.7-.7-9.5-.7-16.9v-35.8H362l.2-15.9h13.4V78zm-51.7 28.7v91.5H324v-91.5zm0-28.7v16.3h-19V78zm-83.6 102.2h48.2l-18 18H240V78h19.2z"></path></symbol><symbol id="flame-symbol" viewBox="0 0 160 200"><path fill="var(--lit-logo-dark-cyan, #00e8ff)" d="M40 120l20-60l90 90l-30 50l-40-40h-20"></path><path fill="var(--lit-logo-dark-blue, #283198)" d="M80 160 L80 80 L120 40 L 120 120 M0 160 L40 200 L40 120 L20 120"></path><path fill="var(--lit-logo-blue, #324fff)" d="M40 120v-80l40-40v80M120 200v-80l40-40v80M0 160v-80l40 40"></path><path fill="var(--lit-logo-cyan, #0ff)" d="M40 200v-80l40 40"></path></symbol><use href="#name-symbol" x="332.5" y="127.5" transform="scale(0.61)"></use><use href="#flame-symbol" x="-132.5"></use></svg>"""
    )
