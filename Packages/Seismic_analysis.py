import comtypes.client
import sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def connect_etabs():
    try:
        #get the active ETABS object
        EtabsObject=comtypes.client.GetActiveObject("CSI.ETABS.API.ETABSObject")
    except (OSError,comtypes.COMError):
        print("No running instance of the program found or failed to attach.")
        sys.exit(-1)
    #create SapModel object
    SapModel=EtabsObject.SapModel
    return SapModel

def Periods_X_Y(SapModel):
    ret = SapModel.Analyze.RunAnalysis()

    ret = SapModel.DatabaseTables.GetTableForDisplayArray("Modal Participating Mass Ratios",GroupName="")
    n_modes = ret[3]
    table = np.array_split(ret[4],n_modes)
    table = np.array(ret[4]).reshape(n_modes,15)
    table
    max_mode_x = max(table[:,3])
    max_mode_y = max(table[:,4])
    #max_mode_x
    for i in np.arange(n_modes):
        if table[i,3]==max_mode_x:
            Tx = float(table[i,2])
        if table[i,4]==max_mode_y:
            Ty = float(table[i,2])

    return Tx, Ty

def Factors(Z,U,S,Tx,Ty,Rox,Roy,Ia,Ip):
    if Z=="Z1":
        Z_f = 0.10
    elif Z=="Z2":
        Z_f = 0.25
    elif Z=="Z3":
        Z_f = 0.35
    elif Z=="Z4":
        Z_f = 0.45


    if S=="S0":
        S_f=0.8
        Tp = 0.3
        Tl = 3
    elif S=="S1":
        S_f=1
        Tp = 0.4
        Tl = 2.5
    elif S=="S2":
        if Z=="Z1":
            S_f = 1.6
        elif Z=="Z2":
            S_f = 1.2
        elif Z=="Z3":
            S_f = 1.15
        elif Z=="Z4":
            S_f = 1.05
        Tp = 0.6
        Tl = 2
    elif S=="S3":
        if Z=="Z1":
            S_f = 2
        elif Z=="Z2":
            S_f = 1.4
        elif Z=="Z3":
            S_f = 1.2
        elif Z=="Z4":
            S_f = 1.1
        Tp = 1
        Tl = 1.6

    if U=="A":
        U_f = 1.5
    elif U=="B":
        U_f = 1.3
    elif U=="C":
        U_f = 1

    if Tx<Tp:
        Cx=2.5
    elif Tp<Tx<Tl:
        Cx=2.5*(Tp/Tx)
    elif Tx>Tl:
        Cx=2.5*(Tp*Tl/Tx)

    if Ty<Tp:
        Cy=2.5
    elif Tp<Ty<Tl:
        Cy=2.5*(Tp/Ty)
    elif Ty>Tl:
        Cy=2.5*(Tp*Tl/Ty)

    Rx = Rox*Ia*Ip
    Ry = Roy*Ia*Ip

    df = pd.DataFrame(np.array([[Z,Z_f],[U,U_f],[S,S_f]]),columns=["Parámetro","Coeficiente"],index=["Zona","Importancia","Suelo"])

    return Z_f,U_f,S_f,Cx,Cy,Rx,Ry,Tp,Tl,df

def Peso_sismico(U,SapModel,Dead,Live):
    if U =="A" or U =="B":
        Perc = 0.5
        Name_P = "CM+0.50CV"
    elif U == "C":
        Perc = 0.25
        Name_P = "CM+0.25CV"

    ret = SapModel.RespCombo.Add(Name_P,0) # 0 Linear additive
    ret = SapModel.RespCombo.SetCaseList(Name_P,0,Dead,1) # Estamos añadiendo a la combo Name un load case
    ret = SapModel.RespCombo.SetCaseList(Name_P,0,Live,Perc)

    ret = SapModel.Analyze.RunAnalysis() #Temporary analysis

    ret = SapModel.SetPresentUnits(8)
    
    ret = SapModel.DatabaseTables.GetTableForDisplayArray("Base Reactions",GroupName="")

    cols = ret[2]
    index = cols.index('FZ')
    nrows = ret[3]

    table = np.array_split(ret[4],nrows)

    for row in np.arange(nrows):
        if(table[row][0]==Name_P):
            P_tot = float(table[row][index])

    return P_tot,Name_P

