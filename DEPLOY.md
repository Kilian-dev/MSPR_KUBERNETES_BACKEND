# Déploiement COFRAP — OpenFaaS sur Minikube

## ÉTAPE 1 — Démarrer Minikube

```powershell
minikube start --driver=docker --memory=4096 --cpus=4
minikube addons enable ingress
kubectl create namespace cofrap
kubectl create namespace openfaas
kubectl create namespace openfaas-fn
```

## ÉTAPE 2 — PostgreSQL

```powershell
kubectl apply -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.22/releases/cnpg-1.22.0.yaml
kubectl get pods -n cnpg-system -w
```
Ctrl+C quand Running, puis :
```powershell
kubectl apply -f k8s/postgres.yaml
kubectl get clusters -n cofrap -w
```
Ctrl+C quand healthy.

### Récupérer le mot de passe DB
```powershell
kubectl get secret cofrap-db-cofrap-user -n cofrap `
  -o jsonpath="{.data.password}" | `
  ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
```
Note ce mot de passe → DB_PASSWORD

### Créer la table
```powershell
kubectl port-forward svc/cofrap-db-rw 5432:5432 -n cofrap
```
Dans un autre terminal, connecte-toi avec DBeaver (localhost:5432, user: cofrap_user) et exécute k8s/init-db.sql

## ÉTAPE 3 — OpenFaaS

```powershell
helm repo add openfaas https://openfaas.github.io/faas-netes/
helm repo update
helm install openfaas openfaas/openfaas `
  --namespace openfaas `
  --set functionNamespace=openfaas-fn `
  --set generateBasicAuth=true `
  --set serviceType=NodePort
kubectl get pods -n openfaas -w
```
Ctrl+C quand tout est Running.

### Récupérer le mot de passe OpenFaaS
```powershell
kubectl get secret -n openfaas basic-auth `
  -o jsonpath="{.data.basic-auth-password}" | `
  ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
```
Note ce mot de passe → FAAS_PASSWORD

## ÉTAPE 4 — Installer faas-cli et se connecter

```powershell
winget install OpenFaaS.faas-cli
```
Ferme et réouvre PowerShell, puis dans un terminal avec port-forward gateway actif :
```powershell
kubectl port-forward svc/gateway -n openfaas 8080:8080
```
Dans un autre terminal :
```powershell
$env:OPENFAAS_URL = "http://localhost:8080"
faas-cli login --username admin --password FAAS_PASSWORD
```

## ÉTAPE 5 — Créer le Secret DB pour les fonctions

Remplace DB_PASSWORD par le mot de passe récupéré à l'étape 2 :
```powershell
kubectl create secret generic db-credentials `
  --from-literal=host=cofrap-db-rw.cofrap.svc.cluster.local `
  --from-literal=port=5432 `
  --from-literal=dbname=cofrap `
  --from-literal=user=cofrap_user `
  --from-literal=password=DB_PASSWORD `
  -n openfaas-fn
```

## ÉTAPE 6 — Build, Push et Deploy des fonctions

Remplace TONUSER par votre username Docker Hub dans stack.yaml, puis :
```powershell
faas-cli template store pull python3-http
faas-cli build -f stack.yaml
faas-cli push -f stack.yaml
faas-cli deploy -f stack.yaml
faas-cli list
```

## ÉTAPE 7 — Déployer le Frontend

```powershell
cd C:\chemin\vers\frontend
docker build -t TONUSER/cofrap-frontend:latest .
docker push TONUSER/cofrap-frontend:latest
cd C:\chemin\vers\cofrap
kubectl apply -f k8s/frontend.yaml
kubectl port-forward svc/cofrap-frontend 5000:80 -n cofrap
```
Ouvre http://localhost:5000

## ÉTAPE 8 — Vérification finale

```powershell
kubectl get all -n cofrap
kubectl get all -n openfaas
kubectl get all -n openfaas-fn
faas-cli list
kubectl get clusters -n cofrap
```

## URLs des fonctions OpenFaaS
- register : http://localhost:8080/function/generate-password
- 2fa      : http://localhost:8080/function/generate-2fa
- auth     : http://localhost:8080/function/authenticate
- renew    : http://localhost:8080/function/renew-credentials
