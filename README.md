## About Amazon Connect Quick Connects CDK
This solution can be used to create quick connects and associate/disassociate these with queues.

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

Then you should install the local requirements

```bash
pip install -r requirements.txt
```


### Build and run the Application Locally

```bash
streamlit run quick_connects/quick_connects_stack.py
```