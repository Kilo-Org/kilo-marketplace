# Pipeline Templates Reference

This document contains comprehensive pipeline configuration examples for various CI/CD platforms and use cases. **All configurations are customizable** - the skill will prompt you for your specific requirements.

## Customization Options

When requesting a pipeline, you can specify:

| Option | Examples |
|--------|----------|
| **Operating System** | `ubuntu-latest`, `windows-latest`, `macos-latest`, self-hosted runners |
| **Language** | Node.js, Python, Ruby, Go, Rust, Java, .NET, PHP |
| **Versions** | Single version or matrix (e.g., `['18.x', '20.x', '22.x']`) |
| **Package Manager** | npm, yarn, pnpm, pip, bundler, cargo, maven, gradle |
| **Container Base** | Any Docker image (e.g., `node:20`, `python:3.11`, `golang:1.21`) |

## GitHub Actions Templates

### Node.js with Matrix Strategy

```yaml
name: Node.js CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]  # Customize: include/exclude OS
        node-version: [18.x, 20.x, 22.x]  # Customize: versions to test
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Use Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage/lcov.info
```

> **Tip**: Remove OS from matrix to test on a single platform for faster builds.

### Python with Virtual Environment

```yaml
name: Python CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]  # Customize: OS list
        python-version: ['3.10', '3.11', '3.12']  # Customize: versions
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
      
      - name: Lint with flake8
        run: |
          pip install flake8
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
      
      - name: Run tests
        run: pytest
```

### Docker Build and Push

```yaml
name: Docker Build and Push

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest  # Or self-hosted runner
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: myapp/myapp
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-
            type=raw,value={{version}},enable={{is_version_tag}}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=myapp/myapp:latest
          cache-to: type=inline
```

---

## GitLab CI Templates

### Multi-Stage Pipeline

```yaml
stages:
  - lint
  - test
  - build
  - deploy

variables:
  NODE_VERSION: "20"  # Customize: any version

lint:
  stage: lint
  image: node:${NODE_VERSION}  # Customize: any Docker image
  script:
    - npm ci
    - npm run lint
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/

test:
  stage: test
  image: node:${NODE_VERSION}
  script:
    - npm ci
    - npm test -- --coverage
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

build:
  stage: build
  image: node:${NODE_VERSION}
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week

deploy:
  stage: deploy
  script:
    - echo "Deploying to production"
  only:
    - main
```

### Docker Build with GitLab Registry

```yaml
stages:
  - build
  - deploy

build:
  stage: build
  image: docker:24  # Customize: any Docker version
  services:
    - docker:24-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  image: alpine:latest
  script:
    - apk add --no-cache curl
    - echo "Deploying $CI_COMMIT_SHA"
  only:
    - main
```

---

## Azure DevOps Templates

### Node.js Application

```yaml
trigger:
  branches:
    include:
      - main
      - develop

pr:
  branches:
    include:
      - main

pool:
  vmImage: 'ubuntu-latest'  # Customize: ubuntu-latest, windows-latest, macOS-latest

stages:
  - stage: Build
    jobs:
      - job: BuildJob
        steps:
          - task: NodeTool@0
            inputs:
              versionSpec: '20.x'  # Customize: version
            displayName: 'Install Node.js'

          - script: |
              npm install
              npm run lint
              npm test
            displayName: 'Install, lint, and test'

          - script: |
              npm run build
            displayName: 'Build'

          - publish: $(System.DefaultWorkingDirectory)/dist
            artifact: dist

  - stage: Deploy
    dependsOn: Build
    jobs:
      - deployment: DeployJob
        environment: 'production'
        strategy:
          runOnce:
            deploy:
              steps:
                - script: echo "Deploying to production"
```

---

## Comparison Matrix

| Feature | GitHub Actions | GitLab CI | Azure DevOps |
| -------- | --------------- | --------- | ------------ |
| **Syntax** | YAML | YAML | YAML |
| **Host** | GitHub-hosted or self-hosted | GitLab-hosted or self-hosted | Azure-hosted or self-hosted |
| **Free Minutes** | 2000/month (public), 2000/min (private) | 2000/min | 1800/min |
| **Matrix Strategy** | Yes | Yes | Yes |
| **Self-Hosted Runners** | Yes (any OS) | Yes (GitLab Runner) | Yes (any OS) |
| **Container Support** | Docker | Docker | Docker |
| **Secrets Management** | Yes | Yes | Yes |

## Best Practices

1. **Use caching** - Cache dependencies to speed up builds
2. **Fail fast** - Run fast checks (linting) before slow checks (tests)
3. **Use matrix strategy** - Test against multiple versions
4. **Keep secrets secure** - Never expose secrets in logs or config
5. **Use versions for actions** - Pin to specific versions (e.g., v4, not @master)
6. **Clean up artifacts** - Set expiration dates for artifacts
