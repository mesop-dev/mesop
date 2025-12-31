import mesop as me


@me.page(
  path="/testing/cors_allow_all",
  title="CORS: Allow All Origins",
  security_policy=me.SecurityPolicy(
    allowed_cors_origins=["*"],
  ),
)
def page_cors_allow_all():
  me.text("CORS - Allow All Origins")


@me.page(
  path="/testing/cors_specific_origin",
  title="CORS: Specific Origin",
  security_policy=me.SecurityPolicy(
    allowed_cors_origins=["http://example.com", "https://example.org"],
  ),
)
def page_cors_specific_origin():
  me.text("CORS - Specific Origins")


@me.page(
  path="/testing/cors_disabled",
  title="CORS: Disabled",
)
def page_cors_disabled():
  me.text("CORS - Disabled (no CORS headers)")
