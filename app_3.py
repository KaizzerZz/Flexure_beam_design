from Packages.Sections import Sections
from Packages.Viga import Seccion_Viga,Viga
import streamlit as st
import numpy as np
import subprocess
from jinja2 import Environment, FileSystemLoader
import os


path = "./Images"

def Define_beam(fc,fy,Es,b,h,strr,s_d_t,espacing,s_d_c,path):
    L = 1#m
    ref = "Otro"
    
    beam = Viga(L,fc,fy,Es)
    beam.Rec_section(b,h)
    beam_sec_1 = Seccion_Viga(beam,ref,strr,recover=4)
    beam_sec_1.Steel_distribution_t(s_d_t,espacing)
    beam_sec_1.Steel_distribution_c(s_d_c)
    beam_sec_1.Create_section()
    beam_sec_1.Find_c()
    beam_sec_1.Asmin_E060()
    beam_sec_1.Plot_rec_beam(path)
    beam_sec_1.section.Plot_comp_defo()
    beam_sec_1.section.Save_comp_defo(path)
    return beam_sec_1

def Make_calculus(beam,s_d_t,espacing,s_d_c,path):
    
    return beam

def Generate_report_download(beam):
    
    env = Environment(
        
        loader=FileSystemLoader(''),  ##This will set the "relative directory" the current directory where this file is located
    )

    template = env.get_template('./Reports/template_beam_section.tex')      

    st.write(os.path.isfile('./Reports/report_beam_section.tex'))
    with open('./Reports/report_beam_section.tex', "w",encoding='utf-8') as f:
        try:
            f.write(template.render(beam=beam))
            #st.write("Succesfully written")
        except:
            pass

    #st.write(os.path.isfile('./Reports/report_beam_section.tex'))
    os.system(f"pdflatex --output-directory=./Reports ./Reports/report_beam_section.tex")

def Generate_report_web(beam):
    #beam = Flexure_Beam_Rec_Section(fc,fy,Es,b,h,strr,s_d_t,espacing,s_d_c,path)
    
    st.title("Compatibilidad de deformaciones y área de Whitney")
    st.image('./Images/Beam sect.png',use_column_width="auto",caption="Sección de viga y área de Whitney")
    st.image('./Images/Beam deformation compatibility.png',use_column_width="auto",caption="Compatibilidad de deformaciones")
    st.title("Cálculos")
    st.write("***1) Condición de falla: $e_t \leq 0.004$***")
    st.write("***2) Cálculos previos:***")
    st.latex(f"c={str(round(beam.section.c,2))}cm")
    st.latex(f"β_1={str(beam.section.b1)},a=β_1c={str(round(beam.section.a,2))} cm")
    st.latex(f"A_w={str(round(beam.section.Aw,2))} cm^2")
    st.write("***3) Fuerzas de acero y concreto:***")
    st.latex(f"C_c=0.85f'cAw={str(round(beam.section.Cc,2))} tonf")
    for i in range(beam.section.n_s):
        st.write(f"**Capa {i+1}:**")
        st.latex(f"es_{i+1}={str(beam.section.es[i])},fs_{i+1}={str(beam.section.fs[i])}kgf/cm^2,Fs_{i+1}=fs_{i+1}As_{i+1}={str(round(beam.section.Fs[i],2))}tonf")
    
    st.write("***4)Fuerzas nominales***")
    st.latex(f"P_n=C_c+ \sum Fs_i= {str(round(beam.section.Pn,2))} tonf")
    st.latex(f"M_n=C_c(CP-y_c)+ \sum Fs_i(CP-y_i)={str(round(beam.section.Mn,2))} tonf-m")
    st.write("***5)Tipo de falla***")
    et = abs(beam.section.et)
    st.latex(f"e_t={et}")
    ey = abs(beam.section.ey)
    st.latex(f"e_y={ey}")
    if et>=0.004:
        st.latex(r"e_t <0.004 \therefore \text{Falla ductil}")
    elif et<ey:
        st.latex(r"e_t <{ey} \therefore \text{Falla fragil}")
    elif et>=ey and et<=0.004:
        st.latex(r"e_y < e_t}<0.004 \therefore \text{Falla intermedia}")

    st.write("***6) Acero mínimo según NTE060:***")
    st.latex(r"As_{min}=0.7\frac{\sqrt{f'c}}{fy} b_w d")
    st.latex(r"As_{min}" + f"= {str(round(beam.Asmin,1))} cm^2") 
    st.latex(r"As_{total}" + f"={str(round(beam.Astot,1))} cm^2")
    if beam.As_tot>=beam.Asmin:
        st.latex(r"As_{total} \geq As_{min} \therefore \text{Cumple con la cuantía mínima}")    
    else:
        st.latex(r"As_{total} < As_{min} \therefore \text{No cumple con la cuantía mínima}")
                                                            
    
    
    

