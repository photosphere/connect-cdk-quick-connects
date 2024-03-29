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
import time
from PIL import Image
import json
from datetime import datetime


connect_client = boto3.client("connect")

st.set_page_config(
    page_title="Amazon Connect Quick Connects Deployment Tool!", layout="wide")

# app title
st.header(f"Amazon Connect Quick Connects Deployment Tool!")

connect_instance_id = ''

if os.path.exists('connect.json'):
    with open('connect.json') as f:
        connect_data = json.load(f)
        connect_instance_id = connect_data['Id']
        connect_instance_arn = connect_data['Arn']

# connect configuration
connect_instance_id = st.text_input(
    'Connect Instance Id', value=connect_instance_id)

# load env
load_button = st.button('Load Configuration')
if load_button:
    with st.spinner('Loading......'):
        # connect configuration
        try:
            res = connect_client.describe_instance(
                InstanceId=connect_instance_id)
            connect_filtered = {k: v for k, v in res['Instance'].items() if k in [
                'Id', 'Arn']}
            with open('connect.json', 'w') as f:
                json.dump(connect_filtered, f)

            # queues
            res = connect_client.list_queues(InstanceId=connect_instance_id, QueueTypes=[
                'STANDARD'])

            df = pd.DataFrame(res['QueueSummaryList'])
            if len(df) > 0:
                df.to_csv("queues.csv", index=False)

            # quick connects
            res = connect_client.list_quick_connects(InstanceId=connect_instance_id, QuickConnectTypes=[
                'USER'])

            df = pd.DataFrame(res['QuickConnectSummaryList'])
            if len(df) > 0:
                df.to_csv("quick_connects.csv", index=False)

            # users
            res = connect_client.list_users(
                InstanceId=connect_instance_id)
            df = pd.DataFrame(res['UserSummaryList'])
            if len(df) > 0:
                df.to_csv("users.csv", index=False)

            # contact flows
            res = connect_client.list_contact_flows(
                InstanceId=connect_instance_id, ContactFlowTypes=[
                    'AGENT_TRANSFER',
                ])
            df = pd.DataFrame(res['ContactFlowSummaryList'])
            if len(df) > 0:
                df.to_csv("contact_flows.csv", index=False)

            st.success("Configuration loaded!")
        except Exception as e:
            st.error('Load Configuration Failed')

tab1, tab2 = st.tabs(["Deployment", "Configuration"])

with tab1:
    if load_button or os.path.exists('users.csv'):
        if os.path.exists('users.csv'):
            users = pd.read_csv("users.csv")
            sorted_users = users.sort_values(by=["Username"], ascending=True)

            hide_button = st.checkbox(
                'Hide Users with Quick Connect Already Added')
            if hide_button:
                res = connect_client.list_quick_connects(
                    InstanceId=connect_instance_id, QuickConnectTypes=[
                        'USER'
                    ])
                quick_connects_df = pd.DataFrame(
                    res['QuickConnectSummaryList'])

                if len(quick_connects_df) > 0:
                    mask = sorted_users['Username'].isin(
                        quick_connects_df['Name'])
                    rows_to_remove = sorted_users[mask]
                    sorted_users.drop(index=rows_to_remove.index, inplace=True)

            users_name_selected = st.multiselect(
                'Users', sorted_users['Username'])
        else:
            users_name_selected = st.multiselect('Users')

        users_name_selected_num = len(users_name_selected)
        st.write("Selected Users:" +
                 str(users_name_selected_num)+' (*More than 50 Users Cannot be Selected at A Time*)')

    if load_button or os.path.exists('contact_flows.csv'):
        if os.path.exists('contact_flows.csv'):
            contact_flows = pd.read_csv("contact_flows.csv")
            contact_flows_selected = st.selectbox(
                'Contact Flows', contact_flows['Name'])
            contact_flows_arn_selected = contact_flows.loc[contact_flows['Name']
                                                           == contact_flows_selected, 'Arn'].iloc[0]
        else:
            contact_flows_selected = st.selectbox('Contact Flows')

