load("//build_defs:defaults.bzl", "py_library")

package(
    default_visibility = ["//build_defs:mesop_examples"],
)

py_library(
    name = "demo",
    srcs = glob([
        "*.py",
        "*/*.py",
    ]),
    data = [
        ":screenshots",
        ":web_component_files",
    ],
    deps = [
        "//mesop",
        "//mesop/labs",
    ],
)

# JS/CSS files for subdirectory web component demos
filegroup(
    name = "web_component_files",
    srcs = glob([
        "*/*.js",
        "*/*.css",
    ]),
)

# Make source files available for distribution via pkg_npm
filegroup(
    name = "screenshots",
    srcs = glob(["screenshots/*"]),
)