with st.sidebar:
    st.title("Propiedades geométricas")

    b = st.number_input("Base (cm)",value=30)

    h = st.number_input("Peralte (cm)",value=50)

    st.title("Propiedades de los materiales")

    fc = st.number_input("Resistencia a la compresión del concreto (kg/cm2)",value=210)

    fy = st.number_input("Resistencia a la fluencia del acero (kg/cm2)",value=4200)

    Es = st.number_input("Modulo de elasticidad del acero (kg/cm2)",value=2*10**6)

    st.title("Acero transversal")

    strr = st.selectbox("Diámetro de estribo (pulg)",("0","3/8","1/2","5/8","3/4","7/8","1","1 1/8"),index=1)

    st.title("Acero longitudinal en tracción")

    capas = st.number_input("Número de capas",value=2)
    columns_t = st.number_input("Número de aceros por capa",value=3)
    
    s_d_t = []
    for i in range(capas):
        row = []
        for j in range(columns_t):
            row.append(0)
        s_d_t.append(row)

    cols=[]
    try:
        for i in range(capas):
            cols.append(st.columns(columns_t))
            for j in range(columns_t):
                with cols[i][j]:
                    #s_d_t = st.text_input("Diam.",value="1/2")
                    value = st.selectbox(f'Diam.', ("0","3/8","1/2","5/8","3/4","7/8","1","1 1/8"),key=f'input_{i}_{j}',index=3)
                    s_d_t[i][j] = value
    except:
        pass
    
    espacing = st.number_input("Espaciamiento (cm)",value=5.0,format="%f")

    st.title("Acero longitudinal en compresión")

    columns_c = st.number_input("Número de aceros",value=2)

    cols_c = st.columns(columns_c)

    s_d_c = [None]*columns_c
    for i in range(columns_c):
        with cols_c[i]:
            value = st.selectbox(f'Diam.', ("0","3/8","1/2","5/8","3/4","7/8","1","1 1/8"),key=f'input_{i}',index=1)
            s_d_c[i] = value

st.title("Diseño de viga a flexión")
st.write("Para definir la sección de la viga, se deberá indicar sus propiedades geométricas, del material y de la distribución de aceros en tracción y compresión.")
st.write("Más adelante podrá generar una memoria de los cálculos realizados internamente así como la verificación de acero mínimo según la E060 y el tipo de falla que se presentaría.")

beam = Define_beam(fc,fy,Es,b,h,strr,s_d_t,espacing,s_d_c,path)
st.image('./Images/Beam Section.png',use_column_width="auto",caption="Sección de viga propuesta")

#rf"P_{{\text{{total}}}} = {round(P_tot/1000,2)} ton-f"

button = st.button("Generate Report")

if button:
    try:
        Generate_report_web(beam)
        st.success("Report generated!")
    except:
        st.error("Error")
    button=False

#st.write(os.path.isfile('./Reports/report_beam_section.pdf'))
try:
    with open("./Reports/report_beam_section.pdf", "rb") as pdf_file:
        PDFbyte = pdf_file.read()
        st.download_button(label="Download report",data=PDFbyte,file_name="Report.pdf")
except:
    pass
