import os
from deployment.utils import load_text_file, handle_builder_exceptions
from deployment.logger import get_logger
from deployment.builders.builder_base import BuilderBase

logger = get_logger()

class ExternalPolicyBuilder(BuilderBase):

    @handle_builder_exceptions
    def create(self, environment):
        api_folder_base = os.path.join(
            "environments", environment, self.apim_instance, "apis"
        )
        for api_name in os.listdir(api_folder_base):
            api_path = os.path.join(api_folder_base, api_name)
            policy_path = os.path.join(api_path, "policy.xml")
            if os.path.exists(policy_path):
                policy = load_text_file(policy_path)
                self.update_api_policy(api_name, policy)
        logger.info(f"Successfully deployed external policies for {api_name} on {environment} environment")

    @handle_builder_exceptions
    def delete(self, resource_name: str):
        self.client.api_policy.delete(
            resource_group_name=self.resource_group,
            service_name=self.apim_instance,
            api_id=resource_name,
            policy_id="policy",
            if_match="*",
        )
        logger.info(f"Deleted external policy for {resource_name} on {self.apim_instance}")

    def update_api_policy(self, api_id, policy):
        logger.info(f"Updating policy for API {api_id}")
        self.client.api_policy.create_or_update(
            resource_group_name=self.resource_group,
            service_name=self.apim_instance,
            api_id=api_id,
            policy_id="policy",
            parameters={
                "properties": {
                    "format": "rawxml",
                    "value": policy,
                }
            },
        )
