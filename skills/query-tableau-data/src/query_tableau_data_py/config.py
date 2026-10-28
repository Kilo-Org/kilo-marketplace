"""Environment-first configuration for the query_tableau_data_py package."""

import logging
import os
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class SdkConfig(BaseSettings):
    """Environment-first configuration with optional explicit env-file loading.

    Invariants:
    - At least one valid credential triplet must be present (PAT, username/password, or JWT).
    - ``base_url`` always ends without a trailing slash.
    - If ``use_http=True``, a warning is logged on first access.
    """

    model_config = SettingsConfigDict(
        populate_by_name=True,
        extra="ignore",
        env_file_encoding="utf-8",
    )

    # Server & site
    tableau_server_url: str = Field(..., alias="TABLEAU_SERVER_URL")
    tableau_site_name: str = Field(default="", alias="TABLEAU_SITE_NAME")

    # Credentials — at least one triplet must be provided
    pat_name: str | None = Field(default=None, alias="PAT_NAME")
    pat_secret: str | None = Field(default=None, alias="PAT_VALUE")
    username: str | None = Field(default=None, alias="TABLEAU_USERNAME")
    password: str | None = Field(default=None, alias="TABLEAU_PASSWORD")
    jwt_client_id: str | None = Field(default=None, alias="TABLEAU_JWT_CLIENT_ID")
    jwt_secret: str | None = Field(default=None, alias="TABLEAU_JWT_SECRET")

    # API versions
    # api_version is a bootstrap default for the initial /serverinfo request.
    # Auto-negotiated from the server's response in Session.__enter__().
    api_version: str = Field(default="3.24")
    vds_version: str = Field(default="v1", alias="TABLEAU_VDS_VERSION")

    # Transport
    use_http: bool = Field(default=False, alias="TABLEAU_USE_HTTP")
    timeout: float = Field(default=30.0, alias="TABLEAU_TIMEOUT")
    ssl_verify: bool = Field(default=True)

    @property
    def base_url(self) -> str:
        """Normalized server URL without trailing slash."""
        url = self.tableau_server_url.rstrip("/")
        if self.use_http or url.startswith("http://"):
            logger.warning(
                "HTTP is being used instead of HTTPS. This is insecure.",
            )
        return url

    def __init__(self, **kwargs):
        if "_env_file" not in kwargs:
            env_file = os.environ.get("TABLEAU_ENV_FILE")
            if env_file:
                env_path = Path(env_file).expanduser().resolve()
                if not env_path.is_file():
                    raise ValueError(f"TABLEAU_ENV_FILE is not a file: {env_path}")
                kwargs["_env_file"] = str(env_path)
            else:
                kwargs["_env_file"] = None
        super().__init__(**kwargs)

    @model_validator(mode="after")
    def _check_credential_triplets(self) -> "SdkConfig":
        """Ensure at least one valid credential triplet is present."""
        has_pat = self.pat_name is not None and self.pat_secret is not None
        has_password = self.username is not None and self.password is not None
        has_jwt = self.jwt_client_id is not None and self.jwt_secret is not None

        if not any((has_pat, has_password, has_jwt)):
            raise ValueError(
                "At least one valid credential triplet must be provided: "
                "(pat_name + pat_secret), (username + password), or "
                "(jwt_client_id + jwt_secret)."
            )
        return self
