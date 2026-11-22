#!/usr/bin/env bash
# One-time Azure setup for Gym Log (Assignment 2). Safe to run again: every step
# skips or updates what already exists. The CD pipeline only swaps images
# afterwards; it never creates resources.
#
# Needs: az (logged in, Azure for Students selected), gh (logged in), docker.
# Passwords are generated here and kept in $SECRETS_DIR on this laptop and in
# Container App secrets on Azure. They never go into git or GitHub.
set -euo pipefail

PREFIX=hrahal-ieu2024
RG=rg-sdd-3a
LOCATION=${LOCATION:-germanywestcentral}
SWA_LOCATION=${SWA_LOCATION:-westeurope}   # Static Web Apps only run in a few regions
REPO=habo212/Ass1_devops
SECRETS_DIR=${SECRETS_DIR:-$HOME/.config/gymlog-azure}

SQL_SERVER=$PREFIX-sql
ENV_NAME=$PREFIX-env
UI_NAME=$PREFIX-ui
IDENTITY=$PREFIX-github

say() { printf '\n== %s\n' "$*"; }

# Read a password from $SECRETS_DIR, creating it on first run.
# "Gl" + 32 hex chars: upper, lower and digits (Azure's complexity rule), URL-safe.
password() {
  local file=$SECRETS_DIR/$1
  if [ ! -f "$file" ]; then
    mkdir -p "$SECRETS_DIR" && chmod 700 "$SECRETS_DIR"
    (umask 077; echo "Gl$(openssl rand -hex 16)" > "$file")
  fi
  cat "$file"
}

say "Subscription: $(az account show --query name -o tsv)"
az extension add --name containerapp --upgrade --only-show-errors -y

say "Resource providers"
for ns in Microsoft.App Microsoft.OperationalInsights Microsoft.Sql Microsoft.Web Microsoft.ManagedIdentity; do
  az provider register --namespace "$ns" --wait
done

say "Resource group $RG"
az group create -n "$RG" -l "$LOCATION" -o none

say "SQL server $SQL_SERVER"
ADMIN_PASSWORD=$(password sql-admin)
if ! az sql server show -g "$RG" -n "$SQL_SERVER" -o none 2>/dev/null; then
  az sql server create -g "$RG" -n "$SQL_SERVER" -l "$LOCATION" \
    --admin-user gymlogadmin --admin-password "$ADMIN_PASSWORD" -o none
fi
# 0.0.0.0 = "allow Azure services" (the Container Apps); plus this laptop, to create the users below.
az sql server firewall-rule create -g "$RG" -s "$SQL_SERVER" -n allow-azure \
  --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 -o none
