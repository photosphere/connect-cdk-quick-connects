from aws_cdk import (
    # Duration,
    Stack,
    CfnTag
    # aws_sqs as sqs,
)
from constructs import Construct
from aws_cdk import aws_connect as connect
import os
import subprocess
import streamlit as st
import pandas as pd
import boto3
import sys
import time
from PIL import Image
import json
from datetime import datetime

# Constants
MAX_SELECTABLE_USERS = 50
MAX_SELECTABLE_QUICK_CONNECTS = 50

# Initialize AWS clients
connect_client = boto3.client("connect")
cfm_client = boto3.client("cloudformation")

# Streamlit page configuration
st.set_page_config(
    page_title="Amazon Connect Quick Connects Deployment Tool!", layout="wide")
st.header("Amazon Connect Quick Connects Deployment Tool!")

# Helper functions


def load_json_file(filename):
    if os.path.exists(filename):
        with open(filename) as f:
            return json.load(f)
    return {}


def save_json_file(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)


def load_csv_file(filename):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return pd.DataFrame()


def save_csv_file(filename, df):
    df.to_csv(filename, index=False)


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def get_summary_list(action):
    def_val = "SummaryList"
    if action == "list_queues":
        def_val = "Queue" + def_val
    elif action == "list_quick_connects":
        def_val = "QuickConnect" + def_val
    elif action == "list_users":
        def_val = "User" + def_val
    elif action == "list_contact_flows":
        def_val = "ContactFlow" + def_val
    return def_val


def get_file_name(action):
    def_val = ""
    if action == "list_queues":
        def_val = "queues.csv"
    elif action == "list_quick_connects":
        def_val = "quick_connects.csv"
    elif action == "list_users":
        def_val = "users.csv"
    elif action == "list_contact_flows":
        def_val = "contact_flows.csv"
    return def_val

    # Load configuration
connect_data = load_json_file('connect.json')
connect_instance_id = connect_data.get('Id', '')
connect_instance_arn = connect_data.get('Arn', '')

# Connect configuration
connect_instance_id = st.text_input(
    'Connect Instance Id', value=connect_instance_id)
max_results = st.number_input(
    "Queues/QuickConnects/Users Max Results", value=200)

# Load configuration button
if st.button('Load Configuration'):
    with st.spinner('Loading......'):
        try:
            # Load and save Connect instance data
            res = connect_client.describe_instance(
                InstanceId=connect_instance_id)
            connect_filtered = {k: v for k, v in res['Instance'].items() if k in [
                'Id', 'Arn']}
            save_json_file('connect.json', connect_filtered)

            # Load and save queues, quick connects, users, and contact flows
            for entity, params in [
                ('list_queues', {'QueueTypes': ['STANDARD']}),
                ('list_quick_connects', {'QuickConnectTypes': ['USER']}),
                ('list_users', {}),
                ('list_contact_flows', {
                 'ContactFlowTypes': ['AGENT_TRANSFER']})
            ]:
                res = getattr(connect_client, f'{entity}')(
                    InstanceId=connect_instance_id, MaxResults=max_results, **params)
                df = pd.DataFrame(res[get_summary_list(f'{entity}')])
                if not df.empty:
                    df = df.sort_values(
                        by=["Name" if entity != 'list_users' else "Username"], ascending=True)
                    save_csv_file(get_file_name(f"{entity}"), df)
                else:
                    delete_file(get_file_name(f"{entity}"))

            st.success("Configuration loaded!")
        except Exception as e:
            st.error(f'Load Configuration Failed: {str(e)}')

# Tabs
tab1, tab2 = st.tabs(["Deployment", "Configuration"])

