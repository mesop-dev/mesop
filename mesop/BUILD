# Description:
#   Mesop is a Python UI framework that allows you to build web demos.
load("//build_defs:defaults.bzl", "py_library")

package(
    default_visibility = ["//build_defs:mesop_internal"],
)

licenses(["notice"])

exports_files(["LICENSE"])

py_library(
    name = "mesop",
    srcs = [
        "__init__.py",
        "py.typed",
    ],
    data = glob(
        [
            ".env",
            "static/**/*",
        ],
    ),
    visibility = ["//build_defs:mesop_users"],
    deps = [
        ":version",
        # REF(//scripts/scaffold_component.py):insert_component_import
        "//mesop/components/accordion:py",
        "//mesop/components/expansion_panel:py",
        "//mesop/components/card_header:py",
        "//mesop/components/card_actions:py",
        "//mesop/components/card_content:py",
        "//mesop/components/card:py",
        "//mesop/components/button_toggle:py",
        "//mesop/components/date_range_picker:py",
        "//mesop/components/datepicker:py",
        "//mesop/components/autocomplete:py",
        "//mesop/components/link:py",
        "//mesop/components/html:py",
        "//mesop/components/uploader:py",
        "//mesop/components/code:py",
        "//mesop/components/embed:py",
        "//mesop/components/table:py",
        "//mesop/components/sidenav:py",
        "//mesop/components/video:py",
        "//mesop/components/audio:py",
        "//mesop/components/image:py",
        "//mesop/components/slider:py",
        "//mesop/components/plot:py",
        "//mesop/components/select:py",
        "//mesop/components/radio:py",
        "//mesop/components/slide_toggle:py",
        "//mesop/components/progress_spinner:py",
        "//mesop/components/progress_bar:py",
        "//mesop/components/icon:py",
        "//mesop/components/divider:py",
        "//mesop/components/badge:py",
        "//mesop/components/tooltip:py",
        "//mesop/components/input:py",
        "//mesop/components/markdown:py",
        "//mesop/components/box:py",
        "//mesop/components",
        "//mesop/components/button:py",
        "//mesop/components/checkbox:py",
        "//mesop/components/text:py",
        "//mesop/colab",
        "//mesop/events",
        "//mesop/commands",
        "//mesop/features",
        "//mesop/server",
    ],
)

py_library(
    name = "version",
    srcs = ["version.py"],
    visibility = ["//build_defs:mesop_internal"],
)

py_library(
    name = "example_index",
    srcs = ["example_index.py"],
    visibility = ["//build_defs:mesop_internal"],
    deps = [
        "//mesop",
        # REF(//scripts/scaffold_component.py):insert_component_e2e_import
        "//mesop/components/slider/e2e",
        "//mesop/components/select/e2e",
        "//mesop/components/radio/e2e",
        "//mesop/components/slide_toggle/e2e",
        "//mesop/components/progress_spinner/e2e",
        "//mesop/components/progress_bar/e2e",
        "//mesop/components/icon/e2e",
        "//mesop/components/divider/e2e",
        "//mesop/components/badge/e2e",
        "//mesop/components/tooltip/e2e",
        "//mesop/components/input/e2e",
        "//mesop/components/markdown/e2e",
        "//mesop/components/box/e2e",
        "//mesop/components/checkbox/e2e",
        "//mesop/components/text/e2e",
        "//mesop/examples",
        "//mesop/examples/docs",
        "//mesop/examples/shared",
    ],
)
