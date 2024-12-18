from deployment.builders.api_builder import ApiBuilder
from deployment.builders.product_builder import ProductBuilder
from deployment.builders.operation_policy_builder import OperationPolicyBuilder
from deployment.builders.external_policy_builder import ExternalPolicyBuilder
from deployment.builders.policy_fragment_builder import PolicyFragmentBuilder
from deployment.builders.backend_builder import BackendBuilder


class BuilderFactory:
    def __init__(self, client, resource_group, apim_instance, subscription_id):
        self.client = client
        self.resource_group = resource_group
        self.apim_instance = apim_instance
        self.subscription_id = subscription_id
        self.builders = {
            "apis": ApiBuilder,
            "products": ProductBuilder,
            "operation_policy": OperationPolicyBuilder,
            "external_policy": ExternalPolicyBuilder,
            "policy_fragments": PolicyFragmentBuilder,
            "backends": BackendBuilder
        }

    def get_builder(self, builder_type):
        builder_class = self.builders.get(builder_type)
        if not builder_class:
            raise ValueError(f"Builder type {builder_type} is not recognized")
        return builder_class(self.client, self.resource_group, self.apim_instance, self.subscription_id)
