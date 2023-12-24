## About Amazon Connect Quick Connects CDK
This solution can be used to create quick connects and associate/disassociate these with queues.

### Requirements

1.[AWS CDK 2.100.0 installed](https://docs.aws.amazon.com/cdk/v2/guide/home.html)

2.[NodeJS 14.x installed](https://nodejs.org/en/download/)

### Installation

Clone the repo

```bash
git clone https://github.com/photosphere/connect-cdk-quick-connects.git
```

cd into the project root folder

```bash
cd connect-cdk-quick-connects
```

#### Create virtual environment

##### via python

Then you should create a virtual environment named .venv

```bash
python -m venv .venv
```

and activate the environment.

On Linux, or OsX 

```bash
source .venv/bin/activate
```
On Windows

```bash
source.bat
```

Then you should install the local requirements

```bash
pip install -r requirements.txt
```
### Build and run the Application Locally

```bash
streamlit run quick_connects/quick_connects_stack.py
```
### Or Build and run the Application on Cloud9

```bash
streamlit run quick_connects/quick_connects_stack.py --server.port 8080 --server.address=0.0.0.0 
```

#### Deployment screenshot
<img width="1573" alt="deploy_screenshot" src="https://github.com/photosphere/connect-cdk-quick-connects/assets/3398595/375df2db-d4ee-40c4-91b9-816448dcfe90">

#### Configuration screenshot
<img width="1557" alt="configure_screenshot" src="https://github.com/photosphere/connect-cdk-quick-connects/assets/3398595/9b41f373-851f-4f86-ac3b-76dc3de5287d">

#### Cloudformation screenshot
<img width="1360" alt="quick-connects-stack" src="https://github.com/photosphere/connect-cdk-quick-connects/assets/3398595/9c2814a9-ba3f-4ba9-b417-1645843d78ee">
