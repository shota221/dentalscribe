import json
from dataclasses import dataclass, asdict


@dataclass
class GetVoiceDownloadUrlResponse:
    upload_id: str
    presigned_url: str
    content_type: str
    size: int | None
    expires_in: int
    created_at: str | None

    def to_dict(self):
        return asdict(self)

    # Chalice互換
    def __iter__(self):  # type: ignore
        yield from self.to_dict().items()