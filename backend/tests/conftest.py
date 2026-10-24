"""Shared pytest configuration.

Settings are instantiated during module import, so the complete suite must set
its test environment before individual test modules import application code.
"""

import os


os.environ.update(
    {
        "ENVIRONMENT": "test",
        "SECRET_KEY": "test-secret-key-that-is-long-enough-for-tests",
        "FIELD_ENCRYPTION_KEY": "test-encryption-key-that-is-long-enough",
        "DATABASE_URL": "sqlite:///./test_suite.db",
        "ADMIN_BOOTSTRAP_EMAIL": "owner@example.com",
        "ADMIN_BOOTSTRAP_PASSWORD": "OwnerStrong!2026",
        "DEFAULT_PUBLIC_ROLE": "Viewer",
        "LOAD_DEMO_DATA": "false",
        "AUTO_CREATE_TABLES": "true",
        "TEST_ADMIN_PASSWORD": "TestAdmin@2026!Secure",
        "TEST_SOC_PASSWORD": "TestSOC@2026!Secure",
        "TEST_MALWARE_PASSWORD": "TestMalware@2026!Secure",
        "TEST_VULN_PASSWORD": "TestVuln@2026!Secure",
        "TEST_VIEWER_PASSWORD": "TestViewer@2026!Secure",
    }
)
