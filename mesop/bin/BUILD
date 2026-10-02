load("//build_defs:defaults.bzl", "THIRD_PARTY_PY_ABSL_PY", "py_binary")

package(
    default_visibility = ["//build_defs:mesop_internal"],
)

py_binary(
    name = "bin",
    srcs = ["bin.py"],
    data = [
        "//mesop:example_index",  # TODO: remove
        "//mesop/web/src/app/editor:web_package",
        "//mesop/web/src/app/prod:web_package",
    ],
    main = "bin.py",
    deps = [
        "//mesop",  # Keep dep to ensure the entire Mesop library is loaded.
        "//mesop/runtime",
        "//mesop/server",
    ] + THIRD_PARTY_PY_ABSL_PY,
)