def Base_shear(Z_f,U_f,S_f,Cx,Cy,Rx,Ry,P_tot):
    Vx = (Z_f*U_f*S_f*Cx/Rx)*P_tot/1000
    Vy = (Z_f*U_f*S_f*Cy/Ry)*P_tot/1000

    return Vx,Vy

def get_stories(SapModel):
    ret = SapModel.DatabaseTables.GetTableForDisplayArray("Story Definitions",GroupName="")
    n_stories = ret[3]
    stories = np.array_split(ret[4],n_stories)

    he = np.array([])
    story_names = np.array([])

    for story in stories:
        story_names = np.append(story_names,[story[1]])
        he = np.append(he,[story[2]])

    hi = np.array([])
    he = np.flip(he)

    for i in np.arange(n_stories):
        if i!=0:
            hi = np.append(hi,float(he[i])+hi[i-1])
        else:
            hi = np.append(hi,float(he[i]))

    hi = np.flip(hi)

    return n_stories,hi,np.flip(he)

def Seismic_forces(SapModel,Name_P,Tx,Ty,Vx,Vy,n_stories,hi):

    ret = SapModel.DatabaseTables.GetTableForDisplayArray("Story Forces",GroupName="")

    cols = ret[2]
    index_loc = cols.index('Location')
    index_P = cols.index('P')

    n_split = ret[3]

    table = np.array_split(ret[4],n_split)

    P = np.zeros(n_stories)  # Fuerzas axiales en cada story

    j=0
    for i in np.arange(n_split):
        if table[i][1]==Name_P and table[i][index_loc]=='Bottom':  #Fuerzas axiales para combinacion de peso sismico
            P[j] = float(table[i][index_P])/1000
            j=j+1

    Pi = np.zeros(n_stories)  # Peso de cada story
    for i in np.arange(n_stories):
        if i!=0:
            Pi[i] = P[i] - P[i-1]
        else:
            Pi[i] = P[i]

    if Tx<=0.5:
        kx=1
    elif Tx>0.5:
        kx=0.75+0.5*Tx

    if kx>2:
        kx=2

    ## Valor de ky
    if Ty<=0.5:
        ky=1
    elif Ty>0.5:
        ky=0.75+0.5*Ty

    if ky>2:
        ky=2

    ##Fi_x
    coefs_x = Pi*(hi**kx)
    alpha_i_x = coefs_x/np.sum(coefs_x)
    Fi_x = alpha_i_x*Vx

    ##Fi_y
    coefs_y = Pi*(hi**ky)
    alpha_i_y = coefs_y/np.sum(coefs_y)
    Fi_y = alpha_i_y*Vy

    df_x = pd.DataFrame({'hi (m)':hi,'Pi (ton-f)':Pi,'Pihi^k':coefs_x,'αi':alpha_i_x,'Fi=Vαi (ton-f)':Fi_x})
    df_y = pd.DataFrame({'hi (m)':hi,'Pi (ton-f)':Pi,'Pihi^k':coefs_y,'αi':alpha_i_y,'Fi=Vαi (ton-f)':Fi_y})

    df_x = df_x.round(decimals=1)
    df_x['αi'] = df_x['αi'].round(3)
    df_x['Fi=Vαi (ton-f)'] = df_x['Fi=Vαi (ton-f)'].round(2)
    df_y = df_y.round(decimals=1)
    df_y['αi'] = df_y['αi'].round(3)
    df_y['Fi=Vαi (ton-f)'] = df_y['Fi=Vαi (ton-f)'].round(2)


    d = {'Fx':Fi_x,'Fy':Fi_y}
    df = pd.DataFrame(data=d)
    df.to_excel("Fuerzas sísmicas.xlsx")

    return kx,ky,df,df_x,df_y,np.round(Pi,2)

