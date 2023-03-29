import os
import yaml
import streamlit as st
import streamlit_authenticator as stauth
from yaml import SafeLoader

def register():
    st.title("User Registration Page")
    config_path = os.path.join(os.getcwd(), 'config')

    with open(os.path.join(config_path, "users.yaml")) as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )
    try:

        if authenticator.register_user('Register user', preauthorization=False):
            st.success('User registered successfully')


        #if authenticator.registered_user('Register user', preauthorization=False):
            #st.success('User registered successfully')
            with open(os.path.join(config_path, "users.yaml"), "w") as file:
                yaml.dump(config, file, default_flow_style=False)
    except Exception as e:
        st.error(e)
