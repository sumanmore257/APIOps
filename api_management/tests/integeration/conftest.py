import os
import pytest
from azure.identity import DefaultAzureCredential
from azure.mgmt.apimanagement import ApiManagementClient
from deployment.factory import BuilderFactory
from deployment.utils import load_json_file

@pytest.fixture(scope="session")
def environment_variables():
    return {
        "subscription_id": os.getenv("SUBSCRIPTION_ID", "89dfb358-f764-4940-aa9f-68d7ab4b5f6e"),
        "apim_instance": os.getenv("APIM_INSTANCE", "apim-core-gateway"),
        "resource_group": os.getenv("RESOURCE_GROUP", "rg-apim-gateway"),
        "environment": os.getenv("ENVIRONMENT", "integration_test"),
    }

@pytest.fixture(scope="session")
def api_management_client(environment_variables):
    credential = DefaultAzureCredential()
    client = ApiManagementClient(credential, environment_variables["subscription_id"])
    return client

@pytest.fixture(scope="session")
def builder_factory(api_management_client, environment_variables):
    factory = BuilderFactory(
        api_management_client,
        environment_variables["resource_group"],
        environment_variables["apim_instance"],
        environment_variables["subscription_id"]
    )
    return factory

@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_api(api_management_client, builder_factory, environment_variables):
    api_builder = builder_factory.get_builder("apis")

    # Create API
    result = api_builder.create(environment_variables["environment"])
    if result["status"] == "error":
        pytest.fail(f"API creation failed: {result['message']}")
    else:
        api_id = "echo-api"
        response = api_management_client.api.get(
            builder_factory.resource_group, builder_factory.apim_instance, api_id
        )
        assert response.name == api_id
        assert response.display_name == "Echo Test API"

    yield

    # Clean up (Delete the API)
    delete_result = api_builder.delete("echo-api")
    if delete_result["status"] == "error":
        pytest.fail(f"API deletion failed: {delete_result['message']}")
    else:
        with pytest.raises(Exception):
            api_management_client.api.get(
                builder_factory.resource_group, builder_factory.apim_instance, api_id
            )

@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_product(api_management_client, builder_factory, environment_variables):
    product_id = "basic-test"

    # Create Product
    try:
        response = api_management_client.product.create_or_update(
            resource_group_name=builder_factory.resource_group,
            service_name=builder_factory.apim_instance,
            product_id=product_id,
            parameters={
                "properties": {
                    "displayName": "Basic Test Product",
                    "description": "Product used for integration testing",
                    "subscriptionRequired": True,
                    "approvalRequired": False,
                    "subscriptionsLimit": 1,
                    "state": "published",
                }
            },
        )
        assert response.name == product_id
    except Exception as e:
        pytest.fail(f"Product creation failed: {str(e)}")

    yield

    # Clean up (Delete the Product and associated subscriptions)
    try:
        # List and delete all subscriptions associated with the product
        subscriptions = list(
            api_management_client.product_subscriptions.list(
                resource_group_name=builder_factory.resource_group,
                service_name=builder_factory.apim_instance,
                product_id=product_id,
            )
        )

        if subscriptions:
            for subscription in subscriptions:
                api_management_client.subscription.delete(
                    resource_group_name=builder_factory.resource_group,
                    service_name=builder_factory.apim_instance,
                    sid=subscription.name,
                    if_match="*"
                )

        # Delete the Product
        api_management_client.product.delete(
            resource_group_name=builder_factory.resource_group,
            service_name=builder_factory.apim_instance,
            product_id=product_id,
            if_match="*",
        )
    except Exception as e:
        if "ResourceNotFound" not in str(e):
            pytest.fail(f"Product deletion failed: {str(e)}")

@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_backend(api_management_client, builder_factory, environment_variables):
    backend_info_path = os.path.join("tests","data", "backend_information.json")

    try:
        backend_info = load_json_file(backend_info_path)
        for backend_name, backend_params in backend_info.items():
            response = api_management_client.backend.create_or_update(
                resource_group_name=builder_factory.resource_group,
                service_name=builder_factory.apim_instance,
                backend_id=backend_name,
                parameters=backend_params
            )
            assert response.name == backend_name
        
    except Exception as e:
        pytest.fail(f"Backend creation failed: {str(e)}")

    yield

    # Clean up (Delete the backends)
    for backend_name in backend_info.keys():
        try:
            api_management_client.backend.delete(
                resource_group_name=builder_factory.resource_group,
                service_name=builder_factory.apim_instance,
                backend_id=backend_name,
                if_match="*"
            )
        except Exception as e:
            if "ResourceNotFound" not in str(e):
                pytest.fail(f"Backend deletion failed: {str(e)}")