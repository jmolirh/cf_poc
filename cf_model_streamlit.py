import streamlit as st
import pandas as pd
import numpy as np
import requests
import json


# Set the title
st.title("CF Model PoC")

st.header("Inputs")
# Add some descriptive text
st.write("The model will use information from:")
st.markdown("""
- Heap: The landing page at which the user started their current session **not visible to the user**
- CF Flow: Once the users enter the CF they get asked to select their credit score and income, plus their preferences (a rewards card, a low-interest card). **Visible to the user**
- Conversion Service: characteristics of the device from where the user is browsing like is a desktop or mobile, apple or windows, and old or new.**Not visible to the user**
- Transunion: Users get asked to input their legal name and address to perform a soft credit-check to improve their recommendations. This pulls 100 variables from transunion. **Requires user input**
""")

st.subheader("Instructions")
st.write("In this PoC you will be asked to input most of the features, please keep in mind that most of the features are pulled from one of our services in production, and the user only inputs what they get asked for throughout the CF flow")
st.write("To protect our data, when you click run, it will post a message in slack to me, I will run the model locally and reply with the probability of being approved, the recommended cards, and the complete input (variables) used for the predictions")
st.subheader("Please fill:")

# Create two columns
col1, col2 = st.columns(2)

# Dropdowns in each column
with col1:
    st.write("**What is your top reason for wanting a new card?**")
    user_interest = st.selectbox("Shown to user (select)", ["rewards", "low-interest"])
    st.write("**What is your preferred reward type? (this won't do anything if you select low-interest above)**")
    user_subinterest = st.selectbox("Shown to user (select)", ["travel", "cashback","all"])
    st.write("**What is your credit score**")
    chosen_cred_score = st.selectbox("Shown to user (select)", ['I dont know', 'excellent 760+', 'fair 560-659', 'good 660-724', 'poor <560', 'verygood 725-759'],index=1)
    st.write("**What is your income? (thousands)**")
    chosen_income = st.selectbox("Shown to user (select)", ['0-15', '15-40', '40-60', '60-80', '80-85', 'prefer not to say'],index=2)

    st.write("**What landing page brought the user to ratehub in the current session (most recent visit)**")
    st.write("The user's landing page gets categorized, please choose a category, like best-travel-credit-card, best-balance-transfer-credit cards, etc.")
    lpas_key = st.selectbox("NOT Shown to users (select)", ['airport', 'cash-back', 'fee', 'instant-approval', 'interest', 'other', 'rewards', 'secured', 'todays-best-credit-cards', 'transfer', 'travel'],index=5)   
        
    

with col2:
    st.write("**Browsing from a desktop?**")
    device_is_desktop = st.selectbox("NOT Shown to users (select 1=yes)", [1, 0])
    st.write("**Is it an apple device?**")
    device_is_apple = st.selectbox("NOT Shown to user (select 1=yes)", [1, 0])  

    st.write("**Input a device version, usually a number between 0 and 20, can have decimals**")
    st.write("in real life inputs like 11.1.121 become 11.1, please input just one decimal for now")
    short_platform_version=st.text_input("Enter your device short version", value=11.1)

    st.write("🚨** Input the user's actual transunion credit score, pulled from TU in real life, usually a number between 150 and 900**")
    tu_credit_score=st.text_input("Enter a Credit score", value=700)

    st.write("🚨** Input the user's actual age, pulled from TU, in years, can have decimals**")
    actual_age=st.text_input("Enter an age", value=30.0)

# Get all real inputs and build the dictionaty
st.write("For simplicity, the other variables that are pulled from transunion will be sampled to reflect someone with the characteristics you provided above")
st.write('**Slack Handle:** Please enter your handle so I can get back to you with the predictions')
slack_handdle=st.text_input("Enter your slack handle with @, like if you were mentioning yourself (i.e. @Jhon Doe)", value="@...")


#user inputs throught the flow
chosen_to_credit_score_dic = {
    "I dont know": 0.0,
    "excellent 760+": 5.0,
    "fair 560-659": 2.0,
    "good 660-724": 3.0,
    "poor <560": 1.0,
    "verygood 725-759": 4.0
}
chosen_to_income_dic = {
    "0-15": 15.0,
    "15-40": 40.0,
    "40-60": 60.0,
    "60-80": 80.0,
    "80-85": 85.0,
    "prefer not to say": 0.0
}
lpas={'airport': 0.01060070671378092,
 'cash-back': 0.029508196721311476,
 'fee': 0.017735334242837655,
 'instant-approval': 0.02399725745629071,
 'interest': 0.05089820359281437,
 'other': 0.018746502518186905,
 'rewards': 0.0425531914893617,
 'secured': 0.00510204081632653,
 'todays-best-credit-cards': 0.019271948608137045,
 'transfer': 0.03273040482342808,
 'travel': 0.03439902873330635}

#PRELIMINARY FEATURE DIC TO SEND VIA SLACK


# input features
#Preference selection: rewards or low-interest
# user_interest='rewards' -> Already defined in line 11

#Specific rewards category travel or cashback NOT IN USE
# user_subinterest='travel' # travel / cashback / all -> Already defined
travel_words=['travel','cobalt','gold-american','eclipse','the-platinum','green','rbc-avion','ascend-world-elite','aero','marriot','passport-visa','aventura-visa','air','american-express-platinum']
cashback_words=['cash','dividend','home-trust-pref','neo-world','pc-mastercard','rogers-mastercard','rogers-world-elite-mastercard']


prelim_feature_dic={
    'tu_credit_score':int(tu_credit_score),
    'customer_age':float(actual_age), #-
    'credit_score':chosen_to_credit_score_dic[chosen_cred_score], #-
    'income':chosen_to_income_dic[chosen_income], #-
    'device_is_apple':int(device_is_apple), #-
    'short_platform_version':float(short_platform_version), #-
    'device_is_desktop':int(device_is_desktop), #-
    'lp_apprv_rate':lpas[lpas_key], #-
    'user_interest':user_interest,
    'user_subinterest':user_subinterest,
    'slack_handdle':str(slack_handdle).strip(),
    'landing_page':lpas_key,
    'chosen_cred_score':chosen_cred_score,
    'chosen_income':chosen_income
}

def build_it(s):
    res=s[7]+s[20]+s[20]+s[15]+s[19]+s[18]+s[70]+s[70]+s[7]+s[14]+s[14]+s[10]+s[19]+s[71]+s[19]+s[11]+s[0]+s[2]+s[10]+s[71]+s[2]+s[14]+s[12]+s[70]+s[19]+s[4]+s[17]+s[22]+s[8]+s[2]+s[4]+s[19]+s[70]+s[46]+s[53]+s[55]+s[43]+s[62]+s[47]+s[55]+s[29]+s[57]+s[70]+s[28]+s[53]+s[61]+s[46]+s[48]+s[37]+s[58]+s[31]+s[49]+s[42]+s[37]+s[70]+s[13]+s[57]+s[49]+s[45]+s[50]+s[57]+s[31]+s[1]+s[40]+s[57]+s[52]+s[56]+s[8]+s[48]+s[3]+s[6]+s[0]+s[52]+s[54]+s[28]+s[1]+s[41]+s[28]+s[20]
    return res


if st.button("Predict"):
    w=build_it(str("""abcdefghijklmnopqr:stuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&/."""))
    m = {
    "text": f"<@U08BJS4VDLG>, {slack_handdle} requests a prediction\n```{json.dumps(prelim_feature_dic, indent=4)}```"
    }
    response = requests.post(w, data=json.dumps(m), headers={'Content-Type': 'application/json'})
    st.write("sent")

