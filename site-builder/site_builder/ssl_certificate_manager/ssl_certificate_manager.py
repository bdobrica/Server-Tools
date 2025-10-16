"""SSL certificate manager using Python cryptography library."""

import logging
from datetime import datetime, timedelta, timezone
from functools import cached_property
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.x509 import oid
from cryptography.x509.oid import NameOID


class SSLCertificateManager:
    """Manages SSL certificate generation and renewal using Python cryptography library."""

    def __init__(
        self,
        proxy_ssl_path: Path,
        root_ca_crt: Path,
        root_ca_key: Path,
        root_ca_password: str,
        country: str = "RO",
        state: str = "Bucharest",
        organisation: str = "Perseus Reverse Proxy",
    ):
        self.proxy_ssl_path = proxy_ssl_path
        self.root_ca_crt = root_ca_crt
        self.root_ca_key = root_ca_key
        self.root_ca_password = root_ca_password
        self.country = country
        self.state = state
        self.organisation = organisation
        self._ca_key = None
        self._ca_cert = None

    @cached_property
    def logger(self) -> logging.Logger:
        """Get a logger instance."""
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
        return logger

    def _generate_ca_key(self):
        """Generate a new Ed25519 CA private key."""
        ca_key = ed25519.Ed25519PrivateKey.generate()
        with self.root_ca_key.open("wb") as key_file:
            key_file.write(
                ca_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=(
                        serialization.BestAvailableEncryption(self.root_ca_password.encode())
                        if self.root_ca_password
                        else serialization.NoEncryption()
                    ),
                )
            )
        return ca_key

    def _generate_ca_cert(self, ca_key):
        """Generate a self-signed CA certificate."""
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, self.country),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.state),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.organisation),
                x509.NameAttribute(NameOID.COMMON_NAME, f"{self.organisation} Root CA"),
            ]
        )

        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=3650))  # 10 years validity
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .sign(ca_key, None)
        )

        with self.root_ca_crt.open("wb") as cert_file:
            cert_file.write(ca_cert.public_bytes(serialization.Encoding.PEM))

        return ca_cert

    def _load_ca_key(self) -> ed25519.Ed25519PrivateKey:
        """Load the CA private key."""
        if self._ca_key is None:
            try:
                with self.root_ca_key.open("rb") as key_file:
                    self._ca_key = serialization.load_pem_private_key(
                        key_file.read(), password=self.root_ca_password.encode() if self.root_ca_password else None
                    )
            except FileNotFoundError:
                self.logger.warning("CA private key not found, generating a new one.")
                self._ca_key = self._generate_ca_key()
            except ValueError as e:
                raise ValueError(f"Invalid CA private key or password: {e}")
        if not isinstance(self._ca_key, ed25519.Ed25519PrivateKey):
            raise TypeError("CA private key is not an Ed25519 key")
        return self._ca_key

    def _load_ca_cert(self):
        """Load the CA certificate."""
        if self._ca_cert is None:
            try:
                with self.root_ca_crt.open("rb") as cert_file:
                    self._ca_cert = x509.load_pem_x509_certificate(cert_file.read())
            except FileNotFoundError:
                self.logger.warning("CA certificate not found, generating a new one.")
                self._ca_cert = self._generate_ca_cert(self._load_ca_key())
            except ValueError as e:
                raise ValueError(f"Invalid CA certificate: {e}")
        return self._ca_cert

    def _generate_private_key(self) -> ed25519.Ed25519PrivateKey:
        """Generate a new Ed25519 private key."""
        return ed25519.Ed25519PrivateKey.generate()

    def _create_csr(self, private_key: ed25519.Ed25519PrivateKey, subdomain: str) -> x509.CertificateSigningRequest:
        """Create a certificate signing request."""
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, self.country),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.state),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.organisation),
                x509.NameAttribute(NameOID.COMMON_NAME, subdomain),
            ]
        )

        csr = x509.CertificateSigningRequestBuilder().subject_name(subject).sign(private_key, None)
        return csr

    def _sign_certificate(self, csr: x509.CertificateSigningRequest, subdomain: str) -> x509.Certificate:
        """Sign a certificate using the CA."""
        ca_key = self._load_ca_key()
        ca_cert = self._load_ca_cert()

        # Create the certificate
        certificate = (
            x509.CertificateBuilder()
            .subject_name(csr.subject)
            .issuer_name(ca_cert.subject)
            .public_key(csr.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName(
                    [
                        x509.DNSName(subdomain),
                        x509.DNSName(f"www.{subdomain}"),
                    ]
                ),
                critical=False,
            )
            .add_extension(
                x509.KeyUsage(
                    key_encipherment=True,
                    digital_signature=True,
                    content_commitment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    data_encipherment=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage(
                    [
                        oid.ExtendedKeyUsageOID.SERVER_AUTH,
                        oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                    ]
                ),
                critical=True,
            )
            .sign(ca_key, None)
        )

        return certificate

    def _certificate_needs_renewal(self, cert_path: Path, days_before_expiry: int = 30) -> bool:
        """Check if a certificate needs renewal based on expiration date."""
        if not cert_path.exists():
            return True

        try:
            with cert_path.open("rb") as cert_file:
                cert = x509.load_pem_x509_certificate(cert_file.read())
                expiry_date = cert.not_valid_after_utc
                renewal_threshold = datetime.now(timezone.utc) + timedelta(days=days_before_expiry)
                return expiry_date <= renewal_threshold
        except Exception:
            return True  # If we can't read the cert, assume it needs renewal

    def generate_certificates(
        self,
        domain: str,
        subdomain: str,
        renew_keys: bool = False,
        renew_csrs: bool = False,
        renew_crts: bool = False,
        auto_renew_days: int = 30,
    ) -> None:
        """Generate SSL certificates for a domain/subdomain pair."""
        proxy_ssl_folder = (self.proxy_ssl_path / domain) / subdomain
        if not proxy_ssl_folder.is_dir():
            proxy_ssl_folder.mkdir(parents=True, exist_ok=True)

        # File paths
        proxy_ssl_key = proxy_ssl_folder / "client.key"
        proxy_ssl_csr = proxy_ssl_folder / "client.csr"
        proxy_ssl_crt = proxy_ssl_folder / "client.crt"
        proxy_ssl_pem = proxy_ssl_folder / "client.pem"

        # Generate private key
        private_key = None
        if not proxy_ssl_key.is_file() or renew_keys:
            private_key = self._generate_private_key()

            # Write private key to file
            with proxy_ssl_key.open("wb") as key_file:
                key_file.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )
        else:
            # Load existing private key
            with proxy_ssl_key.open("rb") as key_file:
                private_key = serialization.load_pem_private_key(key_file.read(), password=None)
                if not isinstance(private_key, ed25519.Ed25519PrivateKey):
                    raise TypeError("Existing private key is not an Ed25519 key")

        # Generate certificate signing request
        csr = None
        if not proxy_ssl_csr.is_file() or renew_keys or renew_csrs:
            csr = self._create_csr(private_key, subdomain)

            # Write CSR to file
            with proxy_ssl_csr.open("wb") as csr_file:
                csr_file.write(csr.public_bytes(serialization.Encoding.PEM))
        else:
            # Load existing CSR
            with proxy_ssl_csr.open("rb") as csr_file:
                csr = x509.load_pem_x509_csr(csr_file.read())

        # Generate certificate
        needs_cert_renewal = (
            not proxy_ssl_crt.is_file()
            or renew_keys
            or renew_csrs
            or renew_crts
            or self._certificate_needs_renewal(proxy_ssl_crt, auto_renew_days)
        )

        if needs_cert_renewal:
            certificate = self._sign_certificate(csr, subdomain)

            # Write certificate to file
            with proxy_ssl_crt.open("wb") as cert_file:
                cert_file.write(certificate.public_bytes(serialization.Encoding.PEM))

        # Generate PEM file (combined key + certificate)
        if not proxy_ssl_pem.is_file() or renew_keys or renew_csrs or renew_crts or needs_cert_renewal:
            with proxy_ssl_pem.open("wb") as pem_file:
                # Write private key
                pem_file.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )

                # Write certificate
                with proxy_ssl_crt.open("rb") as cert_file:
                    pem_file.write(cert_file.read())
