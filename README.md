## About Amazon Connect Quick Connects CDK
This solution can be used to create quick connects and associate/disassociate these with queues.

## Build
```
$ pip install streamlit
```

## Install dependencies
```
$ git clone https://github.com/photosphere/connect-cdk-quick-connects.git
$ cd connect-cdk-quick-connects
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

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

On Linux, OsX or in a Windows Git Bash terminal it's

```bash
source .venv/Scripts/activate
```

or alternatively

```bash
source .venv/bin/activate
```

In a Windows terminal it's

```bash
.venv/Scripts/activate.bat
```

Then you should install the local requirements

```bash
pip install -r requirements_local.txt
```

Install streamlit

```bash
pip install streamlit
```

### Build and run the Application Locally

```bash
streamlit run quick_connects/quick_connects_stack.py
```