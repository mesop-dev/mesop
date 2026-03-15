import importlib
from unittest.mock import patch

import mesop.server.server_utils as su
from mesop.env import env


def reload_utils():
  importlib.reload(su)


def test_remove_base_url_path_no_base():
  with patch.object(env, "MESOP_BASE_URL_PATH", ""):
    reload_utils()
    assert su.remove_base_url_path("/foo") == "/foo"


def test_remove_base_url_path_with_base():
  with patch.object(env, "MESOP_BASE_URL_PATH", "/base"):
    reload_utils()
    assert su.remove_base_url_path("/base/foo") == "/foo"
    assert su.remove_base_url_path("/base") == "/"
    assert su.remove_base_url_path("/base/") == "/"


def test_prefix_base_url_with_base():
  with patch.object(env, "MESOP_BASE_URL_PATH", "/base"):
    reload_utils()
    assert su.prefix_base_url("/foo") == "/base/foo"
    assert su.prefix_base_url("foo") == "/base/foo"


def test_prefix_base_url_no_base():
  with patch.object(env, "MESOP_BASE_URL_PATH", ""):
    reload_utils()
    assert su.prefix_base_url("/foo") == "/foo"


def test_is_same_site_identical():
  assert (
    su.is_same_site("http://localhost:32123", "http://localhost:32123/") is True
  )


def test_is_same_site_different_ports():
  assert (
    su.is_same_site("http://localhost:32123", "http://localhost:8080") is False
  )


def test_is_same_site_different_schemes():
  assert su.is_same_site("http://example.com", "https://example.com") is False


def test_is_same_site_different_hosts():
  assert su.is_same_site("http://evil.com", "http://localhost:32123") is False


def test_is_same_site_none():
  assert su.is_same_site(None, "http://localhost:32123") is False
  assert su.is_same_site("http://localhost:32123", None) is False
