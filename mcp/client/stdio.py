class DummyStdioClient:
    async def __aenter__(self):
        return (None, None)
    async def __aexit__(self, exc_type, exc, tb):
        pass

def stdio_client(params):
    return DummyStdioClient()
