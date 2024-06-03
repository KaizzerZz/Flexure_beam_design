def Cent_plas_rec(fc,fy,b,h,n_s,A_s,d_s):
    h_c = h/2
    
    F = 0.85*fc*(b)*(h)
    M = F*h_c

    for i in range(n_s):
        F_o =  A_s[i]*fy
        M_o =  A_s[i]*fy*d_s[i]
        F = F + F_o
        M = M + M_o

    return M/F

def Cent_plas(fc,fy,Ac,cen_c,n_s,A_s,d_s): #Ac y cen_c son Area de concreto y centroide de area de concreto
    F = 0.85*fc*Ac
    M = F*cen_c

    for i in range(n_s):
        F_o =  A_s[i]*fy
        M_o =  A_s[i]*fy*d_s[i]
        F = F + F_o
        M = M + M_o

    return M/F