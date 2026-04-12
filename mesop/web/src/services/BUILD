load("//build_defs:defaults.bzl", "ANGULAR_CORE_DEPS", "ANGULAR_MATERIAL_TS_DEPS", "ng_module", "ng_test_library", "ng_web_test_suite")

package(
    default_visibility = ["//build_defs:mesop_internal"],
)

ng_module(
    name = "services",
    srcs = glob(
        ["*.ts"],
        exclude = ["*_spec.ts"],
    ),
    deps = [
        "//mesop/protos:ui_jspb_proto",
        "//mesop/web/src/utils",
    ] + ANGULAR_CORE_DEPS + ANGULAR_MATERIAL_TS_DEPS,
)

ng_test_library(
    name = "services_test_lib",
    srcs = glob(["*_spec.ts"]),
    deps = [
        ":services",
    ] + ANGULAR_CORE_DEPS,
)

ng_web_test_suite(
    name = "unit_tests",
    deps = [
        ":services_test_lib",
    ],
)
