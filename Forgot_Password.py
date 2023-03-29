import os
import yaml
import streamlit as st
import streamlit_authenticator as stauth
from yaml import SafeLoader


def forget_password():
    config_path = os.path.join(os.getcwd(), 'config')
    st.markdown("<style> ul {display: inline-block;} </style>", unsafe_allow_html=True)

    with open(os.path.join(config_path, "users.yaml")) as file:
        config = yaml.load(file, Loader=SafeLoader)
    try:
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
            config['preauthorized']
        )
        password_forgot_username = authenticator.forgot_password('Forgot Password')
        if password_forgot_username:
            st.success('Username sent securely')
            # Username to be transferred to user securely
        else:
            st.error('Email not found')
    except Exception as e:
        st.error(e)
