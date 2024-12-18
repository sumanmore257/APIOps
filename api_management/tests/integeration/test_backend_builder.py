import pytest
import os

def test_create_backend(builder_factory, setup_and_teardown_backend):
    backend_builder = builder_factory.get_builder("backends") 
    environment = os.getenv("ENVIRONMENT", "integration_test")

    # Create backend
    result = backend_builder.create(environment)

    # Verify the backend was created
    if result and result.get("status") == "error":
        pytest.fail(f"Backend creation failed: {result['message']}")
    else:
        backend_name = "echo-backend-test-pool"
        response = backend_builder.client.backend.get(
            builder_factory.resource_group,
            builder_factory.apim_instance,
            backend_name
            )
        assert response.name == backend_name
        assert response is not None


    # Clean up (Delete the backend)
    delete_result = backend_builder.delete(backend_name)
    if delete_result and delete_result.get("status") == "error":
        pytest.fail(f"Backend deletion failed: {delete_result['message']}")
    else:
        with pytest.raises(Exception):
            backend_builder.client.backend.get(
                builder_factory.resource_group,
                builder_factory.apim_instance,
                backend_name
            )
