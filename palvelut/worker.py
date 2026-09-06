from uvicorn_worker import UvicornWorker


class BoundedUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {
        **UvicornWorker.CONFIG_KWARGS,
        "limit_concurrency": 16,
    }
