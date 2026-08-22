#!/usr/bin/env python3
"""
KubeOpt — Multi-Cloud Kubernetes Cost Optimizer
================================================
Production entry point.  Boots FastAPI via uvicorn.

Developer: Srinivas Kondepudi
Organization: Nivaya Technologies & kubeopt
"""

import os
import sys

# Fix OpenTelemetry StopIteration crash that prevents google.cloud.bigquery from importing.
# The Dockerfile strips .dist-info dirs for image size, which removes the entry_points metadata
# that opentelemetry uses to find its context implementation. Patching sys.modules before any
# google-cloud library is imported bypasses the broken module-level code entirely.
import types as _types
_fake_otel_ctx = _types.ModuleType('opentelemetry.context')
class _FakeRuntimeContext:
    def attach(self, token): return token
    def detach(self, token): pass
    def get_current(self): return {}
_fake_otel_ctx._RUNTIME_CONTEXT = _FakeRuntimeContext()
_fake_otel_ctx.attach = lambda t: t
_fake_otel_ctx.detach = lambda t: None
_fake_otel_ctx.get_current = lambda: {}
_fake_otel_ctx.create_key = lambda name: name
_fake_otel_ctx.get_value = lambda key, context=None: None
_fake_otel_ctx.set_value = lambda key, value, context=None: {}
sys.modules['opentelemetry.context'] = _fake_otel_ctx

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def load_env_files():
    """Load environment variables from persistent .env file."""
    settings_dir = os.getenv('SETTINGS_PATH', current_dir)
    main_env_file = os.path.join(settings_dir, '.env')

    if os.path.exists(main_env_file):
        print(f"Loading environment variables from {main_env_file}...")
        with open(main_env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    os.environ[key] = value
        print("Environment variables loaded")
    else:
        print(f"No .env file found at {main_env_file}")


# Load environment variables at import time
load_env_files()


def _install_access_log_redactor():
    """Redact ?token= values from uvicorn access log lines before they are written."""
    import logging
    import re

    _TOKEN_RE = re.compile(r'([\?&]token=)[^&\s"]+')

    class _TokenRedactor(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            if record.args:
                args = record.args
                if isinstance(args, (list, tuple)):
                    record.args = tuple(
                        _TOKEN_RE.sub(r'\1[REDACTED]', a) if isinstance(a, str) else a
                        for a in args
                    )
                elif isinstance(args, dict):
                    record.args = {
                        k: _TOKEN_RE.sub(r'\1[REDACTED]', v) if isinstance(v, str) else v
                        for k, v in args.items()
                    }
            if isinstance(record.msg, str):
                record.msg = _TOKEN_RE.sub(r'\1[REDACTED]', record.msg)
            return True

    redactor = _TokenRedactor()
    for name in ("uvicorn.access", "uvicorn"):
        logging.getLogger(name).addFilter(redactor)


def main():
    """Main application entry point — starts uvicorn."""
    import uvicorn

    _install_access_log_redactor()

    print("Starting KubeOpt (FastAPI)")
    print("=" * 60)

    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')

    print(f"Server: uvicorn on {host}:{port}")
    print(f"Docs:   http://localhost:{port}/docs")
    print("=" * 60)

    try:
        uvicorn.run(
            "fastapi_app:app",
            host=host,
            port=port,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Application error: {e}")
        return False

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