## Aquí se debería asignar fuerzas a diafragmas manualmente...

def Inelastic_Displacements(SapModel,Rx,Ry,Ia,Ip):
    if Ia==1 and Ip ==1:
        Cd = 0.75
    else:
        Cd = 0.85

    ret = SapModel.RespCombo.Add("DX",0)
    ret = SapModel.RespCombo.SetCaseList("DX",0,"Sx",Cd*Rx)

    ret = SapModel.RespCombo.Add("DY",0)
    ret = SapModel.RespCombo.SetCaseList("DY",0,"Sy",Cd*Ry)

    ret = SapModel.Analyze.RunAnalysis()  ##Analysis for all the cases

    return ret

def Plot_drifts(SapModel,n_stories,hi,lim):
    ret = SapModel.DatabaseTables.GetTableForDisplayArray("Story Drifts",GroupName="")

    Dx = np.zeros(n_stories+1)
    Dy = np.zeros(n_stories+1)

    cols = ret[2]
    n_rows = int(ret[3])
    len(ret[4])
    #len(ret[4])/n_rows
    table = np.array(ret[4]).reshape(n_rows,int(len(ret[4])/n_rows))


    j_x = 0
    j_y = 0
    index = cols.index('Drift')
    for i in np.arange(n_rows):
        if table[i][1]=="DX":
            Dx[j_x]=table[i][index]
            j_x = j_x+1
        if table[i][1]=="DY":
            Dy[j_y]=table[i][index]
            j_y = j_y+1

    drift_lim = lim * np.ones(n_stories+1)

    dict_of_fig = dict({
        "data": [{'line': {'color':'red'},
                'x': Dx,
                'y': hi,
                'type':'scatter',
                'name':'Derivas en X',
                'mode':'lines+markers'},
                {'line': {'color':'cyan'},
                'x': Dy,
                'y': hi,
                'type':'scatter',
                'name':'Derivas en Y',
                'mode':'lines+markers'},
                {'line': {'color':'light blue',
                            'dash':'dot'},
                'x': drift_lim,
                'y': hi,
                'type':'scatter',
                'name':'Limite de deriva',
                'mode':'lines',}],
        "layout": {"title":{"text":"Distorsiones por piso",
                            "xanchor":"center",
                            "x":0.5,
                            'font':{'size':30}},
                "xaxis_title":"Distorsión (sin unidades)",
                "yaxis_title":"Nivel",
                "plot_bgcolor":'#FFFAFB',
                "paper_bgcolor":'#FFFAFB',
                "font":{"color":'rgba(255,255,255, 0.3)'}
                }
    })


    fig = go.Figure(dict_of_fig)

    #fig.show()

    return fig

