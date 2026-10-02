"""Wrapper for commonly used Bazel rules.
"""

load("@aspect_rules_py//py:defs.bzl", _py_binary = "py_binary", _py_library = "py_library", _py_test = "py_test")
load("@build_bazel_rules_nodejs//:index.bzl", _nodejs_binary = "nodejs_binary", _pkg_web = "pkg_web")
load("@my_deps//:requirements.bzl", "requirement")
load("@rules_proto//proto:defs.bzl", _proto_library = "proto_library")
load("//build_defs:jspb_proto_library.bzl", _jspb_proto_library = "jspb_proto_library")
load("//build_defs:ng_js_binary.bzl", _ng_js_binary = "ng_js_binary", _ng_js_binary_prod = "ng_js_binary_prod")
load("//build_defs:py_proto_library.bzl", _py_proto_library = "py_proto_library")
load("//build_defs:sass_external_binary.bzl", _sass_external_binary = "sass_external_binary")
load("//tools:defaults.bzl", _esbuild = "esbuild", _esbuild_config = "esbuild_config", _http_server = "http_server", _karma_web_test_suite = "karma_web_test_suite", _ng_module = "ng_module", _ng_test_library = "ng_test_library", _ng_web_test_suite = "ng_web_test_suite", _sass_binary = "sass_binary", _sass_library = "sass_library", _ts_library = "ts_library")
load("//tools/angular:index.bzl", _LINKER_PROCESSED_FW_PACKAGES = "LINKER_PROCESSED_FW_PACKAGES")

# Re-export symbols
esbuild = _esbuild
esbuild_config = _esbuild_config
karma_web_test_suite = _karma_web_test_suite
http_server = _http_server
jspb_proto_library = _jspb_proto_library
ng_js_binary = _ng_js_binary
ng_js_binary_prod = _ng_js_binary_prod
ng_module = _ng_module
ng_test_library = _ng_test_library
ng_web_test_suite = _ng_web_test_suite
nodejs_binary = _nodejs_binary
pkg_web = _pkg_web
proto_library = _proto_library
py_binary = _py_binary
py_library = _py_library
py_proto_library = _py_proto_library
py_test = _py_test
sass_binary = _sass_binary
sass_external_binary = _sass_external_binary
sass_library = _sass_library
ts_library = _ts_library

# Constants for deps
ANGULAR_CORE_DEPS = [
    "@npm//@angular/compiler",
    "@npm//@angular/router",
    "@npm//@angular/elements",
]

ANGULAR_MATERIAL_TS_DEPS = [
    "@npm//@angular/material",
]

ANGULAR_CDK_TS_DEPS = [
    "@npm//@angular/cdk",
]

JS_STATIC_FILES = [
    "@npm//:node_modules/moment/min/moment-with-locales.min.js",
    "@npm//:node_modules/rxjs/bundles/rxjs.umd.min.js",
    "@npm//:node_modules/zone.js/bundles/zone.umd.js",
]

LINKER_PROCESSED_FW_PACKAGES = _LINKER_PROCESSED_FW_PACKAGES

PYTHON_RUNFILES_DEP = [
    "@rules_python//python/runfiles",
]

THIRD_PARTY_JS_RXJS = [
    "@npm//rxjs",
]

THIRD_PARTY_JS_CODEMIRROR = [
    "@npm//codemirror",
    "@npm//@codemirror/lang-python",
    "@npm//@codemirror/merge",
    "@npm//@codemirror/theme-one-dark",
]

THIRD_PARTY_JS_HIGHLIGHTJS = [
    "@npm//highlight.js",
]

THIRD_PARTY_PY_ABSL_PY = [
    requirement("absl-py"),
]

THIRD_PARTY_PY_FIREBASE_ADMIN = [
    requirement("firebase-admin"),
]

THIRD_PARTY_PY_FLASK = [
    requirement("flask"),
]

THIRD_PARTY_PY_FLASK_SOCK = [
    requirement("flask-sock"),
]

THIRD_PARTY_PY_MATPLOTLIB = [
    requirement("matplotlib"),
]

THIRD_PARTY_PY_PYDANTIC = [
    requirement("pydantic"),
]

THIRD_PARTY_PY_PYTEST = [
    requirement("pytest"),
]

THIRD_PARTY_PY_MYPY_PROTOBUF = [
    requirement("mypy-protobuf"),
]

THIRD_PARTY_PY_PANDAS = [
    requirement("pandas"),
]

THIRD_PARTY_PY_DEEPDIFF = [
    requirement("deepdiff"),
]

THIRD_PARTY_PY_DOTENV = [
    requirement("python-dotenv"),
]

THIRD_PARTY_PY_MSGPACK = [
    requirement("msgpack"),
]

THIRD_PARTY_PY_SQLALCHEMY = [
    requirement("sqlalchemy"),
]

THIRD_PARTY_PY_GREENLET = [
    requirement("greenlet"),
]

THIRD_PARTY_PY_GOOGLE_GENAI = [
    requirement("google-genai"),
]

THIRD_PARTY_PY_WATCHDOG = [
    requirement("watchdog"),
]
