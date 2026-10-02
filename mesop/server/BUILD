load(
    "//build_defs:defaults.bzl",
    "THIRD_PARTY_PY_ABSL_PY",
    "THIRD_PARTY_PY_DOTENV",
    "THIRD_PARTY_PY_FIREBASE_ADMIN",
    "THIRD_PARTY_PY_FLASK",
    "THIRD_PARTY_PY_FLASK_SOCK",
    "THIRD_PARTY_PY_GREENLET",
    "THIRD_PARTY_PY_MSGPACK",
    "THIRD_PARTY_PY_PYTEST",
    "THIRD_PARTY_PY_SQLALCHEMY",
    "THIRD_PARTY_PY_WATCHDOG",
    "py_library",
    "py_test",
)

package(
    default_visibility = ["//build_defs:mesop_internal"],
)

STATE_SESSIONS_SRCS = [
    "config.py",
    "state_session.py",
]

py_library(
    name = "server",
    srcs = glob(
        ["*.py"],
        exclude = [
            "*_test.py",
        ] + STATE_SESSIONS_SRCS,
    ),
    deps = [
               "//mesop/cli:execute_module",
               "//mesop/component_helpers",
               "//mesop/env",
               "//mesop/events",
               "//mesop/exceptions",
               "//mesop/protos:ui_py_pb2",
               "//mesop/runtime",
               "//mesop/utils",
               "//mesop/warn",
           ] + THIRD_PARTY_PY_ABSL_PY +
           THIRD_PARTY_PY_FLASK +
           THIRD_PARTY_PY_FLASK_SOCK +
           THIRD_PARTY_PY_WATCHDOG,
)

py_library(
    name = "state_sessions",
    srcs = STATE_SESSIONS_SRCS,
    deps = [
               "//mesop/dataclass_utils",
               "//mesop/exceptions",
           ] + THIRD_PARTY_PY_MSGPACK +
           THIRD_PARTY_PY_DOTENV,
)

py_test(
    name = "config_test",
    srcs = ["config_test.py"],
    deps = [":server"] + THIRD_PARTY_PY_PYTEST,
)

py_test(
    name = "state_session_test",
    srcs = ["state_session_test.py"],
    deps = [":server"] +
           THIRD_PARTY_PY_PYTEST +
           THIRD_PARTY_PY_FIREBASE_ADMIN +
           THIRD_PARTY_PY_SQLALCHEMY +
           THIRD_PARTY_PY_GREENLET,
)

py_test(
    name = "wsgi_app_test",
    srcs = ["wsgi_app_test.py"],
    deps = [":server"] + THIRD_PARTY_PY_PYTEST,
)

py_test(
    name = "static_file_serving_test",
    srcs = ["static_file_serving_test.py"],
    deps = [":server"] + THIRD_PARTY_PY_PYTEST,
)
