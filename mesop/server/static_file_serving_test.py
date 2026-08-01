import gzip
import tempfile
from io import BytesIO

from flask import Flask

from mesop.server.static_file_serving import (
  _sanitize_terminal,
  configure_static_file_serving,
  gzip_cache,
  send_file_compressed,
)


# Putting this test first because it's making sure the cache is empty.
# Note: the cache is a static variable.
def test_send_file_compressed_do_not_cache():
  app = Flask(__name__)
  with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
    file_content = b"abc"
    tmp_file.write(file_content)
    tmp_file_path = tmp_file.name

  with app.test_request_context():
    send_file_compressed(tmp_file_path, disable_gzip_cache=True)
    # Check that cache is still empty
    assert len(gzip_cache) == 0


def test_send_file_compressed_uncached_request():
  app = Flask(__name__)
  with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
    file_content = b"abc"
    tmp_file.write(file_content)
    tmp_file_path = tmp_file.name

  with app.test_request_context():
    response = send_file_compressed(tmp_file_path, disable_gzip_cache=False)

    assert response.headers["Content-Encoding"] == "gzip"
    assert response.direct_passthrough is False
    assert int(response.headers["Content-Length"]) == len(response.get_data())

    # Check if the ungzipped data is correct
    with gzip.GzipFile(fileobj=BytesIO(response.get_data()), mode="rb") as f:
      ungzipped_data = f.read()
      assert ungzipped_data == file_content

    # Check that cache is properly stored
    assert len(gzip_cache) == 1
    assert gzip_cache[tmp_file_path] == response.get_data()


def test_send_file_compressed_cached_request():
  app = Flask(__name__)
  with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
    tmp_file.write(b"")
    tmp_file_path = tmp_file.name

  cached_bytes = b"test_data"
  gzip_buffer = BytesIO()
  with gzip.GzipFile(
    mode="wb", fileobj=gzip_buffer, compresslevel=6
  ) as gzip_file:
    gzip_file.write(cached_bytes)
  gzip_buffer.seek(0)
  gzip_cache[tmp_file_path] = gzip_buffer.getvalue()
  with app.test_request_context():
    response = send_file_compressed(tmp_file_path, disable_gzip_cache=False)

    assert response.headers["Content-Encoding"] == "gzip"
    assert response.direct_passthrough is False
    assert int(response.headers["Content-Length"]) == len(response.get_data())

    # Check that the cached bytes is returned
    with gzip.GzipFile(fileobj=BytesIO(response.get_data()), mode="rb") as f:
      ungzipped_data = f.read()
      assert ungzipped_data == cached_bytes


def test_sanitize_terminal_removes_ansi_escape_sequences():
  payload = "\x1b[2J\x1b[H\x1b[32mPWNED\x1b[0m"

  assert _sanitize_terminal(payload) == "PWNED"


def test_sanitize_terminal_removes_osc_sequences():
  # OSC 8 hyperlink escape sequence terminated with BEL.
  payload = "\x1b]8;;https://evil.example\x07click me\x1b]8;;\x07"

  assert _sanitize_terminal(payload) == "click me"


def test_sanitize_terminal_keeps_plain_text():
  payload = "Normal CSP report message"

  assert _sanitize_terminal(payload) == payload


def test_sanitize_terminal_coerces_non_str_input():
  assert _sanitize_terminal(123) == "123"


def test_csp_report_sanitizes_ansi_escapes_in_output(capsys):
  app = Flask(__name__)
  configure_static_file_serving(
    app,
    static_file_runfiles_base="unused",
    disable_gzip_cache=True,
  )
  client = app.test_client()

  response = client.post(
    "/__csp__",
    json={
      "csp-report": {
        # Attacker-controlled escape sequences distinct from the app's own
        # tc.* color codes, so this test can't pass by accident.
        "document-uri": "https://example.com/\x1b[2J\x1b[Hpwned/page",
        "blocked-uri": "https://evil.example\x1b]0;INJECTED-TITLE\x07",
        "violated-directive": "connect-src",
      }
    },
  )

  # A NameError or other exception in the handler would surface as a 500.
  assert response.status_code == 204
  output = capsys.readouterr().out
  assert "\x1b[2J" not in output
  assert "\x1b]0;INJECTED-TITLE" not in output
  assert "pwned/page" in output
  assert "evil.example" in output


if __name__ == "__main__":
  import pytest

  raise SystemExit(pytest.main([__file__]))
