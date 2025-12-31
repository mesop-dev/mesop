import mesop as me


@me.page(
  path="/testing/cors_allow_all",
  title="CORS: Allow All Origins",
  security_policy=me.SecurityPolicy(
    cors=me.CORS(
      allowed_origins=["*"],
    ),
  ),
)
def page_cors_allow_all():
  me.text("CORS - Allow All Origins")


@me.page(
  path="/testing/cors_specific_origin",
  title="CORS: Specific Origin",
  security_policy=me.SecurityPolicy(
    cors=me.CORS(
      allowed_origins=["http://example.com", "https://example.org"],
      allow_credentials=True,
    ),
  ),
)
def page_cors_specific_origin():
  me.text("CORS - Specific Origins")


@me.page(
  path="/testing/cors_custom_headers",
  title="CORS: Custom Headers",
  security_policy=me.SecurityPolicy(
    cors=me.CORS(
      allowed_origins=["http://example.com"],
      allowed_methods=["GET", "POST", "PUT", "DELETE"],
      allowed_headers=["Content-Type", "Authorization", "X-Custom-Header"],
      expose_headers=["X-Custom-Response-Header"],
      allow_credentials=True,
      max_age=3600,
    ),
  ),
)
def page_cors_custom_headers():
  me.text("CORS - Custom Headers Configuration")


@me.page(
  path="/testing/cors_disabled",
  title="CORS: Disabled",
)
def page_cors_disabled():
  me.text("CORS - Disabled (no CORS headers)")
