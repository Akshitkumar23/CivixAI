"""
Production SSRF Protection Engine (Milestones P & R)
Strict SSRF defense on official government source fetchers.
Blocks:
- Private RFC1918 IP addresses (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Loopback addresses (127.0.0.0/8, ::1, localhost)
- AWS/Cloud metadata endpoints (169.254.169.254, 169.254.0.0/16)
- Carrier-Grade NAT (100.64.0.0/10)
- Multicast, broadcast, reserved, and IPv6 private/unspecified addresses
- Non-HTTP protocols (file://, ftp://, gopher://, dict://, ldap://)
- Redirection to intranet/private IP addresses
"""
import ipaddress
import socket
from urllib.parse import urlparse, urljoin
from typing import Optional, List, Set, Tuple
import requests
from requests.adapters import HTTPAdapter


class SSRFSecurityViolation(ValueError):
    """Raised when a URL violates SSRF safety boundaries."""
    pass


ALLOWED_SCHEMES: Set[str] = {"http", "https"}
ALLOWED_PORTS: Set[int] = {80, 443, 8080, 8443}

OFFICIAL_GOV_DOMAINS: Tuple[str, ...] = (
    ".gov.in",
    ".nic.in",
    ".dbtbharat.gov.in",
    ".myscheme.gov.in",
    "myscheme.gov.in",
    "apisetu.gov.in",
    ".apisetu.gov.in",
    "jansamarth.in",
    ".jansamarth.in",
    "data.gov.in",
)