MY_IP=$(curl -fsS https://api.ipify.org)
az sql server firewall-rule create -g "$RG" -s "$SQL_SERVER" -n setup-laptop \
  --start-ip-address "$MY_IP" --end-ip-address "$MY_IP" -o none

for svc in workouts records; do
  db=$PREFIX-$svc-db
  say "Database $db (free serverless offer, pauses when idle)"
  if ! az sql db show -g "$RG" -s "$SQL_SERVER" -n "$db" -o none 2>/dev/null; then
    az sql db create -g "$RG" -s "$SQL_SERVER" -n "$db" \
      --edition GeneralPurpose --compute-model Serverless --family Gen5 --capacity 1 --min-capacity 0.5 \
      --backup-storage-redundancy Local \
      --use-free-limit --free-limit-exhaustion-behavior AutoPause -o none
  fi
  # The free offer fixes auto-pause at 60 min and max size at 32 GB (the shortest/only values it allows).

  say "Login ${svc}_user: db_owner of $db only"
  docker run --rm --platform linux/amd64 --entrypoint /opt/mssql-tools18/bin/sqlcmd \
    -e APP_USER="${svc}_user" -e APP_PASSWORD="$(password "$svc-db")" \
    -v "$(pwd)/db:/db:ro" mcr.microsoft.com/mssql/server:2022-latest \
    -S "$SQL_SERVER.database.windows.net" -d "$db" -U gymlogadmin -P "$ADMIN_PASSWORD" \
    -l 90 -b -i /db/azure-user.sql   # 90 s login timeout: a paused database takes ~1 min to resume
done

say "Static Web App $UI_NAME"
if ! az staticwebapp show -g "$RG" -n "$UI_NAME" -o none 2>/dev/null; then
  # Azure for Students only allows 5 regions and Static Web Apps run in none of them,
  # so this can be refused by policy; the rest of the system still gets set up.
  az staticwebapp create -g "$RG" -n "$UI_NAME" -l "$SWA_LOCATION" --sku Free -o none \
    || echo "WARNING: Static Web App not created (region policy?), so the UI is not deployed yet"
fi
UI_HOST=$(az staticwebapp show -g "$RG" -n "$UI_NAME" --query defaultHostname -o tsv 2>/dev/null || true)
UI_ORIGIN=${UI_HOST:+https://$UI_HOST}   # empty = CORS lets no browser origin in

say "Container Apps environment $ENV_NAME"
if ! az containerapp env show -g "$RG" -n "$ENV_NAME" -o none 2>/dev/null; then
  az containerapp env create -g "$RG" -n "$ENV_NAME" -l "$LOCATION" -o none
fi

# Placeholder image until the first CD run pushes ours; CD then only changes the image.
PLACEHOLDER=mcr.microsoft.com/k8se/quickstart:latest
create_app() {
  local name=$1; shift
  if ! az containerapp show -g "$RG" -n "$name" -o none 2>/dev/null; then
    az containerapp create -g "$RG" -n "$name" --environment "$ENV_NAME" --image "$PLACEHOLDER" \
      --ingress external --target-port 8000 --min-replicas 0 --max-replicas 1 \
      --cpu 0.25 --memory 0.5Gi "$@" -o none
  fi
}
db_url() { echo "mssql://$1_user:$(password "$1-db")@$SQL_SERVER.database.windows.net:1433/$PREFIX-$1-db"; }

say "Container App $PREFIX-workouts"
create_app "$PREFIX-workouts" --secrets "db-url=$(db_url workouts)" \
  --env-vars DATABASE_URL=secretref:db-url UI_ORIGIN="$UI_ORIGIN"
WORKOUTS_URL=https://$(az containerapp show -g "$RG" -n "$PREFIX-workouts" --query properties.configuration.ingress.fqdn -o tsv)

say "Container App $PREFIX-records"
create_app "$PREFIX-records" --secrets "db-url=$(db_url records)" \
  --env-vars DATABASE_URL=secretref:db-url UI_ORIGIN="$UI_ORIGIN" WORKOUTS_URL="$WORKOUTS_URL" WORKOUTS_TIMEOUT_S=5

say "Pipeline identity $IDENTITY (GitHub OIDC, main branch only, no stored secret)"
if ! az identity show -g "$RG" -n "$IDENTITY" -o none 2>/dev/null; then
  az identity create -g "$RG" -n "$IDENTITY" -l "$LOCATION" -o none
fi
# GitHub's OIDC subject now carries the owner and repo IDs as well as their names
# (repo:owner@id/name@id:ref:...), so build it from the GitHub API instead of the name alone.
SUBJECT=$(gh api "repos/$REPO" --jq '"repo:\(.owner.login)@\(.owner.id)/\(.name)@\(.id):ref:refs/heads/main"')
verb=create
az identity federated-credential show -g "$RG" --identity-name "$IDENTITY" -n github-main -o none 2>/dev/null && verb=update
az identity federated-credential "$verb" -g "$RG" --identity-name "$IDENTITY" -n github-main \
  --issuer https://token.actions.githubusercontent.com \
  --subject "$SUBJECT" --audiences api://AzureADTokenExchange -o none
PRINCIPAL_ID=$(az identity show -g "$RG" -n "$IDENTITY" --query principalId -o tsv)
az role assignment create --assignee-object-id "$PRINCIPAL_ID" --assignee-principal-type ServicePrincipal \
  --role Contributor --scope "$(az group show -n "$RG" --query id -o tsv)" -o none

say "GitHub secrets for the CD job"
# The connection strings (with each service user's password) go straight from this laptop into
# GitHub secrets; the pipeline passes them to the Container Apps as secrets on every deploy.
gh secret set WORKOUTS_DATABASE_URL -R "$REPO" -b "$(db_url workouts)"
gh secret set RECORDS_DATABASE_URL -R "$REPO" -b "$(db_url records)"
# IDs only, nothing that signs in by itself: Azure trusts the OIDC token, not these values.
gh secret set AZURE_CLIENT_ID -R "$REPO" -b "$(az identity show -g "$RG" -n "$IDENTITY" --query clientId -o tsv)"
gh secret set AZURE_TENANT_ID -R "$REPO" -b "$(az account show --query tenantId -o tsv)"
gh secret set AZURE_SUBSCRIPTION_ID -R "$REPO" -b "$(az account show --query id -o tsv)"

say "Firewall: remove this laptop's IP now that setup is done"
az sql server firewall-rule delete -g "$RG" -s "$SQL_SERVER" -n setup-laptop -o none

say "Done"
echo "UI:       $UI_ORIGIN"
echo "workouts: $WORKOUTS_URL"
echo "records:  https://$(az containerapp show -g "$RG" -n "$PREFIX-records" --query properties.configuration.ingress.fqdn -o tsv)"
