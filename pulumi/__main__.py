import pulumi
import pulumi_gcp as gcp
import pulumi_docker as docker
import shutil


project = "rare-mender-353319"

############### QuestDB VM Instance
# Create a Google Cloud Network
firewall = gcp.compute.Firewall(
    "questdb-firewall",
    network="default",
    allows=[
        gcp.compute.FirewallAllowArgs(
            protocol="tcp",
            ports=["9000", "8812"],
        ),
    ],
    target_tags=["questdb"],
    source_ranges=["10.128.0.0/20"],
)

# Create a Compute Engine Instance
instance = gcp.compute.Instance(
    "questdb-instance",
    machine_type="e2-micro",
    zone="us-central1-a",
    boot_disk={
        "initialize_params": {
            "image": "ubuntu-os-cloud/ubuntu-2004-lts",
        },
    },
    network_interfaces=[
        gcp.compute.InstanceNetworkInterfaceArgs(
            network="default",
            access_configs=[{}],  # Ephemeral public IP
        )
    ],
    metadata_startup_script="""#!/bin/bash
        sudo apt-get update
        sudo apt-get install -y docker.io
        sudo docker run -d -p 9000:9000 -p 8812:8812 \
        --env QDB_HTTP_USER="admin" \
        --env QDB_HTTP_PASSWORD="quest" \
        questdb/questdb
        """,
    tags=["questdb"],
)

# Export the instance's name and public IP
pulumi.export("instanceName", instance.name)
pulumi.export("instance_ip", instance.network_interfaces[0].access_configs[0].nat_ip)



########### Twitch App ID and Secret
config = pulumi.Config()
appid = config.require_secret('appid')
appsecret = config.require_secret('appsecret')
# Create a Secret Manager Secret
secret = gcp.secretmanager.Secret(
    "twitch-app",
    secret_id='twitch-app-id-secret',
    replication={
            "auto": {},
        }
)
secret_secret = gcp.secretmanager.SecretVersion('twitch-app-secret', secret=secret.id, secret_data=appsecret)
secret_secret = gcp.secretmanager.SecretVersion('twitch-app-id', secret=secret.id, secret_data=appid)

pulumi.export("secret_name", secret.name)



########### Cloud Run functions
bucket = gcp.storage.Bucket("bucket",
    name=f"{project}-gcf-source",
    location="US",
    uniform_bucket_level_access=True)

all_users = gcp.organizations.get_iam_policy(bindings=[
    {
        "role": "roles/cloudfunctions.invoker",
        "members": ["allUsers"],
    },
])

#Twitch Auth Code
shutil.make_archive("../backend/twitch_auth_code", "zip", "../backend/twitch_auth_code")
twitch_auth_code = gcp.storage.BucketObject("start_eventsub_code",
    name="twitch_auth_code.zip",
    bucket=bucket.name,
    source=pulumi.FileAsset("../backend/twitch_auth_code.zip"))

twitch_auth_function = gcp.cloudfunctionsv2.Function("start_eventsub_function",
    name="start_eventsub",
    location="us-central1",
    description="a new function",
    build_config={
        "runtime": "python311",
        "entry_point": "start_eventsub",
        "source": {
            "storage_source": {
                "bucket": bucket.name,
                "object": twitch_auth_code.name,
            },
        },
    },
    service_config={
        "max_instance_count": 1,
        "available_memory": "256M",
        "timeout_seconds": 60,
    })
auth_policy = gcp.cloudfunctionsv2.FunctionIamMember("auth_policy",
    cloud_function=twitch_auth_function.name,
    location=twitch_auth_function.location,
    role="roles/cloudfunctions.invoker",
    member="allUsers"
)

pulumi.export("auth_function_name", twitch_auth_function.name)
pulumi.export("auth_function_url", twitch_auth_function.url)


#Twitch Webhook Code
shutil.make_archive("../backend/twitch_webhook_endpoint", "zip", "../backend/twitch_webhook_endpoint")
twitch_webhook_code = gcp.storage.BucketObject("twitch_webhook_endpoint",
    name="twitch_webhook_endpoint.zip",
    bucket=bucket.name,
    source=pulumi.FileAsset("../backend/twitch_webhook_endpoint.zip"))

twitch_webhook_function = gcp.cloudfunctionsv2.Function("twitch_webhook",
    name="twitch_webhook",
    location="us-central1",
    description="a new function",
    build_config={
        "runtime": "python311",
        "entry_point": "receive_webhook",
        "source": {
            "storage_source": {
                "bucket": bucket.name,
                "object": twitch_webhook_code.name,
            },
        },
    },
    service_config={
        "max_instance_count": 1,
        "available_memory": "256M",
        "timeout_seconds": 60,
    })

webhook_policy = gcp.cloudfunctionsv2.FunctionIamMember("webhook_policy",
    cloud_function=twitch_webhook_function.name,
    location=twitch_webhook_function.location,
    role="roles/cloudfunctions.invoker",
    member="allUsers"
)

pulumi.export("webhook_function_name", twitch_webhook_function.name)
pulumi.export("webhook_function_url", twitch_webhook_function.url)



########### Cloud Run Service
cloud_run_repo = gcp.artifactregistry.Repository("cloud-run-services",
    location="us-central1",
    repository_id="cloud-run-services",
    description="Cloud Run Services",
    format="DOCKER",
    cleanup_policies=[{
        'id': 'delete-old-images',
        'action':'KEEP',
        'most_recent_versions': {
            'keep_count':1
        }
    }]
)

marimo_image = docker.Image("marimo-image",
    build={
        "context": "../marimo",
        "dockerfile": "../marimo/Dockerfile",
        'platform': 'linux/amd64'
    },
    image_name=pulumi.Output.concat('us-central1-docker.pkg.dev/',project,'/',cloud_run_repo.repository_id,'/marimo:latest'),
    registry={
        'server': 'us-central1-docker.pkg.dev',
        "username": "oauth2accesstoken",
        "password": ''
    }
)
sha = marimo_image.repo_digest[-10:]
revision = pulumi.Output.concat('twitch-chat-analytics-',sha)

marimo_service = gcp.cloudrunv2.Service("marimo-service",
    name="twitch-chat-analytics",
    location="us-central1",
    deletion_protection=False,
    template={
            "containers": [
                {
                    "image": marimo_image.image_name
                }],
            'vpc_access': {
                'network_interfaces':[{
                    'network': 'default',
                    'subnetwork': 'default',
                }]
            },
            'revision': revision
        }
    )

marimo_policy = gcp.cloudrunv2.ServiceIamMember("marimo-policy",
    name=marimo_service.name,
    location=marimo_service.location,
    role="roles/run.invoker",
    member="allUsers"
)

pulumi.export("marimo_service_name", marimo_service.name)
pulumi.export("marimo_service_revision", revision)
pulumi.export("marimo_service_uri", marimo_service.uri)
