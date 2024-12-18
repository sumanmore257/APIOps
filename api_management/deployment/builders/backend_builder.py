import os
import requests
from deployment.utils import load_json_file
from azure.identity import DefaultAzureCredential
from deployment.logger import get_logger
from deployment.builders.builder_base import BuilderBase
from deployment.utils import handle_builder_exceptions

logger = get_logger()

class BackendBuilder(BuilderBase):

    def get_access_token(self):
        credential = DefaultAzureCredential()
        token = credential.get_token("https://management.azure.com/.default")
        return token.token

    @handle_builder_exceptions
    def create(self, environment: str):
        backend_folder_base = os.path.join(
            "environments", environment, self.apim_instance, "backends"
        )

        for backend_name in os.listdir(backend_folder_base):
            backend_path = os.path.join(backend_folder_base, backend_name)
            backend_info = load_json_file(
                os.path.join(backend_path, "backend_information.json")
            )

            url = f"https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.ApiManagement/service/{self.apim_instance}/backends/{backend_name}?api-version=2023-09-01-preview"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.get_access_token()}",
            }
            
            response = requests.put(url, json=backend_info, headers=headers)
            response.raise_for_status()

            if response.status_code == 201:
                logger.info(f"Successfully created backend {backend_name} in {self.apim_instance} on {environment}")
            else:
                logger.info(f"Successfully updated backend {backend_name} in {self.apim_instance} on {environment}")

    @handle_builder_exceptions
    def delete(self, resource_name: str):
        url = f"https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.ApiManagement/service/{self.apim_instance}/backends/{resource_name}?api-version=2023-09-01-preview"

        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
        }

        response = requests.delete(url, headers=headers)
        response.raise_for_status()

        logger.info(f"Deleted backend {resource_name} from {self.apim_instance}")
