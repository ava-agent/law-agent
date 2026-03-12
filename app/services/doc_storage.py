from io import BytesIO


class DocStorage:
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.bucket = "documents"

    def upload(self, file_id: str, content: bytes) -> str:
        path = f"{file_id}.docx"
        self.client.storage.from_(self.bucket).upload(
            path,
            content,
            {"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        )
        return self.get_public_url(file_id)

    def get_public_url(self, file_id: str) -> str:
        path = f"{file_id}.docx"
        res = self.client.storage.from_(self.bucket).get_public_url(path)
        return res