# Deployment tab
with tab1:
    users = load_csv_file("users.csv")
    quick_connects = load_csv_file("quick_connects.csv")

    if not users.empty:
        st.write(f'Users: {len(users)}')
        st.write(f'Quick Connects: {len(quick_connects)}')

        if st.checkbox('Hide Users with Quick Connect Already Added'):
            if not quick_connects.empty:
                users = users[~users['Username'].isin(quick_connects['Name'])]
                st.write(f'Users with Quick Connects Added: {len(users)}')

        users_name_selected = st.multiselect(
            f'Users({len(users)})', users['Username'])
        st.write(
            f"Selected Users: {len(users_name_selected)} (*More than {MAX_SELECTABLE_USERS} Users Cannot be Selected at A Time*)")

    contact_flows = load_csv_file("contact_flows.csv")
    if not contact_flows.empty:
        contact_flows_selected = st.selectbox(
            f'Contact Flows({len(contact_flows)})', contact_flows['Name'])
        contact_flows_arn_selected = contact_flows.loc[contact_flows['Name']
                                                       == contact_flows_selected, 'Arn'].iloc[0]

# Configuration tab
with tab2:
    queues = load_csv_file("queues.csv")
    if not queues.empty:
        queues_name_selected = st.multiselect(
            f'Queues({len(queues)})', queues['Name'])
        queues_selected = queues[queues['Name'].isin(queues_name_selected)]

        for _, row in queues_selected.iterrows():
            res = connect_client.list_queue_quick_connects(
                InstanceId=connect_instance_id, QueueId=row['Id'])
            queue_quick_connects_df = pd.DataFrame(
                res['QuickConnectSummaryList'])
            if not queue_quick_connects_df.empty:
                st.write(row['Name'])
                st.write(queue_quick_connects_df.sort_values(
                    by=['Name']).reset_index(drop=True))

    quick_connects_name_selected = []
    quick_connects = load_csv_file("quick_connects.csv")
    if not quick_connects.empty:
        quick_connects_name_selected = st.multiselect(
            f'Quick Connects({len(quick_connects)})', quick_connects['Name'])
        st.write(
            f"Selected Quick Connects: {len(quick_connects_name_selected)} (*More than {MAX_SELECTABLE_QUICK_CONNECTS} Quick Connects Cannot be Selected at A Time*)")

    col1, col2 = st.columns([2, 8])
    with col1:
        if st.button('Associate', disabled=(len(quick_connects_name_selected) > MAX_SELECTABLE_QUICK_CONNECTS)):
            queues_selected = queues[queues['Name'].isin(queues_name_selected)]
            save_csv_file('queues_selected.csv', queues_selected)

            quick_connects_selected = quick_connects[quick_connects['Name'].isin(
                quick_connects_name_selected)]
            save_csv_file('quick_connects_selected.csv',
                          quick_connects_selected)

            for _, row in queues_selected.iterrows():
                connect_client.associate_queue_quick_connects(
                    InstanceId=connect_instance_id,
                    QueueId=row['Id'],
                    QuickConnectIds=quick_connects_selected['Id'].tolist()
                )
            st.success('Associate Successfully!')

    with col2:
        if st.button('Disassociate'):
            for _, row in queues_selected.iterrows():
                res = connect_client.list_queue_quick_connects(
                    InstanceId=connect_instance_id, QueueId=row['Id'])
                queue_quick_connects_df = pd.DataFrame(
                    res['QuickConnectSummaryList'])
                connect_client.disassociate_queue_quick_connects(
                    InstanceId=connect_instance_id,
                    QueueId=row['Id'],
                    QuickConnectIds=queue_quick_connects_df['Id'].tolist()
                )
            st.success('Disassociate Successfully!')

