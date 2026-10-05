# stage environment (stub)

Not provisioned yet (YAGNI). To create it:

```bash
cp -r ../dev ../stage          # or ../dev-azure for Azure
cd ../stage
# edit backend.tf (use a REMOTE backend with a different state key), set environment = "stage"
```

Use a separate state key/bucket path per environment and never share state between environments.