with tab2:
    if load_button or os.path.exists('queues.csv'):
        queues = pd.read_csv("queues.csv")
        queues_name_selected = st.multiselect('Queues', queues['Name'])

        queues_selected = queues[queues['Name'].isin(queues_name_selected)]
        for index, row in queues_selected.iterrows():
            res = connect_client.list_queue_quick_connects(
                InstanceId=connect_instance_id,
                QueueId=row['Id']
            )
            queue_quick_connects_df = pd.DataFrame(
                res['QuickConnectSummaryList'])
            if len(queue_quick_connects_df) > 0:
                st.write(row['Name'])
                queue_quick_connects_df = queue_quick_connects_df.sort_values(by=[
                    'Name'])
                queue_quick_connects_df = queue_quick_connects_df.reset_index(
                    drop=True)
                st.write(queue_quick_connects_df)

    quick_connects_name_selected_num = 0
    if os.path.exists('quick_connects.csv'):
        quick_connects = pd.read_csv("quick_connects.csv")
        sorted_quick_connects = quick_connects.sort_values(
            by=["Name"], ascending=True)
        quick_connects_name_selected = st.multiselect(
            'Quick Connects', sorted_quick_connects['Name'])
        quick_connects_name_selected_num = len(quick_connects_name_selected)
        st.write("Selected Quick Connects:" +
                 str(quick_connects_name_selected_num)+' (*More than 50 Quick Connects Cannot be Selected at A Time*)')

    col1, col2 = st.columns([2, 8])
    with col1:
        associate_button = st.button('Associate', disabled=(
            quick_connects_name_selected_num > 50))
        if associate_button:

            queues_selected = queues[queues['Name'].isin(queues_name_selected)]
            queues_selected.to_csv('queues_selected.csv', index=False)

            quick_connects_selected = quick_connects[quick_connects['Name'].isin(
                quick_connects_name_selected)]
            quick_connects_selected.to_csv(
                'quick_connects_selected.csv', index=False)
            quick_connects_Id_selected = quick_connects_selected['Id'].tolist()

            for index, row in queues_selected.iterrows():
                res = connect_client.associate_queue_quick_connects(
                    InstanceId=connect_instance_id,
                    QueueId=row['Id'],
                    QuickConnectIds=quick_connects_Id_selected
                )

    with col2:
        disassociate_button = st.button('Disassociate')
        if disassociate_button:
            for index, row in queues_selected.iterrows():
                res = connect_client.list_queue_quick_connects(
                    InstanceId=connect_instance_id,
                    QueueId=row['Id']
                )
                queue_quick_connects_df = pd.DataFrame(
                    res['QuickConnectSummaryList'])

                connect_client.disassociate_queue_quick_connects(InstanceId=connect_instance_id,
                                                                 QueueId=row['Id'], QuickConnectIds=queue_quick_connects_df['Id'].tolist())

    if associate_button:
        st.success('Associate Successfully!')

    if disassociate_button:
        st.success('Disassociate Successfully!')


with st.sidebar:

    # stack name
    quick_connects_name = st.text_input('Quick Connects Name (Required)')

    st.write('*You must click follow button to save configuration before deployment*')

    # save env
    if st.button('Save Configuration'):
        os.environ["connect_instance_arn"] = connect_instance_arn
        os.environ["quick_connects_name"] = quick_connects_name

        users_selected = users[users['Username'].isin(users_name_selected)]
        users_selected.to_csv('users_selected.csv', index=False)

        os.environ["contact_flows_arn_selected"] = contact_flows_arn_selected

        st.success("ENV has been set")

    # deploy cdk
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

    # destroy cdk
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


class QuickConnectsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # parameter
        connect_instance_arn = os.environ["connect_instance_arn"]
        contact_flows_arn_selected = os.environ["contact_flows_arn_selected"]

        now = datetime.now()
        formatted_now = now.strftime("%Y%m%d%H%M%S")

        # load users
        users_df = pd.read_csv("users_selected.csv")
        for index, row in users_df.iterrows():
            cfn_user = connect.CfnQuickConnect(self, "CfnQuickConnect"+formatted_now+str(index),
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
