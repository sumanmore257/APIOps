import os
from deployment.utils import load_text_file, handle_builder_exceptions
from deployment.logger import get_logger
from deployment.builders.builder_base import BuilderBase

logger = get_logger()

class OperationPolicyBuilder(BuilderBase):

    @handle_builder_exceptions
    def create(self, environment):
        api_folder_base = os.path.join(
            "environments", environment, self.apim_instance, "apis"
        )
        for api_name in os.listdir(api_folder_base):
            api_path = os.path.join(api_folder_base, api_name)
            operations_folder = os.path.join(api_path, "operations")

            if os.path.exists(operations_folder):
                for operation in os.listdir(operations_folder):
                    operation_path = os.path.join(operations_folder, operation)
                    operation_policy_path = os.path.join(operation_path, "policy.xml")
                    if os.path.exists(operation_policy_path):
                        operation_policy = load_text_file(operation_policy_path)
                        self.update_operation_policy(
                            api_name, operation, operation_policy
                        )
        logger.info(f"Successfully deployed operation policies for {api_name} on {environment} environment")

    @handle_builder_exceptions
    def delete(self, resource_name: str):
        api_folder_base = os.path.join(
            "environments", resource_name, self.apim_instance, "apis"
        )
        for api_name in os.listdir(api_folder_base):
            api_path = os.path.join(api_folder_base, api_name)
            operations_folder = os.path.join(api_path, "operations")
            if os.path.exists(operations_folder):
                for operation in os.listdir(operations_folder):
                    self.client.api_operation_policy.delete(
                        resource_group_name=self.resource_group,
                        service_name=self.apim_instance,
                        api_id=api_name,
                        operation_id=operation,
                        policy_id="policy",
                        if_match="*",
                    )
        logger.info(f"Deleted operation policies for {resource_name} on {self.apim_instance} environment")

    def update_operation_policy(self, api_id, operation_id, policy):
        self.client.api_operation_policy.create_or_update(
            resource_group_name=self.resource_group,
            service_name=self.apim_instance,
            api_id=api_id,
            operation_id=operation_id,
            policy_id="policy",
            parameters={
                "properties": {
                    "format": "rawxml",
                    "value": policy,
                }
            },
        )
