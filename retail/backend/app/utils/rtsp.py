from urllib.parse import quote


def build_rtsp_url(
    ip_address: str | None,
    port: int = 554,
    username: str | None = None,
    password: str | None = None,
    stream_path: str | None = None,
    rtsp_url: str | None = None,
) -> str | None:
    if rtsp_url and rtsp_url.strip():
        return rtsp_url.strip()
    if not ip_address or not ip_address.strip():
        return None

    ip = ip_address.strip()
    path = (stream_path or "Streaming/Channels/101").strip().lstrip("/")
    port_val = port or 554

    if username:
        user = quote(username, safe="")
        pwd = quote(password or "", safe="")
        return f"rtsp://{user}:{pwd}@{ip}:{port_val}/{path}"

    return f"rtsp://{ip}:{port_val}/{path}"