# Sidebar
with st.sidebar:
    quick_connects_name = st.text_input('Quick Connects Name (Required)')
    st.write('*You must click follow button to save configuration before deployment*')

    if st.button('Save Configuration'):
        os.environ["connect_instance_arn"] = connect_instance_arn
        os.environ["quick_connects_name"] = quick_connects_name
        users_selected = users[users['Username'].isin(users_name_selected)]
        save_csv_file('users_selected.csv', users_selected)
        os.environ["contact_flows_arn_selected"] = contact_flows_arn_selected
        st.success("ENV has been set")

    st.subheader('CDK Deployment', divider="rainbow")
    if st.button('Deploy CDK Stack'):
        try:
            p = subprocess.Popen(['cdk', 'deploy'])
            out, err = p.communicate()
        except OSError as e:
            print("Exception while running subprocess: ", e)
        except ValueError as e:
            print("Invalid arguments: ", e)
        except:
            print("Unexpected error:", sys.exc_info()[0])
        else:
            if out:
                print(out.decode('utf-8'))
            if err:
                print(err.decode('utf-8'), file=sys.stderr)

        st.write('CDK stack initialized...........')
        time.sleep(5)
        with st.spinner('Deploying......'):
            cfm_client = boto3.client("cloudformation")
            try:
                while True:
                    time.sleep(5)
                    res = cfm_client.describe_stacks()
                    stacks = [i['StackName'] for i in res['Stacks']]
                    if os.environ["quick_connects_name"] in stacks:
                        res = cfm_client.describe_stacks(
                            StackName=os.environ["quick_connects_name"])
                        status = res['Stacks'][0]['StackStatus']
                        if status == 'CREATE_COMPLETE':
                            st.success('Deploy complete!')
                            break
                        elif status in ['CREATE_FAILED', 'ROLLBACK_COMPLETE']:
                            st.error(
                                'Deploy failed, please check CloudFormation event for detailed messages.')
                            break
                        else:
                            continue
            except Exception as e:
                st.error('Deploy Failed')

    st.subheader('Clean Resources', divider="rainbow")
    if st.button('Destroy CDK Stack'):
        try:
            p = subprocess.Popen(['cdk', 'destroy', '--force'])
            out, err = p.communicate()
        except OSError as e:
            print("Exception while running subprocess: ", e)
        except ValueError as e:
            print("Invalid arguments: ", e)
        except:
            print("Unexpected error:", sys.exc_info()[0])
        else:
            if out:
                print(out.decode('utf-8'))
            if err:
                print(err.decode('utf-8'), file=sys.stderr)

        st.write('Destroying CDK stack...........')
        time.sleep(5)
        with st.spinner('Destroying......'):
            cfm_client = boto3.client("cloudformation")
            try:
                while True:
                    time.sleep(5)
                    res = cfm_client.describe_stacks()
                    stacks = [i['StackName'] for i in res['Stacks']]
                    if os.environ["quick_connects_name"] not in stacks:
                        st.success('Destroy complete!')
                        break
                    else:
                        res = cfm_client.describe_stacks(
                            StackName=os.environ["quick_connects_name"])
                        status = res['Stacks'][0]['StackStatus']
                        if status == 'DELETE_FAILED':
                            st.error(
                                'Destroy failed, please check CloudFormation event for detailed messages.')
                            break
                        else:
                            continue
            except Exception as e:
                st.error('Failed')

# CDK Stack definition


class QuickConnectsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        connect_instance_arn = os.environ["connect_instance_arn"]
        contact_flows_arn_selected = os.environ["contact_flows_arn_selected"]
        now = datetime.now().strftime("%Y%m%d%H%M%S")

        users_df = pd.read_csv("users_selected.csv")
        for index, row in users_df.iterrows():
            connect.CfnQuickConnect(self, f"CfnQuickConnect{now}{index}",
                                    instance_arn=connect_instance_arn,
                                    name=row['Username'],
                                    quick_connect_config=connect.CfnQuickConnect.QuickConnectConfigProperty(
                                        quick_connect_type="USER",
                                        user_config=connect.CfnQuickConnect.UserQuickConnectConfigProperty(
                                            contact_flow_arn=contact_flows_arn_selected,
                                            user_arn=row['Arn']
                                        )
                                    )
                                    )
