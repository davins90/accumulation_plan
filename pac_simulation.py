import pandas as pd
import numpy as np
import streamlit as st
import base64
import io

# Dati input
st.title('Simulatore PAC')
st.markdown("Simula l'andamento di un PAC in base ai dati dei rendimenti reali medi annui imputati (il default è impostato sui valori del [CreditSuisse Yearbook](https://www.credit-suisse.com/about-us/it/reports-ricerca/studi-pubblicazioni.html)).")

numero_pac = st.number_input('Quanti PAC vuoi simulare?',step=1.0)

keys = ['numero_asset','mesi','tempo','infla','azioni','bond_lt','bond_bt','versamento_mensile']
dati_input = {key: {} for key in keys}

final = pd.DataFrame()
ris = {}

for i in range(int(numero_pac)):
    ris['pac_{}'.format(i)] = dati_input
    

st.header('Dati di input')
for i in ris.keys():
    st.subheader('Inserisci i dati di input del ' + i)
    ris[i]['numero_asset'] = st.multiselect('Da quante asset class è costituisto il PAC',[1,2,3],[1], key=i)
    ris[i]['tipo_asset'] = st.multiselect('Quale/quali asset class sono contenute nel PAC?',['Azioni','Bond','Materasso'],['Azioni'], key=i)
    ris[i]['mesi'] = 12
    ris[i]['tempo'] = st.number_input('Per quanti anni rimane attivo il PAC',value=20, key=i)
    ris[i]['infla'] = st.number_input('Inserire target % di inflazione media annua, come proxy del "lasciare i soldi sotto al materasso"',value=2.0, key=i)
    ris[i]['azioni'] = st.number_input('Inserire rendimento % reale medio annuo dell asset class azionaria globale',value=5.3, key=i)
    ris[i]['bond_lt'] = st.number_input('Inserire rendimento % reale medio annuo dell asset class obbligazionaria a lungo termine statunitense',value=2.1, key=i)
    ris[i]['bond_bt'] = st.number_input('Inserire rendimento % reale medio annuo dell asset class obbligazionaria a breve termine statunitense',value=0.8, key=i)
    ris[i]['versamento_mensile'] = st.number_input('Inserire ammontare versamento mensile del PAC', value = 100, key=i)
    
    rend_infla_real = -ris[i]['infla']/100
    rend_bond_real = (ris[i]['bond_lt']/100 + ris[i]['bond_bt']/100)/2
    rend_az_mon = ((1+ris[i]['azioni']/100)**(1/ris[i]['mesi']))-1
    rend_bond_mon = ((1+rend_bond_real)**(1/ris[i]['mesi']))-1
    rend_infla_mon = ((1+rend_infla_real)**(1/ris[i]['mesi']))-1
    
    v = [ris[i]['versamento_mensile']]*int(numero_pac)
    ptf = np.zeros((1,ris[i]['mesi']*ris[i]['tempo']))
    
    if ris[i]['numero_asset'] == 1:
        if ris[i]['tipo_asset'] == 'Azioni':
            rend_ptf = rend_az_mon
        elif ris[i]['tipo_asset'] == 'Bond':
            rend_ptf = rend_bond_mon
        else:
            rend_ptf = rend_infla_mon
    elif ris[i]['numero_asset'] == 2:
        if ris[i]['tipo_asset'] == ['Azioni','Bond']:
            rend_ptf = (rend_az_mon+rend_bond_mon)/ris[i]['numero_asset'][0]
        elif ris[i]['tipo_asset'] == ['Azioni','Materasso']:
            rend_ptf = (rend_az_mon+rend_infla_mon)/ris[i]['numero_asset'][0]
        else:
            rend_ptf = (rend_bond_mon+rend_infla_mon)/ris[i]['numero_asset'][0]
    else:
        rend_ptf = (rend_az_mon+rend_bond_mon+rend_infla_mon)/ris[i]['numero_asset'][0]
    
    for z in range(ptf.shape[0]):
        for j in range(ptf.shape[1]):
            if j == 0:
                ptf[z][j] = v[0]
            else:
                ptf[z][j] = ptf[z][j-1] + (ptf[z][j-1]*rend_ptf)+v[0]
    
    ptf = pd.DataFrame(ptf.T,columns=['nav'])
    st.write('Il versato per il pac mensile a',v[0],' euro è pari a: ',v[0]*ptf.shape[0],'euro in ',int(ptf.shape[0]/12),' anni. Il montante finale è pari a: ',ptf.tail(1).iloc[0].values[0],'euro.')
    st.write('Il guadagno al netto dei versamenti è di: ',ptf.tail(1).iloc[0].values[0] - v[0]*ptf.shape[0],' euro, pari al ',((ptf.tail(1).iloc[0].values[0])/(v[0]*ptf.shape[0])-1)*100,'%')

    
    ris[i]['time_series'] = ptf['nav'].to_dict()
    final = pd.concat([final, pd.DataFrame.from_dict(ris[i]['time_series'],orient='index')],axis=1)
    final = final.rename(columns={0:i})
    

            
towrite = io.BytesIO()
downloaded_file = final.to_excel(towrite, encoding='utf-8', index=False, header=True)
towrite.seek(0)  
b64 = base64.b64encode(towrite.read()).decode()  
linko= f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="pac_simulation.xlsx">Download excel file</a>'
st.markdown(linko, unsafe_allow_html=True)