def Irregularidad_piso_blando(SapModel,n_stories,hi):
    ret = SapModel.SetPresentUnits(12)
    ret = SapModel.DatabaseTables.GetTableForDisplayArray("Story Stiffness",GroupName="")
    cols = np.array(ret[2])
    n_rows = int(ret[3])
    table = np.array(ret[4]).reshape(n_rows,len(cols))

    Stiffness_X = table[0:int(n_rows/2),:]
    Stiffness_Y = table[int(n_rows/2):,:]

    df_stf_x = pd.DataFrame(columns=cols,data=Stiffness_X)[["Story","OutputCase","StiffX"]]
    df_stf_y = pd.DataFrame(columns=cols,data=Stiffness_Y)[["Story","OutputCase","StiffY"]]

    array_stf_x = np.flip(df_stf_x.to_numpy(),axis=0)
    array_stf_y = np.flip(df_stf_y.to_numpy(),axis=0)

    array_stf_x = np.hstack((array_stf_x,np.zeros((n_stories,3)).astype(str)))
    array_stf_y = np.hstack((array_stf_y,np.zeros((n_stories,3)).astype(str)))



    #Criterio 1

    

    for i in np.arange(n_stories):
        if i<n_stories-1:
            ratio1_x = 100*float(array_stf_x[i][2])/float(array_stf_x[i+1][2])
            array_stf_x[i][3]=str(round(ratio1_x,2))
            ratio1_y = 100*float(array_stf_y[i][2])/float(array_stf_y[i+1][2])
            array_stf_y[i][3]=str(round(ratio1_y,2))
        if i<n_stories-3:
            ratio2_x = 100*3*float(array_stf_x[i][2])/(float(array_stf_x[i+1][2])+float(array_stf_x[i+2][2])+float(array_stf_x[i+3][2]))
            ratio2_y = 100*3*float(array_stf_y[i][2])/(float(array_stf_y[i+1][2])+float(array_stf_y[i+2][2])+float(array_stf_y[i+3][2]))
            array_stf_x[i][4]=str(round(ratio2_x,2))
            array_stf_y[i][4]=str(round(ratio2_y,2))
        if ratio1_x<0.7 or ratio2_x<0.8:
            array_stf_x[i][5]="Irregularidad de rigidez"
        else:
            array_stf_x[i][5]="Regular"
        if ratio1_y<0.7 or ratio2_y<0.8:
            array_stf_y[i][5]="Irregularidad de rigidez"
        else:
            array_stf_y[i][5]="Regular"
        

    df_stf_x = pd.DataFrame(columns=["Story","OutputCase","StiffX (tonf/m)","Ki/Ki+1 (%)","Ki/((Ki+1 + Ki+2 + Ki+3)/3) (%)","Conclusión"],data=array_stf_x)
    df_stf_y = pd.DataFrame(columns=["Story","OutputCase","StiffY (tonf/m)","Ki/Ki+1 (%)" ,"Ki/((Ki+1 + Ki+2 + Ki+3)/3) (%)","Conclusión"],data=array_stf_y)
    return df_stf_x.iloc[::-1],df_stf_y[::-1]

def Irregularidad_torsional(SapModel,n_stories,he):
    ret = SapModel.DatabaseTables.GetTableForDisplayArray("Story Max Over Avg Drifts",GroupName="")
    cols = ret[2]
    cols
    n_rows = int(ret[3])
    table = np.array(ret[4]).reshape(n_rows,int(len(ret[4])/n_rows))

    Dx_max_d = np.zeros(n_stories)
    Dx_avg_d = np.zeros(n_stories)
    Dy_max_d = np.zeros(n_stories)
    Dy_avg_d = np.zeros(n_stories)
    stories = np.zeros(n_stories).astype('str')
    ratio_x = np.zeros(n_stories)
    ratio_y = np.zeros(n_stories)
    concl_x = np.zeros(n_stories).astype('str')
    concl_y = np.zeros(n_stories).astype('str')


    table
    j_x = 0
    j_y = 0
    index_max_d = cols.index('Max Drift')
    index_avg_d = cols.index('Avg Drift')
    for i in np.arange(n_rows):
        if table[i][1]=="DX":
            Dx_max_d[j_x]=float(table[i][index_max_d])/float(he[j_x])
            Dx_avg_d[j_x]=float(table[i][index_avg_d])/float(he[j_x])
            ratio_x[j_x]=round(Dx_max_d[j_x]/Dx_avg_d[j_x],2)
            if ratio_x[j_x]<=1.3:
                concl_x[j_x]="Regular"
            elif 1.3<ratio_x[j_x]<=1.5:
                concl_x[j_x]="Irregularidad torsional"
            elif ratio_x[j_x]>1.5:
                concl_x[j_x]="Irregularidad torsional extrema"
            stories[j_x]=table[i][0]
            j_x = j_x+1
        if table[i][1]=="DY":
            Dy_max_d[j_y]=float(table[i][index_max_d])/float(he[j_y])
            Dy_avg_d[j_y]=float(table[i][index_avg_d])/float(he[j_y])
            ratio_y[j_y]=round(Dy_max_d[j_y]/Dy_avg_d[j_y],2)
            if ratio_y[j_y]<=1.3:
                concl_y[j_y]="Regular"
            elif 1.3<ratio_y[j_y]<=1.5:
                concl_y[j_y]="Irregularidad torsional"
            elif ratio_y[j_y]>1.5:
                concl_y[j_y]="Irregularidad torsional extrema"
            j_y = j_y+1

    df_drift_x = pd.DataFrame({"Story":stories,"Max Drift":Dx_max_d,"Avg Drift":Dx_avg_d,"Ratio":ratio_x,"Conclusión":concl_x})
    df_drift_y = pd.DataFrame({"Story":stories,"Max Drift":Dy_max_d,"Avg Drift":Dy_avg_d,"Ratio":ratio_y,"Conclusión":concl_y})
    return df_drift_x,df_drift_y

