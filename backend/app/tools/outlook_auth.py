from app.config import get_settings
from app.tools.outlook_email import MsalCachedTokenProvider


def main() -> None:
    settings = get_settings()
    provider = MsalCachedTokenProvider(
        settings.microsoft_client_id, settings.microsoft_tenant_id, settings.microsoft_token_cache_path
    )
    result = provider.authenticate_interactively()
    print(f"Microsoft sign-in cached for {result.get('account') or 'authorized account'}; scopes: Mail.Send")


if __name__ == "__main__":
    main()
