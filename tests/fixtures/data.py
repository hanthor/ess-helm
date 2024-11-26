# Copyright 2024 New Vector Ltd
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial

import secrets
import string
from dataclasses import dataclass

import pytest
import signedjson.key
from lightkube.models.meta_v1 import ObjectMeta
from lightkube.resources.core_v1 import Secret

from ..artifacts import CertKey, generate_ca
from ..lib.utils import random_string


def generate_signing_key():
    signing_key = signedjson.key.generate_signing_key(0)
    value = f"{signing_key.alg} {signing_key.version} " f"{signedjson.key.encode_signing_key_base64(signing_key)}"
    return value


def unsafe_token(size):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(alphabet) for i in range(size))


@dataclass
class ESSData:
    synapse_postgres_password: str
    macaroon: str
    registration_shared_secret: str
    generic_shared_secret: str
    signing_key: str
    secrets_random: str
    ca: CertKey
    ca1: CertKey
    ca_second: CertKey
    another_ca: CertKey

    @property
    def release_name(self):
        return f"pytest-{self.secrets_random}"

    @property
    def ess_namespace(self):
        return f"ess-{self.secrets_random}"

    def ess_secret(self):
        return Secret(
            metadata=ObjectMeta(
                name="ess-secrets", namespace=self.ess_namespace, labels={"app.kubernetes.io/managed-by": "pytest"}
            ),
            stringData={
                "registrationSharedSecret": self.registration_shared_secret,
                "macaroon": self.macaroon,
                "signingKey": self.signing_key,
            },
        )


@pytest.fixture(scope="session")
async def generated_data(ca):
    return ESSData(
        synapse_postgres_password=unsafe_token(36),
        macaroon=secrets.token_urlsafe(36),
        registration_shared_secret=secrets.token_urlsafe(36),
        generic_shared_secret=secrets.token_urlsafe(36),
        signing_key=generate_signing_key(),
        secrets_random=random_string(string.ascii_lowercase + string.digits, 8),
        ca=ca,
        ca1=generate_ca("ca1"),
        ca_second=generate_ca("ca2"),
        another_ca=generate_ca("ca3"),
    )