def Irregularidad_masa(n_stories,Pi):
    ratio_1 = np.zeros(n_stories)
    ratio_2 = np.zeros(n_stories)
    stories = np.zeros(n_stories).astype('str')
    concl = np.zeros(n_stories).astype('str')

    for i in np.arange(n_stories):
        if i!=n_stories-1:
            ratio_1[i] = int(round(100*Pi[i]/Pi[i+1],1))
        if i!=0:
            ratio_2[i] = int(round(100*Pi[i]/Pi[i-1],1))
        stories[i] = f"Story{n_stories-i}"
        if ratio_1[i]>=150 or ratio_2[i]>=150:
            concl[i] = "Irregularidad de masa"
        else:
            concl[i] = "Regular"

    Mass_ratios = pd.DataFrame({"Story":stories,"Pi (tonf)":Pi,"Pi/Pi-1 (%)":ratio_1,"Pi/Pi+1 (%)":ratio_2,"Conclusión":concl})
    return Mass_ratios

def Sistema_estructural(SapModel,Pier_x,Pier_y):

    ret = SapModel.SetPresentUnits(12)
    ret = SapModel.DatabaseTables.GetTableForDisplayArray("Load Pattern Definitions - Auto Seismic - User Loads",GroupName="")
    cols = ret[2]
    n_rows = ret[3]
    table = np.array(ret[4]).reshape(n_rows,int(len(ret[4])/n_rows))

    Vx = 0
    Vy = 0
    i_x = cols.index("Fx")
    i_y = cols.index("Fy")

    for i in np.arange(n_rows):
        if table[i][0]=="Sx":
            Vx = Vx + round(float(table[i][i_x]),2)
        if table[i][0]=="Sy":
            Vy = Vy + round(float(table[i][i_y]),2)

    ret = SapModel.DatabaseTables.GetTableForDisplayArray("Pier Forces",GroupName="")
    cols = ret[2]
    n_rows = ret[3]
    table = np.array(ret[4]).reshape(n_rows,int(len(ret[4])/n_rows))

    i_loc = cols.index('Location')
    i_V = cols.index('V2')

    for i in np.arange(n_rows):
        if table[i][2]=='Sx' and table[i][i_loc]=='Bottom' and table[i][0] =='Story1' and table[i][1] == Pier_x:
            V_walls_x = round(float(table[i][i_V]),2)
        if table[i][2]=='Sy' and table[i][i_loc]=='Bottom' and table[i][0] =='Story1' and table[i][1] == Pier_y:
            V_walls_y = round(float(table[i][i_V]),2)

    V_cols_x = Vx - V_walls_x
    V_cols_y = Vy - V_walls_y

    df_V = pd.DataFrame({"Vx (tonf)":[V_walls_x,V_cols_x,Vx],"Vy (tonf)":[V_walls_y,V_cols_y,Vy]},index=["Muros","Pórticos","Total"])
    df_V_perc = pd.DataFrame({"Vx (%)":100*np.array([V_walls_x,V_cols_x,Vx])/Vx,"Vy (%)":100*np.array([V_walls_y,V_cols_y,Vy])/Vy},index=["Muros","Pórticos","Total"])

    return df_V,df_V_perc