def is_ip_allowed(ip_str: str) -> bool:
    """
    Evaluates whether an IP address is a safe public routable IP.
    Rejects loopback, private RFC1918, link-local (cloud metadata), multicast,
    reserved, unspecified, and IPv4-mapped IPv6 internal addresses.
    """
    try:
        # Strip potential brackets from IPv6
        clean_ip = ip_str.strip("[]")
        ip = ipaddress.ip_address(clean_ip)

        # Standard checks for IPv4 and IPv6
        if (
            ip.is_loopback
            or ip.is_private
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False

        # Check Carrier Grade NAT (100.64.0.0/10) if not caught by is_private
        cgnat = ipaddress.ip_network("100.64.0.0/10")
        if isinstance(ip, ipaddress.IPv4Address) and ip in cgnat:
            return False

        # Check IPv4-mapped IPv6 (e.g. ::ffff:127.0.0.1)
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            mapped = ip.ipv4_mapped
            if (
                mapped.is_loopback
                or mapped.is_private
                or mapped.is_link_local
                or mapped.is_multicast
                or mapped.is_reserved
                or mapped.is_unspecified
                or mapped in cgnat
            ):
                return False

        return True
    except ValueError:
        return False


def resolve_domain_ips(hostname: str) -> List[str]:
    """
    Resolves a hostname via DNS to its IPv4/IPv6 addresses.
    Returns list of IP strings.
    """
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        ips = list({info[4][0] for info in addr_info})
        return ips
    except socket.gaierror as e:
        raise SSRFSecurityViolation(f"DNS resolution failed for hostname '{hostname}': {e}")
    except Exception as e:
        raise SSRFSecurityViolation(f"Unexpected DNS error for '{hostname}': {e}")


def validate_safe_url(url: str, allow_private_for_tests: bool = False) -> str:
    """
    Validates a URL against strict SSRF rules:
    1. Only http and https protocols allowed.
    2. Hostname must not be empty or localhost.
    3. Resolved IP addresses must be strictly public and routable.
    4. Prohibits intranet redirection targets and metadata IPs.
    """
    if not url or not isinstance(url, str):
        raise SSRFSecurityViolation("Target URL must be a non-empty string.")

    url_str = url.strip()
    parsed = urlparse(url_str)

    # 1. Protocol Scheme Verification
    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise SSRFSecurityViolation(
            f"Blocked protocol scheme '{scheme}'. Only HTTP and HTTPS are permitted."
        )

    # 2. Hostname & Port Verification
    hostname = parsed.hostname
    if not hostname:
        raise SSRFSecurityViolation("URL does not specify a valid hostname.")

    hostname_clean = hostname.strip().lower()

    # Block well-known localhost aliases
    if hostname_clean in ("localhost", "localhost.localdomain", "127.0.0.1", "::1", "0.0.0.0"):
        if not allow_private_for_tests:
            raise SSRFSecurityViolation(f"Access to localhost/loopback address '{hostname}' is blocked.")

    # Block AWS metadata explicit IP
    if hostname_clean == "169.254.169.254" or hostname_clean.startswith("169.254."):
        raise SSRFSecurityViolation(f"Access to cloud metadata service IP '{hostname}' is blocked.")

    if parsed.port and parsed.port not in ALLOWED_PORTS:
        raise SSRFSecurityViolation(f"Access to non-standard port '{parsed.port}' is blocked.")

    # 3. IP Resolution & RFC1918 / Metadata Check
    if not allow_private_for_tests:
        # If hostname is an explicit IP literal
        try:
            ip_obj = ipaddress.ip_address(hostname_clean.strip("[]"))
            if not is_ip_allowed(str(ip_obj)):
                raise SSRFSecurityViolation(
                    f"Target IP '{hostname}' belongs to a private, link-local, or reserved network range."
                )
        except ValueError:
            # Hostname is a domain name: perform DNS resolution pre-flight
            resolved_ips = resolve_domain_ips(hostname_clean)
            if not resolved_ips:
                raise SSRFSecurityViolation(f"Host '{hostname}' resolved to no IP addresses.")

            for ip in resolved_ips:
                if not is_ip_allowed(ip):
                    raise SSRFSecurityViolation(
                        f"Domain '{hostname}' resolved to prohibited IP '{ip}' (RFC1918/Localhost/Metadata)."
                    )

    return url_str


def validate_government_url(url: str, allow_private_for_tests: bool = False) -> str:
    """
    Validates a URL against strict SSRF rules AND strictly enforces that the
    target host belongs to official Indian government or designated statutory domains.
    """
    validated = validate_safe_url(url, allow_private_for_tests=allow_private_for_tests)
    parsed = urlparse(validated)
    host = (parsed.hostname or "").lower()
    
    is_official = any(host == d.lstrip(".") or host.endswith(d) for d in OFFICIAL_GOV_DOMAINS)
    if not is_official and not allow_private_for_tests:
        raise SSRFSecurityViolation(
            f"Domain '{host}' is not on the official government domain allowlist."
        )
    return validated


def is_safe_url(url: str, allow_private_for_tests: bool = False) -> bool:
    """Returns True if the URL passes all SSRF validation rules, False otherwise."""
    try:
        validate_safe_url(url, allow_private_for_tests=allow_private_for_tests)
        return True
    except SSRFSecurityViolation:
        return False


class SSRFSafeSession(requests.Session):
    """
    Hardened HTTP Session that validates both the initial request URL
    and ANY redirect targets against SSRF rules before making network calls.
    """

    def __init__(self, allow_private_for_tests: bool = False):
        super().__init__()
        self.allow_private_for_tests = allow_private_for_tests

    def send(self, request, **kwargs):
        # Validate request URL before dispatch
        validate_safe_url(request.url, allow_private_for_tests=self.allow_private_for_tests)
        return super().send(request, **kwargs)

    def resolve_redirects(self, resp, req, stream=False, timeout=None, verify=True, cert=None, proxies=None, yield_requests=False, **adapter_kwargs):
        """Validates each redirect URL against SSRF rules before yielding/following."""
        for redirect_req in super().resolve_redirects(resp, req, stream, timeout, verify, cert, proxies, yield_requests, **adapter_kwargs):
            target_url = redirect_req.url if hasattr(redirect_req, "url") else redirect_req
            if isinstance(target_url, str):
                validate_safe_url(target_url, allow_private_for_tests=self.allow_private_for_tests)
            yield redirect_req
