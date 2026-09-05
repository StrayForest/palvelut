import re

from django.template.loader import render_to_string
from django.test import Client, RequestFactory, SimpleTestCase


class P4SecurityHeadersTests(SimpleTestCase):
    def test_public_response_has_restrictive_security_headers(self):
        response = Client().get("/palvelut/en/legal/privacy/", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        csp = response.headers["Content-Security-Policy"]
        directives = {directive.split()[0]: directive for directive in csp.split("; ")}
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("base-uri 'self'", csp)
        self.assertNotIn("'unsafe-inline'", directives["script-src"])
        self.assertNotIn("'unsafe-eval'", directives["script-src"])
        self.assertEqual(directives["style-src"], "style-src 'self'")
        self.assertEqual(directives["style-src-elem"], "style-src-elem 'self'")
        self.assertEqual(directives["style-src-attr"], "style-src-attr 'unsafe-inline'")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["Referrer-Policy"], "same-origin")
        self.assertEqual(
            response.headers["Permissions-Policy"],
            "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
        )

    def test_structured_data_nonce_matches_csp_nonce(self):
        response = Client().get("/palvelut/en/legal/privacy/", HTTP_HOST="localhost")
        csp = response.headers["Content-Security-Policy"]
        match = re.search(r"'nonce-([^']+)'", csp)
        self.assertIsNotNone(match)
        nonce = match.group(1)

        request = RequestFactory().get("/palvelut/en/")
        request.csp_nonce = nonce
        html = render_to_string(
            "base.html",
            {"structured_data_json": '{"@context":"https://schema.org"}'},
            request=request,
        )
        self.assertIn(f'nonce="{nonce}"', html)
