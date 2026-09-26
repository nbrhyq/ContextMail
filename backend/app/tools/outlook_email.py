from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Protocol
from uuid import uuid4

import httpx

from app.config import Settings, get_settings
from app.models.domain import ApprovalStatus, EmailDraft
from app.tools.interfaces import EmailTool
from app.tools.mock_tools import MockEmailTool


class AccessTokenProvider(Protocol):
    async def get_access_token(self) -> str: ...


class MsalCachedTokenProvider:
    """Delegated OAuth token provider. Interactive login is an explicit CLI action."""

    SCOPES = ["Mail.Send"]

    def __init__(self, client_id: str, tenant_id: str, cache_path: str) -> None:
        if not client_id:
            raise ValueError("CONTEXTMAIL_MICROSOFT_CLIENT_ID is required for Outlook")
        self.client_id = client_id
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.cache_path = Path(cache_path)

    def _application(self):
        try:
            import msal
        except ImportError as exc:
            raise RuntimeError("Install ContextMail with the 'outlook' extra to use Microsoft Graph") from exc
        cache = msal.SerializableTokenCache()
        if self.cache_path.exists():
            cache.deserialize(self.cache_path.read_text(encoding="utf-8"))
        app = msal.PublicClientApplication(self.client_id, authority=self.authority, token_cache=cache)
        return app, cache

    def _persist(self, cache) -> None:
        if cache.has_state_changed:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(cache.serialize(), encoding="utf-8")
            self.cache_path.chmod(0o600)

    async def get_access_token(self) -> str:
        app, cache = self._application()
        accounts = app.get_accounts()
        result = app.acquire_token_silent(self.SCOPES, account=accounts[0] if accounts else None)
        self._persist(cache)
        if not result or "access_token" not in result:
            raise PermissionError("No cached Microsoft session. Run: python -m app.tools.outlook_auth")
        return result["access_token"]

    def authenticate_interactively(self) -> dict:
        app, cache = self._application()
        flow = app.initiate_device_flow(scopes=self.SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Could not start Microsoft device flow: {flow.get('error_description', 'unknown error')}")
        print(flow["message"])
        result = app.acquire_token_by_device_flow(flow)
        self._persist(cache)
        if "access_token" not in result:
            raise PermissionError(result.get("error_description", "Microsoft authentication failed"))
        return {"account": result.get("id_token_claims", {}).get("preferred_username"), "scopes": self.SCOPES}


class OutlookEmailTool:
    """Microsoft Graph /me/sendMail adapter guarded by explicit approval."""

    def __init__(self, token_provider: AccessTokenProvider, graph_base_url: str, timeout: float = 30, transport=None) -> None:
        self.token_provider = token_provider
        self.graph_base_url = graph_base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport

    @staticmethod
    def _attachments(paths: list[str]) -> list[dict]:
        attachments = []
        for raw_path in paths:
            path = Path(raw_path)
            if not path.is_file():
                raise FileNotFoundError(f"Attachment is not available: {path.name}")
            attachments.append({
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": path.name,
                "contentType": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                "contentBytes": base64.b64encode(path.read_bytes()).decode("ascii"),
            })
        return attachments

    async def send(self, draft: EmailDraft, approval: ApprovalStatus) -> str:
        if approval != ApprovalStatus.APPROVED:
            raise PermissionError("Explicit user approval is required before email action")
        if not draft.recipient:
            raise ValueError("An Outlook recipient is required")
        token = await self.token_provider.get_access_token()
        message = {
            "subject": draft.subject,
            "body": {"contentType": "Text", "content": draft.body},
            "toRecipients": [{"emailAddress": {"address": draft.recipient}}],
        }
        if draft.attachments:
            message["attachments"] = self._attachments(draft.attachments)
        async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
            response = await client.post(
                f"{self.graph_base_url}/me/sendMail",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                content=json.dumps({"message": message, "saveToSentItems": True}),
            )
            response.raise_for_status()
        return f"outlook_accepted_{uuid4().hex[:12]}"


def create_email_tool(settings: Settings | None = None) -> EmailTool:
    configured = settings or get_settings()
    if configured.email_provider.lower() == "outlook":
        tokens = MsalCachedTokenProvider(
            configured.microsoft_client_id,
            configured.microsoft_tenant_id,
            configured.microsoft_token_cache_path,
        )
        return OutlookEmailTool(tokens, configured.microsoft_graph_base_url)
    return MockEmailTool()
