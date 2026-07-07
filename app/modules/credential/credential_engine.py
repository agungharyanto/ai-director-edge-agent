from app.repositories.credential_repository import CredentialRepository


class CredentialEngine:

    def credentials_for_vendor(self, vendor):
        return CredentialRepository().active_by_vendor(vendor)

    def success(self, credential_id):
        CredentialRepository().mark_success(credential_id)

    def failed(self, credential_id):
        CredentialRepository().mark_failed(credential_id)
