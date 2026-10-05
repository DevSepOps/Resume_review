# prod environment (stub)

Not provisioned yet (YAGNI). To create it:

```bash
cp -r ../dev ../prod          # or ../dev-azure for Azure
cd ../prod
# edit backend.tf (use a REMOTE backend with a different state key), set environment = "prod"
```

Use a separate state key/bucket path per environment and never share state between environments.
