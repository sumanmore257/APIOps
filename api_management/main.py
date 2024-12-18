import os
import argparse
from azure.identity import DefaultAzureCredential
from azure.mgmt.apimanagement import ApiManagementClient
from deployment.factory import BuilderFactory
from deployment.logger import get_logger
import sys

logger = get_logger()


def delete_resources(deleted_files, builder_factory):
    unique_resources = set()

    for line in deleted_files:
        path = line.strip().split("environments/")[1]
        parts = path.split("/")
        resource_type, resource_name = parts[2], parts[3]
        unique_resources.add((resource_type, resource_name))

    for resource_type, resource_name in unique_resources:
        try:
            builder = builder_factory.get_builder(resource_type)
            builder.delete(resource_name)
        except Exception as e:
            logger.error(
                f"Deletion failed in {resource_type} builder for {resource_name}: {e}"
            )
            sys.exit(1)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--deleted-files",
            help="Path to the file containing deleted files list",
            default="deleted_files.txt",
        )
        args = parser.parse_args()

        environment = os.getenv("ENVIRONMENT", "dev")
        apim_instance = os.getenv("APIM_INSTANCE", "apim-core-gateway")
        resource_group = os.getenv("RESOURCE_GROUP", "rg-apim-gateway")
        subscription_id = os.getenv(
            "SUBSCRIPTION_ID", "89dfb358-f764-4940-aa9f-68d7ab4b5f6e"
        )

        logger.info(
            f"Starting deployment for {environment} {apim_instance} {resource_group} {subscription_id}"
        )

        if not all([environment, apim_instance, resource_group, subscription_id]):
            raise ValueError("One or more required environment variables are missing")

        credential = DefaultAzureCredential()
        client = ApiManagementClient(credential, subscription_id)

        builder_factory = BuilderFactory(
            client, resource_group, apim_instance, subscription_id
        )

        # Handle deleted resources
        if args.deleted_files:
            logger.info("Deleted files list provided. Deleting resources.")
            if os.path.exists(args.deleted_files):
                logger.info(f"Reading deleted files from {args.deleted_files}")
                with open(args.deleted_files) as f:
                    deleted_files = f.readlines()
                logger.info(f"Deleting {len(deleted_files)} resources")
                delete_resources(
                    deleted_files,
                    builder_factory,
                )
            else:
                logger.error(f"The file {args.deleted_files} does not exist.")
                
        # Deploy resources
        builders = [
            "backends",
            "apis",
            "policy_fragments",
            "products",
            "operation_policy",
            "external_policy",
        ]
        for builder_type in builders:
            try:
                builder = builder_factory.get_builder(builder_type)
                builder.create(environment)
            except Exception as e:
                logger.error(f"Deployment failed in {builder_type} builder: {e}")
                sys.exit(1)

        logger.info(f"Deployment completed successfully for {apim_instance} on {resource_group} in {subscription_id}  🚀")
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)
