from source_capture.block_shell import CaptureBodyClass, classify_capture_body


def test_empty_body_is_empty():
    result = classify_capture_body(status=200, headers={}, body=b"")
    assert result.classification is CaptureBodyClass.EMPTY


def test_whitespace_only_body_is_empty():
    result = classify_capture_body(status=200, headers={}, body=b"   \n\t  ")
    assert result.classification is CaptureBodyClass.EMPTY


def test_cloudflare_interstitial_body_is_block_shell():
    body = (
        b"<html><head><title>Just a moment...</title></head>"
        b"<body>Checking your browser before accessing the site.</body></html>"
    )
    result = classify_capture_body(status=200, headers={"Server": "cloudflare"}, body=body)
    assert result.classification is CaptureBodyClass.BLOCK_SHELL
    assert result.signal is not None


def test_common_waf_body_markers_are_block_shell():
    examples = [
        (b"<html><title>Request blocked</title><body>AWS WAF</body></html>", "generic_request_blocked"),
        (b"<html><body>Access Denied. Reference #18.abc</body></html>", "generic_access_denied"),
        (b"<html><body>Sucuri Website Firewall - Access Denied</body></html>", "generic_access_denied"),
        (b"<html><body>Access to this page has been denied because we believe you are using automation.</body></html>", "perimeterx"),
    ]
    for body, signal in examples:
        result = classify_capture_body(status=200, headers={}, body=body)
        assert result.classification is CaptureBodyClass.BLOCK_SHELL
        assert result.signal == signal


def test_body_scan_extends_past_old_8192_byte_prefix():
    body = b"a" * 9000 + b"<html><body>The request is blocked.</body></html>"
    result = classify_capture_body(status=200, headers={}, body=body)
    assert result.classification is CaptureBodyClass.BLOCK_SHELL
    assert result.signal == "generic_request_blocked"


def test_cf_mitigated_header_is_block_shell():
    result = classify_capture_body(
        status=403, headers={"cf-mitigated": "challenge"}, body=b"<html>anything</html>"
    )
    assert result.classification is CaptureBodyClass.BLOCK_SHELL
    assert result.signal == "cloudflare_mitigated"


def test_datadome_header_is_block_shell_case_insensitive():
    result = classify_capture_body(
        status=403, headers={"X-DataDome": "protected"}, body=b"<html>x</html>"
    )
    assert result.classification is CaptureBodyClass.BLOCK_SHELL
    assert result.signal == "datadome_header"


def test_captcha_body_is_block_shell():
    body = b"<html><body>Please verify you are human by completing the hCaptcha challenge.</body></html>"
    result = classify_capture_body(status=200, headers={}, body=body)
    assert result.classification is CaptureBodyClass.BLOCK_SHELL


def test_embedded_recaptcha_login_widget_is_not_a_challenge_page_signal():
    body = b"""\
    <html><body>
      <article><h1>Visible source content</h1><p>The complete article is here.</p></article>
      <form action="/login">
        <div class="g-recaptcha" data-sitekey="public-widget-key"></div>
        <span class="error bad_captcha" style="display:none"></span>
      </form>
    </body></html>
    """
    result = classify_capture_body(status=200, headers={}, body=body)
    assert result.classification is CaptureBodyClass.CONTENT_UNVERIFIED
    assert result.signal is None


def test_dormant_hcaptcha_script_on_full_page_is_not_a_challenge_page_signal():
    body = b"""\
    <html><head><title>Company sustainability</title>
      <script src="https://js.hcaptcha.com/1/api.js" async defer></script>
    </head><body>
      <main><h1>Sustainability</h1><p>Our complete company statement is here.</p></main>
    </body></html>
    """
    result = classify_capture_body(status=200, headers={}, body=body)
    assert result.classification is CaptureBodyClass.CONTENT_UNVERIFIED
    assert result.signal is None


def test_encoded_body_is_content_unverified_with_limitation_signal():
    result = classify_capture_body(
        status=200,
        headers={"Content-Encoding": "gzip"},
        body=b"\x1f\x8b\x08\x00compressed bytes",
    )
    assert result.classification is CaptureBodyClass.CONTENT_UNVERIFIED
    assert result.signal == "encoded_body_uninspectable"
    assert "inspection is limited" in result.detail


def test_ordinary_html_is_content_unverified():
    body = (
        b"<html><head><title>Q3 Earnings</title></head>"
        b"<body><article>Revenue rose 4 percent year over year.</article></body></html>"
    )
    result = classify_capture_body(status=200, headers={"Content-Type": "text/html"}, body=body)
    assert result.classification is CaptureBodyClass.CONTENT_UNVERIFIED
    assert result.signal is None


def test_no_positive_content_class_exists():
    # Honesty invariant: the guard never asserts a body IS the real source.
    assert not hasattr(CaptureBodyClass, "CONTENT")
    assert set(CaptureBodyClass) == {
        CaptureBodyClass.BLOCK_SHELL,
        CaptureBodyClass.EMPTY,
        CaptureBodyClass.CONTENT_UNVERIFIED,
    }
